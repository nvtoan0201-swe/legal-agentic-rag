"""Compare retrieval configurations on every eval set -> reports/retrieval_eval.md.

uv run python -I scripts/eval_retrieval.py
uv run python -I scripts/eval_retrieval.py --sets lqa_single_test --configs hybrid,hybrid+rr
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path

import pandas as pd

from legalrag.eval.aliases import build_aliases, normalizer
from legalrag.eval.metrics import evaluate_retrieval
from legalrag.eval.sets import build_sets
from legalrag.retrieval.retriever import RetrievalConfig, Retriever, unit_ids
from legalrag.store import Corpus

CONFIGS = {
    "bm25": RetrievalConfig(mode="bm25", k=20),
    "dense": RetrievalConfig(mode="dense", k=20),
    "hybrid": RetrievalConfig(mode="hybrid", k=20),
    "dense+rr": RetrievalConfig(mode="dense", k=20, rerank=True),
    "hybrid+rr": RetrievalConfig(mode="hybrid", k=20, rerank=True),
    "hybrid+rr+in_force": RetrievalConfig(mode="hybrid", k=20, rerank=True, in_force_only=True),
}
COLS = ["recall@1", "recall@5", "recall@10", "mrr", "ndcg@10", "expired@5", "forbidden@5"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", help="comma-separated set names (default: all with gold)")
    ap.add_argument("--configs", default=",".join(CONFIGS))
    ap.add_argument("--out", default="reports/retrieval_eval.md")
    args = ap.parse_args()

    corpus = Corpus.load()
    sets = build_sets(corpus)
    names = args.sets.split(",") if args.sets else [n for n in sets if n != "lqa_oos"]
    configs = args.configs.split(",")
    retriever = Retriever.from_disk(corpus=corpus, reranker=any(CONFIGS[c].rerank for c in configs))
    live = corpus.in_force()
    norm = normalizer(build_aliases(corpus))

    rows, per_item = [], {}
    for cname in configs:
        cfg = CONFIGS[cname]
        for sname in names:
            items = sets[sname]
            t = time.time()

            def run(it, cfg=cfg):
                c = replace(cfg, as_of=it.as_of) if cfg.in_force_only else cfg
                return unit_ids(retriever.search(it.question, c))

            res = evaluate_retrieval(items, run, level=norm, is_bad_doc=lambda k: k not in live)
            ms = (time.time() - t) / max(1, res["n"]) * 1000
            s = res["summary"].get("all", {})
            rows.append({"set": sname, "config": cname, "n": res["n"], "ms/q": ms} | s)
            per_item[f"{sname}|{cname}"] = res["rows"]
            print(
                f"{sname:22} {cname:20} n={res['n']:4} R@5={s.get('recall@5', 0):.3f} "
                f"MRR={s.get('mrr', 0):.3f} {ms:.0f}ms/q",
                flush=True,
            )

    out_dir = Path("data/eval/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "retrieval.json").write_text(json.dumps({"rows": rows, "items": per_item}))
    write_report(pd.DataFrame(rows), sets, Path(args.out))


def write_report(df: pd.DataFrame, sets: dict, path: Path) -> None:
    lines = [
        "# Đánh giá truy xuất (bước 5)",
        "",
        "_Sinh tự động bởi `scripts/eval_retrieval.py` — không sửa tay._ Chấm ở mức Điều "
        "(trúng một khoản của điều gold là trúng; điều trong văn bản hợp nhất được quy về điều cùng "
        "số, cùng tiêu đề của luật gốc). `expired@5` = tỉ lệ điều trong top-5 thuộc "
        "văn bản không còn hiệu lực; `forbidden@5` = tỉ lệ câu có điều của luật cũ (bị cấm làm "
        "căn cứ) trong top-5.",
        "",
        "Cấu hình: `bm25` (âm tiết + bigram) · `dense` (BAAI/bge-m3, Qdrant) · `hybrid` (RRF k=60, "
        "50 ứng viên mỗi bên) · `+rr` (rerank 30 ứng viên đầu bằng BAAI/bge-reranker-v2-m3) · "
        "`+in_force` (chỉ tìm trong văn bản còn hiệu lực tại `as_of`).",
        "",
        "Các bộ: `lqa_*` là câu hỏi LLM sinh từ thangvip/vietnamese-legal-qa (chỉ có luật GTĐB và "
        "BHXH; nhiều câu nêu sẵn số Điều và tên luật nên dễ hơn câu hỏi thật). `lqa_single_noref` "
        "là các câu không nêu số Điều. `lqa_expired_silver`: câu hỏi về luật đã hết hiệu lực, gold "
        "là điều cùng tiêu đề của luật hiện hành (bạc, chưa duyệt tay). `situational`: 66 câu tình "
        "huống không nêu số Điều/số hiệu, phủ cả 6 lĩnh vực (`eval/sets/situational.jsonl`, trợ lý AI "
        "soạn từ nguyên văn điều luật, chưa có người duyệt).",
        "",
    ]
    for sname, g in df.groupby("set", sort=False):
        lines += [f"## {sname} (n={int(g['n'].iloc[0])})", ""]
        cols = ["config"] + [c for c in COLS if c in g and g[c].notna().any()] + ["ms/q"]
        t = g[cols].copy()
        for c in cols[1:]:
            t[c] = t[c].map(
                lambda v, c=c: "" if pd.isna(v) else f"{v:.0f}" if c == "ms/q" else f"{v:.3f}"
            )
        lines += [t.to_markdown(index=False), ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"-> {path}")


if __name__ == "__main__":
    main()
