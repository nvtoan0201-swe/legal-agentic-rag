"""Consolidated texts (Văn bản hợp nhất, VBHN) repeat the base document article by article.

Retrieving "58/VBHN-VPQH#d53-k1" for a question whose gold is "41/2024/QH15#d53-k1" is a correct
hit, so before scoring every VBHN article is mapped to the base article with the same number and
the same heading. Amended articles whose heading changed keep their VBHN id.
"""

from __future__ import annotations

from legalrag.eval.metrics import to_article
from legalrag.eval.versions import norm_title


def build_aliases(corpus) -> dict[str, str]:
    """VBHN article id -> base article id."""
    rels = corpus.rels
    edges = rels[(rels["rel"] == "consolidates") & ~rels["suspect"]].dropna(
        subset=["actor_key", "target_key"]
    )
    u = corpus.units
    arts = u[u["kind"] == "dieu"]
    heads = {
        doc: dict(zip(g["unit_id"], g["text"], strict=True)) for doc, g in arts.groupby("doc_key")
    }
    out: dict[str, str] = {}
    for vbhn, g in edges.groupby("actor_key"):
        mine = heads.get(vbhn, {})
        best: dict[str, str] = {}
        for base in g["target_key"]:
            theirs = heads.get(base, {})
            m = {}
            for uid, text in mine.items():
                other = f"{base}#{uid.split('#', 1)[1]}"
                if other in theirs and norm_title(theirs[other]) == norm_title(text):
                    m[uid] = other
            if len(m) > len(best):  # the base law, not the amending ones
                best = m
        out |= best
    return out


def normalizer(aliases: dict[str, str]):
    """unit id -> base article id when it is a VBHN copy, else its own article id."""

    def norm(unit_id: str) -> str:
        art = to_article(unit_id)
        return aliases.get(art, art)

    return norm
