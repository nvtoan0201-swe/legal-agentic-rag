"""Named eval sets assembled from the committed files and the generated (uncommitted) ones."""

from __future__ import annotations

from pathlib import Path

from legalrag.eval.schema import Category, EvalItem, read_jsonl

LEGAL_QA = Path("data/eval/legal_qa.jsonl")
COMMITTED = Path("eval/sets")


def load_committed(root: Path = COMMITTED) -> dict[str, list[EvalItem]]:
    """{file stem: items} for every committed set except the format template."""
    return {
        p.stem: read_jsonl(p)
        for p in sorted(root.glob("*.jsonl"))
        if p.name != "manual_template.jsonl"
    }


def build_sets(corpus=None, legal_qa: Path = LEGAL_QA, root: Path = COMMITTED) -> dict:
    """{name: items}. `corpus` enables the silver `expired` set (see eval/versions.py)."""
    sets: dict[str, list[EvalItem]] = {}
    if legal_qa.exists():
        lqa = read_jsonl(legal_qa)
        single = [i for i in lqa if i.category == Category.SINGLE_HOP]
        sets["lqa_single_test"] = [i for i in single if i.meta.get("split") == "test"]
        sets["lqa_single_dev"] = [i for i in single if i.meta.get("split") == "dev"]
        # No "Điều N" in the question: closer to how people actually ask.
        sets["lqa_single_noref"] = [i for i in single if not i.meta.get("mentions_article")]
        sets["lqa_oos"] = [i for i in lqa if i.category == Category.OUT_OF_SCOPE]
        if corpus is not None:
            from legalrag.eval.versions import fill_current_gold

            sets["lqa_expired_silver"] = fill_current_gold(lqa, corpus)
    return sets | load_committed(root)
