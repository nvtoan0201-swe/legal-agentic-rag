"""Draft multi-hop / version questions with an LLM, for manual review.

    uv run python -I scripts/gen_drafts.py --kind multihop --per-domain 15
    uv run python -I scripts/gen_drafts.py --kind version --per-domain 10 --dry-run   # prompts only

Output: data/eval/drafts/{kind}.jsonl (items with reviewed=false). Review them, fix gold ids and
answers, set "reviewed": true and move the good ones into eval/sets/.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from legalrag.eval.drafts import draft_item, guide_pairs, prompt_for, sample, version_pairs
from legalrag.eval.schema import write_jsonl

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["multihop", "version"], required=True)
    ap.add_argument("--per-domain", type=int, default=15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true", help="write prompts, do not call the LLM")
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    args = ap.parse_args()

    proc = args.data_dir / "processed"
    docs = pd.read_parquet(proc / "documents.parquet")
    units = pd.read_parquet(proc / "units.parquet")
    rels = pd.read_parquet(proc / "relations.parquet")
    find = guide_pairs if args.kind == "multihop" else version_pairs
    pairs = sample(find(docs, units, rels), args.per_domain, args.seed)
    out_dir = args.data_dir / "eval/drafts"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        out = out_dir / f"{args.kind}_prompts.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for p in pairs:
                f.write(
                    json.dumps(
                        {"pair": [p.a, p.b], "domain": p.domain, "prompt": prompt_for(p)},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        print(f"wrote {len(pairs)} prompts to {out}")
    else:
        from legalrag.llm import complete

        items = []
        for n, p in enumerate(pairs):
            try:
                items.append(draft_item(p, complete, n))
            except Exception as e:  # keep going; report failures
                print(f"failed {p.a} / {p.b}: {e}")
        out = out_dir / f"{args.kind}.jsonl"
        write_jsonl(items, out)
        print(f"wrote {len(items)}/{len(pairs)} drafts to {out}")
