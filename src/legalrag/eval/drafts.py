"""Find related provision pairs and ask an LLM to draft eval questions for human review.

- multihop: an article of a guiding decree/circular that explicitly cites "khoản M Điều N của
  <law>" + that provision of the law. Answering needs both (the law sets the rule, the guiding
  document gives the detail).
- version: same-titled articles of an expired law and the law that replaced it, whose text
  changed. The question is asked "now", so the answer must come from the new law.
"""

from __future__ import annotations

import difflib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from legalrag.eval.legal_qa import article_texts, similarity
from legalrag.eval.schema import Behavior, Category, EvalItem

LAW_TYPES = {"Luật", "Bộ luật"}


@dataclass
class Pair:
    kind: str  # multihop | version
    a: str  # unit id: the law provision (multihop) / old article (version)
    b: str  # unit id: the guiding provision (multihop) / new article (version)
    a_text: str
    b_text: str
    a_title: str
    b_title: str
    domain: str | None


def law_name(title: str) -> str:
    """'Bộ Luật lao động số 45/2019/QH14' -> 'Bộ Luật lao động'; 'Đất đai' -> 'Luật Đất đai'."""
    t = re.split(r"\s+số\s+|\s+năm\s+\d", title.strip())[0]
    return t if re.match(r"(?i)(bộ\s+)?luật\b", t) else f"Luật {t}"


def _full_text(units: pd.DataFrame, prefix: str) -> str:
    rows = units[(units["unit_id"] == prefix) | units["unit_id"].str.startswith(prefix + "-")]
    return "\n".join(rows.sort_values("ordinal")["text"])


def guide_pairs(docs: pd.DataFrame, units: pd.DataFrame, rels: pd.DataFrame) -> list[Pair]:
    doc = docs.set_index("doc_key")
    live = doc[(doc["status"] == "in_force") & doc["core"]]
    g = rels[
        (rels["rel"] == "guides")
        & ~rels["suspect"]
        & rels["actor_key"].isin(live.index)
        & rels["target_key"].isin(live.index)
    ]
    g = g[g["target_key"].map(doc["loai_van_ban"]).isin(LAW_TYPES)]
    by_doc = {k: u for k, u in units.groupby("doc_key")}
    ids = set(units["unit_id"])
    pairs = []
    for actor, target in g[["actor_key", "target_key"]].drop_duplicates().itertuples(index=False):
        name = law_name(doc.loc[target, "title"])
        rx = re.compile(
            r"(?:khoản\s+(\d+)\s+)?Điều\s+(\d+[a-zđ]?)\s+(?:của\s+)?" + re.escape(name),
            re.IGNORECASE,
        )
        u = by_doc.get(actor)
        if u is None:
            continue
        arts = article_texts(u)
        for art_id, text in arts.items():
            for khoan, dieu in rx.findall(text):
                tid = f"{target}#d{dieu}" + (f"-k{khoan}" if khoan else "")
                if tid not in ids:
                    continue
                law_units = by_doc[target]
                pairs.append(
                    Pair(
                        "multihop",
                        tid,
                        art_id,
                        _full_text(law_units, tid),
                        text,
                        doc.loc[target, "title"],
                        doc.loc[actor, "title"],
                        _domain(doc, target),
                    )
                )
    return _dedup(pairs)


def version_pairs(
    docs: pd.DataFrame,
    units: pd.DataFrame,
    rels: pd.DataFrame,
    min_title_ratio: float = 0.85,
    max_text_sim: float = 0.9,
) -> list[Pair]:
    doc = docs.set_index("doc_key")
    laws = doc[doc["loai_van_ban"].isin(LAW_TYPES) & doc["core"]]
    r = rels[
        (rels["rel"] == "replaces")
        & rels["actor_key"].isin(laws.index)
        & rels["target_key"].isin(laws.index)
    ]
    r = r[
        (r["target_key"].map(doc["status"]) == "expired")
        & (r["actor_key"].map(doc["status"]) == "in_force")
    ]
    arts = units[units["kind"] == "dieu"]
    pairs = []
    for new, old in r[["actor_key", "target_key"]].drop_duplicates().itertuples(index=False):
        a_old = arts[arts["doc_key"] == old]
        a_new = arts[arts["doc_key"] == new]
        new_titles = {row.unit_id: _norm(row.title) for row in a_new.itertuples() if row.title}
        old_full = article_texts(units[units["doc_key"] == old])
        new_full = article_texts(units[units["doc_key"] == new])
        for row in a_old.itertuples():
            t = _norm(row.title)
            if not t:
                continue
            best = max(
                new_titles.items(),
                default=(None, ""),
                key=lambda kv: difflib.SequenceMatcher(None, t, kv[1]).ratio(),
            )
            if best[0] is None:
                continue
            if difflib.SequenceMatcher(None, t, best[1]).ratio() < min_title_ratio:
                continue
            ot, nt = old_full.get(row.unit_id, ""), new_full.get(best[0], "")
            if similarity(ot, nt) >= max_text_sim:
                continue  # unchanged: no point asking
            pairs.append(
                Pair(
                    "version",
                    row.unit_id,
                    best[0],
                    ot,
                    nt,
                    doc.loc[old, "title"],
                    doc.loc[new, "title"],
                    _domain(doc, new),
                )
            )
    return pairs


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _domain(doc: pd.DataFrame, key: str) -> str | None:
    from legalrag.eval.legal_qa import primary_domain

    return primary_domain(doc.loc[key, "title"], list(doc.loc[key, "domains"]))


