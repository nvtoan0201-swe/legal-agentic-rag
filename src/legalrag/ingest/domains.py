"""Xác định phạm vi văn bản cho từng lĩnh vực.

Không lọc theo `nganh`/`linh_vuc` được: 66% văn bản có linh_vuc = "Chưa phân loại" và các luật mới
nhất để trống cả hai trường. Cách làm: chọn luật gốc (anchor) theo tên, rồi mở rộng theo đồ thị quan
hệ: văn bản hướng dẫn / sửa đổi / thay thế / hợp nhất luật gốc (bước 1), rồi văn bản hướng dẫn hoặc
sửa đổi các văn bản bước 1 (bước 2). Chỉ giữ văn bản trung ương có tính quy phạm.
"""

from __future__ import annotations

import re

import pandas as pd

from legalrag.ingest.relations import Rel

# Tên luật gốc (không kèm chữ "Luật"/"Bộ luật"). Tiêu đề trong dataset không đồng nhất: có bản ghi
# chỉ ghi "Đất đai" hay "doanh nghiệp", có bản viết "Bộ Luật lao động".
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
    """Khớp tên luật đứng sau "Luật " hoặc ở đầu tiêu đề.

    Tên phải kết thúc bởi "số", "năm", dấu phẩy/chấm phẩy, " và " hoặc hết tiêu đề.
    """
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
# Các loại chỉ cơ quan trung ương ban hành; không cần xét `pham_vi` (đôi khi bị trống).
ALWAYS_CENTRAL = {"Luật", "Bộ luật", "Pháp lệnh", "Nghị định", "Thông tư", "Thông tư liên tịch"}

# Quan hệ dùng để kéo văn bản vào phạm vi: actor có quan hệ này với văn bản đã trong phạm vi.
PULL_IN = {Rel.GUIDES, Rel.AMENDS, Rel.REPLACES, Rel.REPEALS, Rel.REPEALS_PART, Rel.CONSOLIDATES}
# Văn bản cũ bị anchor thay thế/bãi bỏ: giữ lại để làm câu eval "văn bản hết hiệu lực".
PREDECESSOR = {Rel.REPLACES, Rel.REPEALS}


def eligible(meta: pd.DataFrame) -> pd.Series:
    loai = meta["loai_van_ban"]
    central = loai.isin(ALWAYS_CENTRAL) | meta["pham_vi"].isin(CENTRAL_SCOPES)
    return loai.isin(NORMATIVE_TYPES) & central


def find_anchors(meta: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    """Luật gốc của lĩnh vực: luật/bộ luật/pháp lệnh, luật sửa đổi riêng luật đó, và văn bản hợp
    nhất của luật đó. Bỏ luật sửa nhiều luật cùng lúc (vd 03/2022/QH15) vì sẽ kéo lĩnh vực khác vào;
    chúng vẫn vào phạm vi ở hop 1 qua quan hệ `amends`. Dataset thiếu một số luật gốc (vd Luật thuế
    TNCN 2007), khi đó luật sửa đổi và văn bản hợp nhất là cửa vào duy nhất."""
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
    """Trả về các văn bản thuộc lĩnh vực, cột `hop` = 0 (anchor), 1, 2, hoặc 'pred' (tiền nhiệm)."""
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
