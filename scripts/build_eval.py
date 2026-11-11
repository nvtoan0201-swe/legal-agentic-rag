"""Map thangvip/vietnamese-legal-qa onto the corpus and write eval items.

Output: data/eval/legal_qa.jsonl (not committed: the source dataset declares no license) and
reports/eval_mapping.md.

    uv run python -I scripts/build_eval.py
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd

from legalrag.eval.legal_qa import (
    HF_QA,
    HF_QA_REVISION,
    MATCH_THRESHOLD,
    article_texts,
    build_items,
    download,
    explode,
    map_articles,
)
from legalrag.eval.schema import write_jsonl

MATCH_DOC = {
    "ok": "ánh xạ được, nội dung khớp, văn bản lõi",
    "not_in_corpus": "số hiệu không có trong corpus (luật ngoài 6 lĩnh vực)",
    "no_number": "doc_name không có số hiệu",
    "draft_law": "dự thảo luật, bỏ",
    "content_mismatch": f"có số hiệu + điều nhưng nội dung khác (độ trùng từ < {MATCH_THRESHOLD})",
    "article_missing": "văn bản có trong corpus nhưng không có điều này sau parse",
    "not_core": "luật ngoại vi (lĩnh vực khác, chỉ vào corpus vì sửa luật gốc)",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--report", type=Path, default=Path("reports/eval_mapping.md"))
    ap.add_argument("--n-out-of-scope", type=int, default=150)
    args = ap.parse_args()

    qa_path = args.data_dir / "raw/qa/data/train-00000-of-00001.parquet"
    if not qa_path.exists():
        qa_path = download(args.data_dir / "raw/qa")
    proc = args.data_dir / "processed"
    docs = pd.read_parquet(proc / "documents.parquet")
    units = pd.read_parquet(proc / "units.parquet")
    rels = pd.read_parquet(proc / "relations.parquet")

    pairs = explode(pd.read_parquet(qa_path))
    mapped = map_articles(pairs, docs, article_texts(units))
    repl = rels[
        (rels["rel"] == "replaces") & rels["actor_key"].notna() & rels["target_key"].notna()
    ]
    replaced_by = repl.groupby("target_key")["actor_key"].agg(lambda s: sorted(set(s))).to_dict()
    items = build_items(mapped, docs, replaced_by, n_out_of_scope=args.n_out_of_scope)
    out = args.data_dir / "eval/legal_qa.jsonl"
    write_jsonl(items, out)
    print(f"wrote {len(items)} items to {out}")
    write_report(pairs, mapped, items, docs, args.report)


def write_report(pairs, mapped, items, docs, path: Path) -> None:
    arts = mapped.drop_duplicates("row")
    status = arts["match"].value_counts()
    status_tab = pd.DataFrame(
        {
            "điều": status,
            "cặp hỏi-đáp": mapped["match"].value_counts(),
            "ý nghĩa": status.index.map(MATCH_DOC),
        }
    )
    in_corpus = arts[arts["so_ky_hieu"].isin(docs["doc_key"])]
    law_tab = in_corpus.groupby(["so_ky_hieu", "match"]).size().unstack(fill_value=0)
    titles = docs.set_index("doc_key")
    law_tab.insert(0, "văn bản", [titles.loc[k, "title"][:45] for k in law_tab.index])
    law_tab.insert(1, "hiệu lực", [titles.loc[k, "status"] for k in law_tab.index])

    df = pd.DataFrame(
        [
            {
                "category": i.category.value,
                "domain": i.domain,
                "split": i.meta["split"],
                **{k: i.meta.get(k) for k in ("mentions_article", "names_law", "names_version")},
            }
            for i in items
        ]
    )
    cat = pd.crosstab(df["category"], df["split"], margins=True)
    flags = df.groupby("category")[["mentions_article", "names_law", "names_version"]].mean()
    dom = pd.crosstab(df["domain"].fillna("—"), df["category"])
    mism = arts[arts["match"] == "content_mismatch"].head(5)
    sims = arts["sim"].dropna()
    hist = pd.cut(sims, [0, 0.3, 0.5, 0.7, 0.9, 1.0001]).value_counts().sort_index()
    hist.index = hist.index.astype(str)

    text = f"""# Ánh xạ bộ {HF_QA} vào corpus (bước 4)

_Sinh tự động bởi `scripts/build_eval.py` — không sửa tay._ Revision `{HF_QA_REVISION}`.

Bộ QA có {pairs["row"].nunique():,} điều luật và {len(pairs):,} cặp hỏi–đáp do LLM sinh, chỉ gồm Luật/
Bộ luật. Ánh xạ = số hiệu (lấy từ `doc_name`) + số Điều (lấy từ đầu `article_content`), sau đó xác
minh bằng độ trùng từ giữa `article_content` và văn bản điều trong corpus.

## 1. Kết quả ánh xạ

{status_tab.to_markdown()}

Phân bố độ trùng từ (các điều có số hiệu + điều trong corpus):

{hist.to_markdown()}

## 2. Theo văn bản có trong corpus

{law_tab.to_markdown()}

## 3. Bộ eval sinh ra

{cat.to_markdown()}

### Theo lĩnh vực

{dom.to_markdown()}

### "Đường tắt" trong câu hỏi (tỉ lệ)

`mentions_article` = câu hỏi nêu sẵn "Điều N"; `names_law` = nêu tên luật; `names_version` = nêu số
hiệu hoặc năm. Câu hỏi thật của người dùng hiếm khi có các thông tin này, nên khi báo cáo cần tách
riêng nhóm không có đường tắt.

{flags.round(2).to_markdown()}

## 4. Nhận xét

- **Độ phủ lĩnh vực rất lệch:** câu dùng được chỉ thuộc 2/6 lĩnh vực (BHXH, giao thông đường bộ).
  Bộ QA không có Bộ luật Lao động 2019, Luật HN&GĐ 2014, Luật Đất đai 2024 hay Luật thuế TNCN.
  → Bộ câu tự viết và bộ multi-hop sinh nháp phải bù cho lao động, HN&GĐ, đất đai và thuế TNCN.
- `article_missing` gần như toàn bộ là **trùng số hiệu**: 93/2015/QH13 trong bộ QA là Luật Tố tụng
  hành chính, còn trong corpus là Nghị quyết 93/2015/QH13 về BHXH. Bước xác minh đã loại đúng.
- **Câu về luật đã hết hiệu lực** (BHXH 2014, GTĐB 2008/2001) được xếp vào `expired`, chưa có
  gold: phải điền điều tương ứng của luật thay thế khi duyệt. `forbidden_articles` là điều của luật
  cũ.
- **`out_of_scope`** lấy từ luật hoàn toàn không có trong corpus. Đây là ngoài phạm vi theo nghĩa
  corpus; vài câu có thể giao nhau với luật trong corpus, cần duyệt.
- Câu hỏi và đáp án đều do LLM sinh, chưa qua người duyệt, nên mọi item có `reviewed=false`.

### Ví dụ nội dung không khớp

{mism[["doc_name", "so_ky_hieu", "dieu", "sim"]].to_markdown(index=False) if len(mism) else "_Không có._"}
"""
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path}")
    print(Counter(i.category.value for i in items))


if __name__ == "__main__":
    main()
