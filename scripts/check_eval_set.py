"""Validate eval set files: schema, unique ids, unit ids exist, status of gold documents.

uv run python -I scripts/check_eval_set.py eval/sets/*.jsonl
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from legalrag.eval.schema import Behavior, Category, read_jsonl

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--processed", type=Path, default=Path("data/processed"))
    args = ap.parse_args()

    units = set(pd.read_parquet(args.processed / "units.parquet", columns=["unit_id"])["unit_id"])
    docs = pd.read_parquet(args.processed / "documents.parquet").set_index("doc_key")
    errors, warnings, seen = [], [], set()
    for f in args.files:
        for it in read_jsonl(f):
            where = f"{f}:{it.id}"
            if it.id in seen:
                errors.append(f"{where}: duplicate id")
            seen.add(it.id)
            for uid in it.gold_articles + it.forbidden_articles:
                if uid not in units:
                    errors.append(f"{where}: unknown unit id {uid}")
            for uid in it.gold_articles:
                key = uid.split("#")[0]
                if key in docs.index and docs.loc[key, "status"] != "in_force":
                    warnings.append(
                        f"{where}: gold {uid} is in a '{docs.loc[key, 'status']}' document"
                    )
            if it.category == Category.OUT_OF_SCOPE and it.expected_behavior != Behavior.ABSTAIN:
                errors.append(f"{where}: out_of_scope must expect abstain")
            if it.category in (Category.SINGLE_HOP, Category.MULTI_HOP) and not it.gold_articles:
                errors.append(f"{where}: missing gold_articles")
            if it.category == Category.MULTI_HOP and len(it.gold_articles) < 2:
                warnings.append(f"{where}: multi_hop with a single gold article")
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(seen)} items, {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)
