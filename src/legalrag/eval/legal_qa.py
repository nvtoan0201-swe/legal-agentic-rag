"""Load thangvip/vietnamese-legal-qa and map its questions onto the corpus.

Each row is one article (`article_content` starts with "Điều N.") of a law named in `doc_name`
(which usually contains the official number) plus ~3 LLM-generated Q&A pairs. Mapping is
(number, article) -> unit id, then verified by comparing the article text with the corpus,
because the same number can belong to different documents (93/2015/QH13 is both a law and a
resolution).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd

from legalrag.eval.schema import Behavior, Category, EvalItem

HF_QA = "thangvip/vietnamese-legal-qa"
HF_QA_REVISION = "9bd2b0e66fc5a9d09b4df22fade7a8d9592834c2"
SOURCE = HF_QA
MATCH_THRESHOLD = 0.5

RE_NUMBER = re.compile(r"(\d+/\d{4}/[A-ZĐ0-9\-]+)")
RE_ARTICLE = re.compile(r"^\s*Đi[eêề]u\s+(\d+[a-zđ]?)")
RE_MENTIONS_ARTICLE = re.compile(r"Điều\s+\d+", re.IGNORECASE)
RE_NAMES_LAW = re.compile(r"(?:Bộ luật|Luật)\s+[A-ZĐÂĂÊÔƠƯ]")
RE_NAMES_VERSION = re.compile(r"\d+/\d{4}/QH\d+|năm\s+(?:19|20)\d\d|\b(?:19|20)\d\d\b")
_WORD = re.compile(r"\w+", re.UNICODE)


def download(local_dir: Path) -> Path:
    from huggingface_hub import hf_hub_download

    return Path(
        hf_hub_download(
            HF_QA,
            "data/train-00000-of-00001.parquet",
            repo_type="dataset",
            revision=HF_QA_REVISION,
            local_dir=local_dir,
        )
    )


def explode(qa: pd.DataFrame) -> pd.DataFrame:
    """One row per (article, Q&A pair)."""
    qa = qa.reset_index(names="row")
    # The document's own number comes last ("Luật sửa đổi ... Luật Đất đai số 31/2024/QH15 ...,
    # số 43/2024/QH15").
    qa["so_ky_hieu"] = qa["doc_name"].map(lambda n: (RE_NUMBER.findall(n) or [None])[-1])
    qa["dieu"] = qa["article_content"].str.extract(RE_ARTICLE)[0]
    qa["is_draft"] = qa["doc_name"].str.contains(r"^\s*Dự thảo", case=False)
    rows = []
    for r in qa.itertuples():
        for j, p in enumerate(r.generated_qa_pairs):
            rows.append(
                {
                    "row": r.row,
                    "pair": j,
                    "doc_name": r.doc_name.strip(),
                    "so_ky_hieu": r.so_ky_hieu,
                    "dieu": r.dieu,
                    "is_draft": r.is_draft,
                    "article_content": r.article_content,
                    "question": p["question"].strip(),
                    "answer": p["answer"].strip(),
                    "question_type": p.get("question_type"),
                    "difficulty": p.get("difficulty"),
                }
            )
    return pd.DataFrame(rows)


def _words(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def similarity(a: str, b: str) -> float:
    """Word-set overlap relative to the smaller text (robust to truncation and formatting)."""
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))


def article_texts(units: pd.DataFrame) -> dict[str, str]:
    """unit id of each article -> full text (article line + its clauses and points)."""
    u = units.sort_values(["doc_key", "ordinal"])
    art = u["unit_id"].str.extract(r"^(.*?#(?:kt\d+-)?d\d+[a-zđ]?)")[0]
    u = u.assign(article=art).dropna(subset=["article"])
    return u.groupby("article")["text"].agg("\n".join).to_dict()


def map_articles(pairs: pd.DataFrame, docs: pd.DataFrame, art_text: dict[str, str]) -> pd.DataFrame:
    """Add `unit_id`, `match` (status) and `sim` per distinct article."""
    doc = docs.set_index("doc_key")
    arts = pairs.drop_duplicates("row")[
        ["row", "so_ky_hieu", "dieu", "is_draft", "article_content"]
    ]
    out = []
    for r in arts.itertuples():
        uid, status, sim = None, "ok", float("nan")
        if r.is_draft:
            status = "draft_law"
        elif not isinstance(r.so_ky_hieu, str):
            status = "no_number"
        elif r.so_ky_hieu not in doc.index:
            status = "not_in_corpus"
        else:
            uid = f"{r.so_ky_hieu}#d{r.dieu}"
            text = art_text.get(uid)
            if text is None:
                status = "article_missing"
            else:
                sim = similarity(r.article_content[:1500], text[:1500])
                if sim < MATCH_THRESHOLD:
                    status = "content_mismatch"
                elif not doc.loc[r.so_ky_hieu, "core"]:
                    status = "not_core"
        out.append({"row": r.row, "unit_id": uid, "match": status, "sim": sim})
    return pairs.merge(pd.DataFrame(out), on="row")


def _split(key: str, test_share: int = 5) -> str:
    """Deterministic split by article so the pairs of one article stay together."""
    return "test" if int(hashlib.md5(key.encode()).hexdigest(), 16) % test_share == 0 else "dev"


def build_items(
    mapped: pd.DataFrame,
    docs: pd.DataFrame,
    replaced_by: dict[str, list[str]],
    n_out_of_scope: int = 150,
    seed: int = 0,
) -> list[EvalItem]:
    doc = docs.set_index("doc_key")
    items: list[EvalItem] = []
    for r in mapped[mapped["match"] == "ok"].itertuples():
        d = doc.loc[r.so_ky_hieu]
        expired = d["status"] == "expired"
        meta = _flags(r) | {
            "split": _split(r.unit_id),
            "doc_status": d["status"],
            "question_type": r.question_type,
            "difficulty": r.difficulty,
        }
        common = dict(
            id=f"lqa-{r.row}-{r.pair}",
            question=r.question,
            gold_answer=r.answer,
            domain=primary_domain(d["title"], list(d["domains"])),
            source=SOURCE,
            meta=meta,
        )
        if not expired:
            items.append(
                EvalItem(
                    category=Category.SINGLE_HOP,
                    expected_behavior=Behavior.ANSWER,
                    gold_articles=[r.unit_id],
                    **common,
                )
            )
        else:
            meta["superseded_by"] = replaced_by.get(r.so_ky_hieu, [])
            items.append(
                EvalItem(
                    category=Category.EXPIRED,
                    expected_behavior=Behavior.ANSWER_CURRENT,
                    forbidden_articles=[r.unit_id],
                    notes="Gold = điều tương ứng của văn bản thay thế, cần điền khi duyệt. "
                    "gold_answer là đáp án theo văn bản đã hết hiệu lực.",
                    **common,
                )
            )

    # Out of scope: laws absent from the corpus altogether (not drafts, number known).
    oos = mapped[mapped["match"] == "not_in_corpus"]
    per_law = max(1, n_out_of_scope // max(1, oos["so_ky_hieu"].nunique()))
    oos = (
        oos.sample(frac=1, random_state=seed)
        .groupby("so_ky_hieu")
        .head(per_law)
        .head(n_out_of_scope)
    )
    for r in oos.itertuples():
        items.append(
            EvalItem(
                id=f"lqa-{r.row}-{r.pair}",
                question=r.question,
                category=Category.OUT_OF_SCOPE,
                expected_behavior=Behavior.ABSTAIN,
                source=SOURCE,
                meta=_flags(r) | {"split": _split(f"{r.so_ky_hieu}#d{r.dieu}"), "law": r.doc_name},
                notes="Luật không có trong corpus; một số câu có thể vẫn trả lời được một phần "
                "bằng luật trong corpus, cần duyệt.",
            )
        )
    return items


def primary_domain(title: str, domains: list[str]) -> str | None:
    """The domain whose anchor name appears in the title, else the first one."""
    from legalrag.ingest.domains import DOMAINS, anchor_regex

    for d in domains:
        if anchor_regex(DOMAINS[d]).search(title):
            return d
    return domains[0] if domains else None


def _flags(r) -> dict:
    """Shortcuts that make a question easier than a real user question."""
    q = r.question
    return {
        "mentions_article": bool(RE_MENTIONS_ARTICLE.search(q)),
        "names_law": bool(RE_NAMES_LAW.search(q)),
        "names_version": bool(RE_NAMES_VERSION.search(q)),
    }
