"""Load the processed corpus (parquet) into PostgreSQL."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

SCHEMA = Path(__file__).with_name("schema.sql")

DOC_COLS = [
    "doc_key",
    "source_id",
    "legacy_id",
    "so_ky_hieu",
    "loai_van_ban",
    "title",
    "co_quan_ban_hanh",
    "ngay_ban_hanh",
    "ngay_co_hieu_luc",
    "ngay_het_hieu_luc",
    "status_raw",
    "status",
    "status_source",
    "status_flags",
    "domains",
    "hop_rank",
    "content_source",
    "parse_clean",
    "parse_issues",
    "n_articles",
    "dropped_share",
    "attached_share",
    "preamble",
]
UNIT_COLS = [
    "unit_id",
    "doc_key",
    "kind",
    "number",
    "parent_id",
    "ordinal",
    "title",
    "text",
    "chuong",
    "muc",
]
REL_COLS = [
    "actor_key",
    "target_key",
    "actor_source_id",
    "target_source_id",
    "rel",
    "label",
    "source",
    "suspect",
]


def _clean(v):
    """pandas/numpy values -> plain Python for COPY."""
    if v is None or v is pd.NA or v is pd.NaT:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if isinstance(v, pd.Timestamp):
        return v.date()
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, np.generic):
        return v.item()
    return v


def _copy(cur: psycopg.Cursor, table: str, cols: list[str], df: pd.DataFrame) -> None:
    with cur.copy(f"COPY {table} ({', '.join(cols)}) FROM STDIN") as cp:
        for row in df[cols].itertuples(index=False, name=None):
            cp.write_row([_clean(v) for v in row])


def load(dsn: str, processed: Path) -> dict[str, int]:
    docs = pd.read_parquet(processed / "documents.parquet")
    units = pd.read_parquet(processed / "units.parquet")
    rels = pd.read_parquet(processed / "relations.parquet")
    for c in ["legacy_id", "n_articles", "hop_rank"]:
        docs[c] = docs[c].astype("Int64")
    docs["parse_issues"] = docs["parse_issues"].map(
        lambda s: json.dumps(json.loads(s)) if s else None
    )
    # Parents must exist before children (FK on parent_id): units are written in document order.
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(SCHEMA.read_text())
        _copy(cur, "documents", DOC_COLS, docs)
        _copy(cur, "units", UNIT_COLS, units)
        _copy(cur, "relations", REL_COLS, rels)
        conn.commit()
    return {"documents": len(docs), "units": len(units), "relations": len(rels)}
