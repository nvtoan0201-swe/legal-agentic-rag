"""Silver gold for `expired` items: the article of the current law with the same title.

Items mapped from thangvip/vietnamese-legal-qa about an expired law have the old article in
`forbidden_articles` and no gold. When exactly one in-force core law of the same domain has an
article with the same (normalised) title, that article becomes the gold. Same title does not
guarantee the same subject matter, so these items stay `reviewed=false` and are reported apart.
"""

from __future__ import annotations

import re
from collections import defaultdict

from legalrag.eval.schema import Category, EvalItem
from legalrag.store import Corpus

LAW_TYPES = ("Luật", "Bộ luật")


def norm_title(article_text: str) -> str:
    t = re.sub(r"^Điều\s+\d+[a-zđ]?\.?\s*", "", article_text.strip()).lower()
    return re.sub(r"\W+", " ", t).strip()


def title_index(corpus: Corpus) -> dict[str, list[str]]:
    d = corpus.docs
    live = d[(d["status"] == "in_force") & d["loai_van_ban"].isin(LAW_TYPES) & d["core"]].index
    u = corpus.units
    arts = u[(u["kind"] == "dieu") & u["doc_key"].isin(live)]
    idx: dict[str, list[str]] = defaultdict(list)
    for uid, text in zip(arts["unit_id"], arts["text"], strict=True):
        idx[norm_title(text)].append(uid)
    return idx


def fill_current_gold(items: list[EvalItem], corpus: Corpus) -> list[EvalItem]:
    """Copies of the `expired` items whose current article can be found; others are dropped."""
    idx = title_index(corpus)
    out = []
    for it in items:
        if it.category != Category.EXPIRED or it.gold_articles or not it.forbidden_articles:
            continue
        old = it.forbidden_articles[0]
        doc = corpus.doc(old.split("#")[0])
        if doc is None:
            continue
        domains = set(doc["domains"])
        cand = [
            x
            for x in idx.get(norm_title(corpus.heading(old)), [])
            if domains & set(corpus.doc(x.split("#")[0])["domains"])
        ]
        if len(cand) == 1:
            out.append(
                it.model_copy(
                    update={
                        "gold_articles": cand,
                        "meta": it.meta | {"gold": "silver_same_title"},
                    }
                )
            )
    return out