def _dedup(pairs: list[Pair]) -> list[Pair]:
    seen, out = set(), []
    for p in pairs:
        if (p.a, p.b) not in seen:
            seen.add((p.a, p.b))
            out.append(p)
    return out


def sample(pairs: list[Pair], per_domain: int, seed: int = 0) -> list[Pair]:
    df = pd.DataFrame({"i": range(len(pairs)), "d": [p.domain or "" for p in pairs]})
    df = df.sample(frac=1, random_state=seed).groupby("d").head(per_domain)
    return [pairs[i] for i in sorted(df["i"])]


MULTIHOP_PROMPT = """Bạn soạn câu hỏi kiểm thử cho hệ thống hỏi đáp pháp luật Việt Nam.

QUY ĐỊNH A ({a_title}) [{a}]:
{a_text}

QUY ĐỊNH B ({b_title}) [{b}]:
{b_text}

Viết MỘT câu hỏi tình huống thực tế như người dân hỏi, mà muốn trả lời đầy đủ thì phải dùng CẢ HAI
quy định: A đặt ra nguyên tắc, B quy định chi tiết. Yêu cầu:
- Không nêu số điều, số khoản, số hiệu hay năm của văn bản trong câu hỏi.
- Đáp án ngắn gọn, trích dẫn bằng id trong ngoặc vuông, ví dụ [{a}] và [{b}].
Chỉ trả về JSON: {{"question": "...", "answer": "...", "why_both": "vì sao cần cả hai"}}"""

VERSION_PROMPT = """Bạn soạn câu hỏi kiểm thử về việc áp dụng đúng văn bản còn hiệu lực.

ĐIỀU CŨ, ĐÃ HẾT HIỆU LỰC ({a_title}) [{a}]:
{a_text}

ĐIỀU MỚI, ĐANG CÓ HIỆU LỰC ({b_title}) [{b}]:
{b_text}

Viết MỘT câu hỏi thực tế, hỏi ở thời điểm hiện tại, mà câu trả lời theo điều mới KHÁC câu trả lời
theo điều cũ. Không nêu số điều, số hiệu hay năm của văn bản. Đáp án dựa trên điều mới, có trích
dẫn [{b}].
Chỉ trả về JSON: {{"question": "...", "answer": "...", "difference": "điểm khác giữa cũ và mới"}}"""


def prompt_for(p: Pair, max_chars: int = 3000) -> str:
    tpl = MULTIHOP_PROMPT if p.kind == "multihop" else VERSION_PROMPT
    return tpl.format(
        a=p.a,
        b=p.b,
        a_title=p.a_title,
        b_title=p.b_title,
        a_text=p.a_text[:max_chars],
        b_text=p.b_text[:max_chars],
    )


def draft_item(p: Pair, complete: Callable[[str], str], n: int) -> EvalItem:
    raw = complete(prompt_for(p))
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    out = json.loads(m.group(0)) if m else {}
    common = dict(
        id=f"draft-{p.kind}-{n:04d}",
        question=out.get("question", "").strip() or "?",
        gold_answer=out.get("answer"),
        domain=p.domain,
        source="llm_draft",
        reviewed=False,
        meta={
            "pair": [p.a, p.b],
            "raw": raw if not m else None,
            "why": out.get("why_both") or out.get("difference"),
        },
    )
    if p.kind == "multihop":
        return EvalItem(
            category=Category.MULTI_HOP,
            expected_behavior=Behavior.ANSWER,
            gold_articles=[p.a, p.b],
            **common,
        )
    return EvalItem(
        category=Category.EXPIRED,
        expected_behavior=Behavior.ANSWER_CURRENT,
        gold_articles=[p.b],
        forbidden_articles=[p.a],
        **common,
    )
