"""Retrieval metrics (Recall@k, MRR, nDCG@k) over unit ids.

By default ids are compared at article level: retrieving "X#d35-k2" counts as a hit for gold
"X#d35" and vice versa, and several clauses of the same article count once.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable, Sequence

from legalrag.eval.schema import EvalItem

_ARTICLE = re.compile(r"^(.*?#(?:kt\d+-)?(?:d\d+[a-zđ]?|pl\d+|kt\d+|body))")


def to_article(unit_id: str) -> str:
    m = _ARTICLE.match(unit_id)
    return m.group(1) if m else unit_id


def to_document(unit_id: str) -> str:
    return unit_id.split("#", 1)[0]


LEVELS: dict[str, Callable[[str], str]] = {
    "unit": lambda x: x,
    "article": to_article,
    "document": to_document,
}


def _dedup(ids: Iterable[str], norm: Callable[[str], str]) -> list[str]:
    seen, out = set(), []
    for x in ids:
        n = norm(x)
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def recall_at_k(retrieved: Sequence[str], gold: Sequence[str], k: int, level="article") -> float:
    norm = LEVELS[level]
    g = {norm(x) for x in gold}
    if not g:
        return float("nan")
    return len(set(_dedup(retrieved, norm)[:k]) & g) / len(g)


def mrr(retrieved: Sequence[str], gold: Sequence[str], level="article") -> float:
    norm = LEVELS[level]
    g = {norm(x) for x in gold}
    if not g:
        return float("nan")
    for rank, x in enumerate(_dedup(retrieved, norm), 1):
        if x in g:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: Sequence[str], gold: Sequence[str], k: int, level="article") -> float:
    norm = LEVELS[level]
    g = {norm(x) for x in gold}
    if not g:
        return float("nan")
    ranked = _dedup(retrieved, norm)[:k]
    dcg = sum(1.0 / math.log2(i + 2) for i, x in enumerate(ranked) if x in g)
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(g), k)))
    return dcg / ideal


def evaluate_retrieval(
    items: Sequence[EvalItem],
    retrieve: Callable[[str], Sequence[str]],
    ks: Sequence[int] = (1, 5, 10, 20),
    level: str = "article",
) -> dict:
    """Run `retrieve(question) -> ranked unit ids` on items that have gold articles."""
    rows = []
    for it in items:
        if not it.gold_articles:
            continue
        got = list(retrieve(it.question))
        row = {"id": it.id, "category": it.category.value, "mrr": mrr(got, it.gold_articles, level)}
        for k in ks:
            row[f"recall@{k}"] = recall_at_k(got, it.gold_articles, k, level)
            row[f"ndcg@{k}"] = ndcg_at_k(got, it.gold_articles, k, level)
        rows.append(row)
    return {"n": len(rows), "summary": summarize(rows), "rows": rows}


def summarize(rows: list[dict], by: str = "category") -> dict:
    """Mean of every numeric column, overall and per `by` value."""

    def mean(rs):
        keys = [k for k in rs[0] if isinstance(rs[0][k], float)]
        return {k: sum(r[k] for r in rs) / len(rs) for k in keys} | {"n": len(rs)}

    if not rows:
        return {}
    out = {"all": mean(rows)}
    for v in sorted({r[by] for r in rows}):
        out[v] = mean([r for r in rows if r[by] == v])
    return out
