"""Normalise relationship labels between documents.

The `relationships` table mixes two vocabularies: action labels (doc_id acts on other_doc_id,
e.g. "Thay thế", "Sửa đổi, bổ sung") and role labels (what other_doc_id is to doc_id, e.g.
"Văn bản sửa đổi" = other_doc_id amends doc_id). Directions were checked against issue dates:
the acting document is issued later in >= 99% of edges (scripts/explore_metadata.py).

Each label maps to (canonical type, direction). "fwd": actor = doc_id; "rev": actor = other_doc_id.
"""

from __future__ import annotations

from enum import StrEnum

import pandas as pd


class Rel(StrEnum):
    REPLACES = "replaces"
    REPEALS = "repeals"  # bãi bỏ / quy định hết hiệu lực
    REPEALS_PART = "repeals_part"
    AMENDS = "amends"
    GUIDES = "guides"  # quy định chi tiết, hướng dẫn thi hành
    BASED_ON = "based_on"  # căn cứ
    CITES = "cites"
    CONSOLIDATES = "consolidates"
    SUSPENDS = "suspends"
    CORRECTS = "corrects"
    OTHER = "other"


LABELS: dict[str, tuple[Rel, str]] = {
    "Thay thế": (Rel.REPLACES, "fwd"),
    "Bãi bỏ": (Rel.REPEALS, "fwd"),
    "Văn bản hết hiệu lực": (Rel.REPEALS, "fwd"),
    "Văn bản quy định hết hiệu lực": (Rel.REPEALS, "rev"),
    "Văn bản bị hết hiệu lực 1 phần": (Rel.REPEALS_PART, "fwd"),
    "Văn bản quy định hết hiệu lực 1 phần": (Rel.REPEALS_PART, "rev"),
    "Sửa đổi, bổ sung": (Rel.AMENDS, "fwd"),
    "Văn bản được sửa đổi": (Rel.AMENDS, "fwd"),
    "Văn bản được bổ sung": (Rel.AMENDS, "fwd"),
    "Văn bản sửa đổi": (Rel.AMENDS, "rev"),
    "Văn bản bổ sung": (Rel.AMENDS, "rev"),
    "Quy định chi tiết, hướng dẫn thi hành": (Rel.GUIDES, "fwd"),
    "Hướng dẫn áp dụng": (Rel.GUIDES, "fwd"),
    "Văn bản được HD, QĐ chi tiết": (Rel.GUIDES, "fwd"),
    "Giải thích": (Rel.GUIDES, "fwd"),
    "Văn bản HD, QĐ chi tiết": (Rel.GUIDES, "rev"),
    "Căn cứ": (Rel.BASED_ON, "fwd"),
    "Văn bản căn cứ": (Rel.BASED_ON, "fwd"),
    "Dẫn chiếu": (Rel.CITES, "fwd"),
    "Văn bản dẫn chiếu": (Rel.CITES, "fwd"),
    "Hợp nhất": (Rel.CONSOLIDATES, "fwd"),
    "Tạm ngưng hiệu lực": (Rel.SUSPENDS, "fwd"),
    "Đình chỉ thi hành": (Rel.SUSPENDS, "fwd"),
    "Văn bản bị đình chỉ": (Rel.SUSPENDS, "fwd"),
    "Văn bản bị đình chỉ 1 phần": (Rel.SUSPENDS, "fwd"),
    "Văn bản đình chỉ": (Rel.SUSPENDS, "rev"),
    "Văn bản đình chỉ 1 phần": (Rel.SUSPENDS, "rev"),
    "Đính chính": (Rel.CORRECTS, "fwd"),
}


def normalize(rels: pd.DataFrame) -> pd.DataFrame:
    """(doc_id, other_doc_id, relationship) -> deduplicated (actor, target, rel, label)."""
    mapped = rels["relationship"].map(lambda x: LABELS.get(x, (Rel.OTHER, "fwd")))
    kind = mapped.str[0]
    fwd = mapped.str[1] == "fwd"
    out = pd.DataFrame(
        {
            "actor": rels["doc_id"].where(fwd, rels["other_doc_id"]),
            "target": rels["other_doc_id"].where(fwd, rels["doc_id"]),
            "rel": kind.astype(str),
            "label": rels["relationship"],
        }
    )
    return out.drop_duplicates(["actor", "target", "rel"]).reset_index(drop=True)
