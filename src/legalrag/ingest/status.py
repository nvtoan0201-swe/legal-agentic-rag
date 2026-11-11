"""Resolve the effect status of each document from several noisy sources.

Priority: manual override > dates in metadata > replacement edge in the graph > legacy crawl >
raw status. Every disagreement is recorded in `status_flags` so it can be reviewed.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

IN_FORCE, EXPIRED, NOT_YET, SUSPENDED, SUPERSEDED, UNKNOWN = (
    "in_force",
    "expired",
    "not_yet_effective",
    "suspended",
    "superseded",  # an older consolidated text (VBHN) of a document still in force
    "unknown",
)

RAW_MAP = {
    "Còn hiệu lực": IN_FORCE,
    "Hết hiệu lực một phần": IN_FORCE,
    "Ngưng hiệu lực một phần": IN_FORCE,
    "Hết hiệu lực toàn bộ": EXPIRED,
    "Không còn phù hợp": EXPIRED,
    "Ngưng hiệu lực": SUSPENDED,
    "Chưa có hiệu lực": NOT_YET,
    "Chưa xác định": UNKNOWN,
}

OVERRIDES_PATH = Path(__file__).with_name("overrides.yaml")


def load_overrides(path: Path = OVERRIDES_PATH) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def _ts(v) -> pd.Timestamp | None:
    if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NaT:
        return None
    return pd.Timestamp(v)


def resolve_one(
    row: dict,
    as_of: pd.Timestamp,
    replaced_by: list[tuple[str, pd.Timestamp | None]],
    legacy: dict | None,
    override: dict | None,
) -> dict:
    """row needs: tinh_trang_hieu_luc, ngay_co_hieu_luc_dt, ngay_het_hieu_luc_dt."""
    flags: list[str] = []
    eff = _ts(row.get("ngay_co_hieu_luc_dt"))
    exp = _ts(row.get("ngay_het_hieu_luc_dt"))
    raw = RAW_MAP.get(row.get("tinh_trang_hieu_luc") or "", UNKNOWN)
    if row.get("tinh_trang_hieu_luc") == "Hết hiệu lực một phần":
        flags.append("partially_expired")

    if override:
        if "ngay_co_hieu_luc" in override:
            eff = _ts(override["ngay_co_hieu_luc"])
        if "ngay_het_hieu_luc" in override:
            exp = _ts(override["ngay_het_hieu_luc"])
        flags.append("override" if override.get("verified") else "override_unverified")
        status, source = override["status"], "override"
        if exp is not None and exp <= as_of:
            status = EXPIRED
        return {
            "status": status,
            "status_source": source,
            "status_flags": flags,
            "eff": eff,
            "exp": exp,
        }

    if exp is not None and exp <= as_of:
        status, source = EXPIRED, "meta_date"
        if raw == IN_FORCE:
            flags.append("raw_in_force_but_expiry_passed")
    elif eff is not None and eff > as_of:
        status, source = NOT_YET, "meta_date"
    else:
        status, source = raw, "meta_status"

    effective_replacers = [a for a, d in replaced_by if d is not None and d <= as_of]
    if effective_replacers and status == IN_FORCE:
        status, source = EXPIRED, "graph_replaced"
        flags.append("raw_in_force_but_replaced")

    if legacy:
        lst, lexp = legacy.get("effect_status"), _ts(legacy.get("effectless_date"))
        if status == IN_FORCE and lst == "Expired" and lexp is not None and lexp < as_of:
            status, source = EXPIRED, "legacy"
            exp = exp or lexp + pd.Timedelta(days=1)
            flags.append("raw_in_force_but_legacy_expired")
        elif status == EXPIRED and lst == "In effect":
            flags.append("legacy_says_in_effect")

    return {
        "status": status,
        "status_source": source,
        "status_flags": flags,
        "eff": eff,
        "exp": exp,
    }
