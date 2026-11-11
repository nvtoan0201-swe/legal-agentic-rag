import pandas as pd

from legalrag.ingest.relations import Rel, normalize


def test_normalize_direction_and_dedup():
    rels = pd.DataFrame(
        {
            "doc_id": ["new", "old", "nd", "law"],
            "other_doc_id": ["old", "new", "law", "nd"],
            "relationship": [
                "Văn bản hết hiệu lực",  # new làm old hết hiệu lực
                "Văn bản quy định hết hiệu lực",  # trên trang của old: new quy định hết hiệu lực
                "Quy định chi tiết, hướng dẫn thi hành",
                "Văn bản HD, QĐ chi tiết",
            ],
        }
    )
    out = normalize(rels)
    assert len(out) == 2
    rows = {(r.actor, r.target, r.rel) for r in out.itertuples()}
    assert ("new", "old", Rel.REPEALS) in rows
    assert ("nd", "law", Rel.GUIDES) in rows


def test_unknown_label_is_other():
    rels = pd.DataFrame({"doc_id": ["a"], "other_doc_id": ["b"], "relationship": ["Nhãn lạ"]})
    assert normalize(rels).loc[0, "rel"] == Rel.OTHER
