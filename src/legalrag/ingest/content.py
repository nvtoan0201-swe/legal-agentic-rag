"""Fetch full text for selected documents: current HTML first, legacy plain text as fallback."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

MIN_CHARS = 200


def read_current(path: Path, ids: list[str]) -> dict[str, str]:
    """Read one row group at a time to keep memory low (~150 MB per group)."""
    wanted = pa.array(ids)
    pf = pq.ParquetFile(path)
    out: dict[str, str] = {}
    for g in range(pf.num_row_groups):
        t = pf.read_row_group(g, columns=["id", "content_html"])
        t = t.filter(pc.is_in(t["id"], value_set=wanted))
        out.update(zip(t["id"].to_pylist(), t["content_html"].to_pylist(), strict=True))
    return out


def read_legacy(path: Path, ids: list[int]) -> dict[int, str]:
    """legacy/content.parquet is a single 3.5 GB row group; duckdb streams it."""
    if not ids:
        return {}
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'; SET threads=2; SET preserve_insertion_order=false")
    con.register("wanted", pd.DataFrame({"id": ids}))
    rows = con.execute(
        f"SELECT id, content FROM read_parquet('{path}') WHERE id IN (SELECT id FROM wanted)"
    ).fetchall()
    return dict(rows)


def legacy_lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


def match_legacy(docs: pd.DataFrame, legacy_meta: pd.DataFrame) -> pd.Series:
    """docs.id -> legacy id, matched on official number + issue date."""
    lm = legacy_meta.assign(d=pd.to_datetime(legacy_meta["issuance_date"], errors="coerce"))
    lm = lm.dropna(subset=["d"]).drop_duplicates(["document_number", "d"])
    m = docs[["id", "so_ky_hieu", "ngay_ban_hanh_dt"]].merge(
        lm[["id", "document_number", "d"]].rename(columns={"id": "legacy_id"}),
        left_on=["so_ky_hieu", "ngay_ban_hanh_dt"],
        right_on=["document_number", "d"],
    )
    return m.drop_duplicates("id").set_index("id")["legacy_id"]


def text_chars(lines: list[str]) -> int:
    return sum(map(len, lines))
