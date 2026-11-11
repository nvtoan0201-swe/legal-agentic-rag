import pandas as pd

from legalrag.ingest.status import EXPIRED, IN_FORCE, NOT_YET, resolve_one

AS_OF = pd.Timestamp("2026-11-11")


def row(status, eff=None, exp=None):
    return {
        "tinh_trang_hieu_luc": status,
        "ngay_co_hieu_luc_dt": pd.Timestamp(eff) if eff else None,
        "ngay_het_hieu_luc_dt": pd.Timestamp(exp) if exp else None,
    }


def test_raw_in_force():
    r = resolve_one(row("Còn hiệu lực", "2021-01-01"), AS_OF, [], None, None)
    assert (r["status"], r["status_source"]) == (IN_FORCE, "meta_status")


def test_expiry_date_wins_over_raw_status():
    r = resolve_one(row("Còn hiệu lực", "2021-01-01", "2026-07-01"), AS_OF, [], None, None)
    assert r["status"] == EXPIRED
    assert "raw_in_force_but_expiry_passed" in r["status_flags"]


def test_not_yet_effective():
    r = resolve_one(row("Còn hiệu lực", "2027-01-01"), AS_OF, [], None, None)
    assert r["status"] == NOT_YET


def test_effective_replacement_expires_document():
    r = resolve_one(row("Còn hiệu lực"), AS_OF, [("new", pd.Timestamp("2025-01-01"))], None, None)
    assert (r["status"], r["status_source"]) == (EXPIRED, "graph_replaced")


def test_future_replacement_does_not():
    r = resolve_one(row("Còn hiệu lực"), AS_OF, [("new", pd.Timestamp("2027-01-01"))], None, None)
    assert r["status"] == IN_FORCE


def test_legacy_expired_with_past_date():
    legacy = {"effect_status": "Expired", "effectless_date": "2026-06-30"}
    r = resolve_one(row("Còn hiệu lực"), AS_OF, [], legacy, None)
    assert (r["status"], r["status_source"]) == (EXPIRED, "legacy")
    assert r["exp"] == pd.Timestamp("2026-07-01")


def test_legacy_disagreement_is_only_flagged():
    legacy = {"effect_status": "In effect", "effectless_date": None}
    r = resolve_one(row("Hết hiệu lực toàn bộ"), AS_OF, [], legacy, None)
    assert r["status"] == EXPIRED
    assert "legacy_says_in_effect" in r["status_flags"]


def test_override_wins_and_is_flagged_when_unverified():
    ov = {"status": "in_force", "ngay_het_hieu_luc": None, "verified": False}
    r = resolve_one(row("Hết hiệu lực toàn bộ", "2025-07-01", "2026-01-01"), AS_OF, [], None, ov)
    assert (r["status"], r["exp"]) == (IN_FORCE, None)
    assert "override_unverified" in r["status_flags"]
