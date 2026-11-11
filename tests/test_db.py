"""Integration test: needs a running Postgres (make up) and LEGALRAG_TEST_DSN set."""

import os

import pandas as pd
import pytest

from legalrag.ingest.parser import parse

DSN = os.environ.get("LEGALRAG_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="LEGALRAG_TEST_DSN not set")


def test_load_roundtrip(tmp_path):
    import psycopg

    from legalrag.db import load

    p = parse(["Điều 1. A", "1. x", "a) y", "Điều 2. B"], "1/2020/QH14")
    units = pd.DataFrame(
        [
            {
                "unit_id": u.unit_id,
                "doc_key": "1/2020/QH14",
                "kind": u.kind,
                "number": u.number,
                "parent_id": u.parent_id,
                "ordinal": u.ordinal,
                "title": u.title,
                "text": u.text,
                "chuong": u.chuong,
                "muc": u.muc,
            }
            for u in p.units
        ]
    )
    docs = pd.DataFrame(
        [
            {
                "doc_key": "1/2020/QH14",
                "source_id": "1",
                "legacy_id": None,
                "so_ky_hieu": "1/2020/QH14",
                "loai_van_ban": "Luật",
                "title": "Luật thử",
                "co_quan_ban_hanh": "Quốc hội",
                "ngay_ban_hanh": pd.Timestamp("2020-01-01"),
                "ngay_co_hieu_luc": pd.Timestamp("2020-07-01"),
                "ngay_het_hieu_luc": None,
                "status_raw": "Còn hiệu lực",
                "status": "in_force",
                "status_source": "meta_status",
                "status_flags": [],
                "domains": ["lao_dong"],
                "hop_rank": 0,
                "core": True,
                "content_source": "vbpl_html",
                "parse_clean": True,
                "parse_issues": "{}",
                "n_articles": 2,
                "dropped_share": 0.0,
                "attached_share": 0.0,
                "preamble": "",
            }
        ]
    )
    rels = pd.DataFrame(
        [
            {
                "actor_key": None,
                "target_key": "1/2020/QH14",
                "actor_source_id": "9",
                "target_source_id": "1",
                "rel": "guides",
                "label": "x",
                "source": "vbpl",
                "suspect": False,
            }
        ]
    )
    docs.to_parquet(tmp_path / "documents.parquet")
    units.to_parquet(tmp_path / "units.parquet")
    rels.to_parquet(tmp_path / "relations.parquet")
    assert load(DSN, tmp_path) == {"documents": 1, "units": 4, "relations": 1}
    with psycopg.connect(DSN) as conn:
        got = conn.execute(
            "select parent_id from units where unit_id = %s", ["1/2020/QH14#d1-k1-a"]
        ).fetchone()
    assert got == ("1/2020/QH14#d1-k1",)
