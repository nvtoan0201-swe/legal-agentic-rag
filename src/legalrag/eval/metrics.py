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


def _norm(level: str | Callable[[str], str]) -> Callable[[str], str]:
    """`level` is a name in LEVELS or a custom id normaliser (e.g. eval.aliases.normalizer)."""
    return level if callable(level) else LEVELS[level]


def _dedup(ids: Iterable[str], norm: Callable[[str], str]) -> list[str]:
    seen, out = set(), []
    for x in ids:
        n = norm(x)
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def recall_at_k(retrieved: Sequence[str], gold: Sequence[str], k: int, level="article") -> float:
    norm = _norm(level)
    g = {norm(x) for x in gold}
    if not g:
        return float("nan")
    return len(set(_dedup(retrieved, norm)[:k]) & g) / len(g)


def mrr(retrieved: Sequence[str], gold: Sequence[str], level="article") -> float:
    norm = _norm(level)
    g = {norm(x) for x in gold}
    if not g:
        return float("nan")
    for rank, x in enumerate(_dedup(retrieved, norm), 1):
        if x in g:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: Sequence[str], gold: Sequence[str], k: int, level="article") -> float:
    norm = _norm(level)
    g = {norm(x) for x in gold}
    if not g:
        return float("nan")
    ranked = _dedup(retrieved, norm)[:k]
    dcg = sum(1.0 / math.log2(i + 2) for i, x in enumerate(ranked) if x in g)
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(g), k)))
    return dcg / ideal


def forbidden_at_k(
    retrieved: Sequence[str], forbidden: Sequence[str], k: int, level="article"
) -> float:
    """1 if any forbidden article (e.g. of an expired law) is among the top-k articles."""
    norm = _norm(level)
    f = {norm(x) for x in forbidden}
    if not f:
        return float("nan")
    return float(bool(set(_dedup(retrieved, norm)[:k]) & f))


def bad_share_at_k(retrieved: Sequence[str], is_bad: Callable[[str], bool], k: int) -> float:
    """Share of the top-k articles that come from a document flagged by `is_bad(doc_key)`."""
    top = _dedup(retrieved, to_article)[:k]
    return sum(is_bad(to_document(x)) for x in top) / len(top) if top else float("nan")


def evaluate_retrieval(
    items: Sequence[EvalItem],
    retrieve: Callable[[EvalItem], Sequence[str]],
    ks: Sequence[int] = (1, 5, 10, 20),
    level: str | Callable[[str], str] = "article",
    is_bad_doc: Callable[[str], bool] | None = None,
) -> dict:
    """Run `retrieve(item) -> ranked unit ids` on items that have gold articles.

    `is_bad_doc(doc_key)` (e.g. "not in force") adds `expired@k`: the share of top-k articles
    from such documents. Items with `forbidden_articles` also get `forbidden@k`.
    """
    rows = []
    for it in items:
        if not it.gold_articles:
            continue
        got = list(retrieve(it))
        row = {"id": it.id, "category": it.category.value, "mrr": mrr(got, it.gold_articles, level)}
        for k in ks:
            row[f"recall@{k}"] = recall_at_k(got, it.gold_articles, k, level)
            row[f"ndcg@{k}"] = ndcg_at_k(got, it.gold_articles, k, level)
        if is_bad_doc is not None:
            row["expired@5"] = bad_share_at_k(got, is_bad_doc, 5)
        if it.forbidden_articles:
            row["forbidden@5"] = forbidden_at_k(got, it.forbidden_articles, 5, level)
        rows.append(row)
    return {"n": len(rows), "summary": summarize(rows), "rows": rows}


def summarize(rows: list[dict], by: str = "category") -> dict:
    """Mean of every numeric column (ignoring NaN), overall and per `by` value."""

    def mean(rs):
        keys = dict.fromkeys(k for r in rs for k, v in r.items() if isinstance(v, float))
        out = {}
        for k in keys:
            vals = [r[k] for r in rs if k in r and r[k] == r[k]]
            out[k] = sum(vals) / len(vals) if vals else float("nan")
        return out | {"n": len(rs)}

    if not rows:
        return {}
    out = {"all": mean(rows)}
    for v in sorted({r[by] for r in rows}):
        out[v] = mean([r for r in rows if r[by] == v])
    return out
