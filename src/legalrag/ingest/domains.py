"""Decide which documents belong to a legal domain.

`nganh`/`linh_vuc` cannot be used: 69% of `linh_vuc` is "Chưa phân loại" and the newest laws leave
both empty. Instead: pick anchor laws by title, then follow the relation graph: documents that
guide / amend / replace / consolidate the anchors (hop 1), then documents that guide or amend
hop-1 documents (hop 2). Only central, normative documents are kept.
"""

from __future__ import annotations

import re

import pandas as pd

from legalrag.ingest.relations import Rel

# Anchor law names without "Luật"/"Bộ luật". Titles are inconsistent: some records are just
# "Đất đai" or "doanh nghiệp", others "Bộ Luật lao động".
DOMAINS: dict[str, list[str]] = {
    "lao_dong": ["Lao động", "Việc làm"],
    "dat_dai": ["Đất đai"],
    "hon_nhan_gia_dinh": ["Hôn nhân và gia đình"],
    "thue_tncn": ["Thuế thu nhập cá nhân"],
    "giao_thong_duong_bo": [
        "Giao thông đường bộ",
        "Trật tự, an toàn giao thông đường bộ",
        "Đường bộ",
    ],
    "bhxh": ["Bảo hiểm xã hội"],
    "doanh_nghiep": ["Doanh nghiệp"],
    "bhyt": ["Bảo hiểm y tế"],
    "nha_o": ["Nhà ở"],
    "cu_tru": ["Cư trú"],
}


def anchor_regex(names: list[str]) -> re.Pattern[str]:
    """Match a law name after "Luật " or at the start of the title, ending at "số", "năm",
    a comma/semicolon, " và " or the end of the title."""
    alts = "|".join(re.escape(n) for n in names)
    return re.compile(
        rf"(?:^|luật\s+)(?:{alts})(?=\s+số|\s+năm|\s*$|\s*,|\s*;|\s+và\s)", re.IGNORECASE
    )


ANCHOR_TYPES = {"Luật", "Bộ luật", "Pháp lệnh"}
NORMATIVE_TYPES = {
    "Luật",
    "Bộ luật",
    "Pháp lệnh",
    "Nghị định",
    "Nghị quyết",
    "Thông tư",
    "Thông tư liên tịch",
    "Quyết định",
    "Văn bản hợp nhất",
}
CENTRAL_SCOPES = {"Trung ương", "Toàn quốc"}
# Always issued centrally, so `pham_vi` (sometimes empty) is not needed.
ALWAYS_CENTRAL = {"Luật", "Bộ luật", "Pháp lệnh", "Nghị định", "Thông tư", "Thông tư liên tịch"}

# Relations that pull an actor into scope when its target is already in scope.
PULL_IN = {Rel.GUIDES, Rel.AMENDS, Rel.REPLACES, Rel.REPEALS, Rel.REPEALS_PART, Rel.CONSOLIDATES}
# Old documents replaced by an anchor: kept for "expired document" eval questions.
PREDECESSOR = {Rel.REPLACES, Rel.REPEALS}


def eligible(meta: pd.DataFrame) -> pd.Series:
    loai = meta["loai_van_ban"]
    central = loai.isin(ALWAYS_CENTRAL) | meta["pham_vi"].isin(CENTRAL_SCOPES)
    return loai.isin(NORMATIVE_TYPES) & central


def find_anchors(meta: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    """Anchor laws: laws/codes/ordinances, amendments of that single law, and consolidated texts
    (VBHN) of it. Omnibus amendments (e.g. 03/2022/QH15) are excluded because they would pull other
    domains in; they still enter at hop 1 through `amends`. Some base laws are missing from the
    dataset (e.g. Luật thuế TNCN 2007), so amendments and VBHN are the only way in."""
    title = meta["title"].fillna("")
    loai = meta["loai_van_ban"]
    title_ok = title.str.contains(anchor_regex(names))
    omnibus = title.str.contains(r"sửa đổi|bổ sung", case=False) & (
        title.str.lower().str.count(r"luật\s") > 2
    )
    law = loai.isin(ANCHOR_TYPES)
    vbhn_of_law = loai.eq("Văn bản hợp nhất") & title.str.contains(
        r"^Văn bản hợp nhất(?: số \S+)? (?:Bộ )?Luật", case=False
    )
    return meta[title_ok & ~omnibus & (law | vbhn_of_law)]


def scope_domain(meta: pd.DataFrame, edges: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    """Documents of a domain; column `hop` is 0 (anchor), 1, 2 or 'pred' (predecessor)."""
    ok = set(meta.loc[eligible(meta), "id"])
    anchors = set(find_anchors(meta, names)["id"]) & ok
    pull = edges[edges["rel"].isin(PULL_IN)]

    hop1 = set(pull.loc[pull["target"].isin(anchors), "actor"]) & ok
    hop1 -= anchors
    pred = (
        set(edges.loc[edges["rel"].isin(PREDECESSOR) & edges["actor"].isin(anchors), "target"]) & ok
    )
    pred -= anchors | hop1
    known = anchors | hop1 | pred
    # Expand hop 2 only from sub-law documents: a law from another domain that amends an anchor
    # (e.g. BLLĐ amending Luật BHXH) would otherwise drag that whole domain in.
    laws = set(meta.loc[meta["loai_van_ban"].isin(ANCHOR_TYPES), "id"])
    hop2 = set(pull.loc[pull["target"].isin(hop1 - laws), "actor"]) & ok
    hop2 -= known

    hop = {i: 0 for i in anchors} | {i: 1 for i in hop1} | {i: 2 for i in hop2}
    hop |= {i: "pred" for i in pred}
    out = meta[meta["id"].isin(hop)].copy()
    out["hop"] = out["id"].map(hop).astype(str)
    return out
