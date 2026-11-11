"""Select the documents of the chosen domains, deduplicate them and assign stable keys."""

from __future__ import annotations

import pandas as pd

from legalrag.ingest.domains import DOMAINS, scope_domain

CORE_DOMAINS = [
    "lao_dong",
    "bhxh",
    "hon_nhan_gia_dinh",
    "giao_thong_duong_bo",
    "dat_dai",
    "thue_tncn",
]

# Single-case documents with no Q&A value (e.g. one province's land-use plan).
RE_CASE_SPECIFIC = r"quy hoạch sử dụng đất|kế hoạch sử dụng đất|điều chỉnh quy hoạch"


def select(meta: pd.DataFrame, edges: pd.DataFrame, domains=CORE_DOMAINS) -> pd.DataFrame:
    """One row per in-scope document id with `domains` (list) and best `hop`."""
    parts = [scope_domain(meta, edges, DOMAINS[d]).assign(domain=d) for d in domains]
    s = pd.concat(parts, ignore_index=True)
    order = {"0": 0, "1": 1, "pred": 1, "2": 2}
    s["hop_rank"] = s["hop"].map(order)
    agg = s.groupby("id").agg(
        domains=("domain", lambda x: sorted(set(x))), hop_rank=("hop_rank", "min")
    )
    out = meta.merge(agg, left_on="id", right_index=True)
    case = out["title"].str.contains(RE_CASE_SPECIFIC, case=False, na=False) & out[
        "loai_van_ban"
    ].isin(["Nghị quyết", "Quyết định"])
    return out[~case].reset_index(drop=True)


def dedupe(docs: pd.DataFrame, has_text: set[str]) -> tuple[pd.DataFrame, dict[str, str]]:
    """Merge rows that are the same document (same number, type, issue date).

    Keeps the row that has full text, else the first. Returns (docs, alias id -> kept id).
    """
    docs = docs.assign(_text=docs["id"].isin(has_text))
    key = ["so_ky_hieu", "loai_van_ban", "ngay_ban_hanh"]
    docs = docs.sort_values(["_text", "id"], ascending=[False, True])
    kept = docs.drop_duplicates(key, keep="first")
    first = kept.set_index(key)["id"]
    alias = {
        r.id: first[(r.so_ky_hieu, r.loai_van_ban, r.ngay_ban_hanh)]
        for r in docs.itertuples()
        if r.id not in set(kept["id"])
    }
    merged_domains = docs.groupby(key, dropna=False)["domains"].agg(
        lambda x: sorted({d for ds in x for d in ds})
    )
    kept = kept.drop(columns=["domains"]).merge(merged_domains, left_on=key, right_index=True)
    return kept.drop(columns=["_text"]).reset_index(drop=True), alias


def assign_keys(docs: pd.DataFrame) -> pd.Series:
    """Stable human-readable key: the official number, disambiguated only when needed."""
    base = docs["so_ky_hieu"].fillna("").str.strip().str.replace(r"\s+", "", regex=True)
    base = base.str.replace("#", "", regex=False)
    no_number = base.eq("") | base.str.lower().isin(["khôngsố", "không_số"])
    iso = docs["ngay_ban_hanh_dt"].dt.strftime("%Y-%m-%d").fillna("na")
    key = base.where(~no_number, "KS@" + iso)
    dup = key.duplicated(keep=False)
    key = key.where(~dup, key + "@" + iso)
    dup = key.duplicated(keep=False)
    return key.where(~dup, key + "~" + docs["id"])
