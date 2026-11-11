"""Thống kê metadata + quan hệ của th1nhng0/vietnamese-legal-documents.

Chỉ dùng config `metadata`, `relationships` và `legacy_metadata` (không tải toàn văn).
Kết quả: reports/data_exploration.md

    uv run python scripts/explore_metadata.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from legalrag.ingest.domains import DOMAINS, eligible, find_anchors, scope_domain
from legalrag.ingest.metadata import SNAPSHOT_DATE, download, is_missing, load_metadata
from legalrag.ingest.relations import LABELS, normalize

# Đối chiếu tay với hiểu biết thực tế (tính đến 2026-07). Dùng để ước lượng độ tin cậy trường
# hiệu lực, không phải nguồn chân lí: nên kiểm lại trên vbpl.vn.
KNOWN_FACTS = [
    # (số hiệu, loại, tình trạng thực tế, ngày hiệu lực thực tế, ngày hết hiệu lực thực tế, ghi chú)
    ("10/2012/QH13", "Bộ luật", "Hết hiệu lực toàn bộ", "01/05/2013", "01/01/2021", "BLLĐ 2012"),
    ("45/2019/QH14", "Bộ luật", "Còn hiệu lực", "01/01/2021", None, "BLLĐ 2019"),
    (
        "45/2013/QH13",
        "Luật",
        "Hết hiệu lực toàn bộ",
        "01/07/2014",
        "01/08/2024",
        "Luật Đất đai 2013",
    ),
    (
        "31/2024/QH15",
        "Luật",
        "Còn hiệu lực",
        "01/08/2024",
        None,
        "Luật Đất đai 2024, hiệu lực sớm theo Luật 43/2024/QH15",
    ),
    ("52/2014/QH13", "Luật", "Còn hiệu lực", "01/01/2015", None, "Luật HN&GĐ 2014"),
    ("58/2014/QH13", "Luật", "Hết hiệu lực toàn bộ", "01/01/2016", "01/07/2025", "Luật BHXH 2014"),
    ("41/2024/QH15", "Luật", "Còn hiệu lực", "01/07/2025", None, "Luật BHXH 2024"),
    ("23/2008/QH12", "Luật", "Hết hiệu lực toàn bộ", "01/07/2009", "01/01/2025", "Luật GTĐB 2008"),
    ("36/2024/QH15", "Luật", "Còn hiệu lực", "01/01/2025", None, "Luật TTATGTĐB"),
    ("68/2014/QH13", "Luật", "Hết hiệu lực toàn bộ", "01/07/2015", "01/01/2021", "Luật DN 2014"),
    ("59/2020/QH14", "Luật", "Còn hiệu lực", "01/01/2021", None, "Luật DN 2020"),
    (
        "04/2007/QH12",
        "Luật",
        "Còn hiệu lực",
        "01/01/2009",
        None,
        "Luật thuế TNCN 2007 (tại 07/2026)",
    ),
]


def md(df: pd.DataFrame | pd.Series, **kw) -> str:
    if isinstance(df, pd.Series):
        df = df.to_frame()
    return df.to_markdown(**kw)


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def section_missing(m: pd.DataFrame) -> str:
    cols = [c for c in m.columns if not c.endswith("_dt") and c != "nam_ban_hanh"]
    rows = []
    for c in cols:
        null = m[c].isna().mean()
        miss = is_missing(m[c]).mean()
        rows.append(
            {
                "cột": c,
                "null": pct(null),
                "thiếu (gồm 'Chưa phân loại', 'Chưa xác định', rỗng)": pct(miss),
                "số giá trị khác nhau": m[c].nunique(),
                "ví dụ": str(m[c].dropna().iloc[0])[:50] if m[c].notna().any() else "",
            }
        )
    parse_fail = {
        c: pct((m[c].notna() & m[f"{c}_dt"].isna()).mean())
        for c in ["ngay_ban_hanh", "ngay_co_hieu_luc", "ngay_het_hieu_luc", "ngay_dang_cong_bao"]
    }
    out = "## 2. Các cột metadata và tỉ lệ thiếu\n\n" + md(pd.DataFrame(rows), index=False)
    out += "\n\nTỉ lệ ngày có giá trị nhưng không parse được theo DD/MM/YYYY: "
    out += ", ".join(f"`{k}` {v}" for k, v in parse_fail.items()) + "\n"
    return out


def section_distributions(m: pd.DataFrame) -> str:
    out = "## 3. Phân bố\n\n### 3.1 Theo loại văn bản\n\n"
    t = m["loai_van_ban"].value_counts().rename("số văn bản")
    out += md(t) + "\n\n### 3.2 Theo phạm vi\n\n"
    out += md(m["pham_vi"].value_counts().head(5).rename("số văn bản")) + "\n\n"
    out += "### 3.3 Theo thập kỉ ban hành\n\n"
    dec = (m["nam_ban_hanh"] // 10 * 10).value_counts().sort_index().rename("số văn bản")
    dec.index = [f"{int(i)}s" for i in dec.index]
    out += md(dec) + "\n\n### 3.4 Theo năm (2010–2026), chỉ văn bản trung ương có tính quy phạm\n\n"
    e = m[eligible(m)]
    y = e[e["nam_ban_hanh"] >= 2010]
    out += md(pd.crosstab(y["nam_ban_hanh"], y["loai_van_ban"])) + "\n\n"
    out += "### 3.5 Theo ngành (top 25)\n\n"
    out += md(m["nganh"].value_counts(dropna=False).head(25).rename("số văn bản")) + "\n\n"
    out += "### 3.6 Theo lĩnh vực (top 30)\n\n"
    out += md(m["linh_vuc"].value_counts(dropna=False).head(30).rename("số văn bản")) + "\n\n"
    luat = m[m["loai_van_ban"].isin(["Luật", "Bộ luật"])]
    out += (
        f"Trong {len(luat)} Luật/Bộ luật: `nganh` thiếu {pct(is_missing(luat['nganh']).mean())}, "
        f"`linh_vuc` thiếu {pct(is_missing(luat['linh_vuc']).mean())}. Luật ban hành từ 2024: "
        f"`linh_vuc` thiếu {pct(is_missing(luat[luat.nam_ban_hanh >= 2024]['linh_vuc']).mean())}.\n"
    )
    return out


def section_duplicates(m: pd.DataFrame) -> str:
    noTrans = m[m["loai_van_ban"] != "Bản dịch văn bản"]
    dup = noTrans[noTrans.duplicated("so_ky_hieu", keep=False) & noTrans["so_ky_hieu"].notna()]
    e = noTrans[eligible(noTrans)]
    dup_e = e[e.duplicated(["so_ky_hieu", "loai_van_ban"], keep=False) & e["so_ky_hieu"].notna()]
    out = "## 4. Trùng số hiệu\n\n"
    out += (
        f"- `id` là duy nhất ({m['id'].is_unique}). Định dạng id: số "
        f"{pct(m['id'].str.fullmatch(r'\d+').mean())}, `vbpqta_*` (bản dịch) "
        f"{pct(m['id'].str.startswith('vbpqta_').mean())}, còn lại là UUID / tiền tố khác.\n"
        f"- Bỏ bản dịch, {len(dup)} dòng có `so_ky_hieu` trùng với dòng khác (phần lớn là số hiệu "
        f"ngắn của văn bản cũ hoặc địa phương, vd `01/CT`).\n"
        f"- Trong văn bản trung ương có tính quy phạm, {len(dup_e)} dòng trùng cả số hiệu lẫn loại. "
        f"→ Không dùng `so_ky_hieu` làm khoá; id điều khoản phải gắn với `id` gốc khi trùng.\n\n"
    )
    ex = dup_e.sort_values("so_ky_hieu")[
        ["id", "so_ky_hieu", "loai_van_ban", "ngay_ban_hanh", "tinh_trang_hieu_luc"]
    ].head(10)
    return out + md(ex, index=False) + "\n"


def section_effect(m: pd.DataFrame, edges: pd.DataFrame) -> str:
    out = "## 5. Trường hiệu lực và độ tin cậy\n\n"
    out += f"Snapshot ngày {SNAPSHOT_DATE.date()} (theo dataset card).\n\n### 5.1 Phân bố\n\n"
    out += md(m["tinh_trang_hieu_luc"].value_counts(dropna=False).rename("số văn bản")) + "\n\n"

    st = m["tinh_trang_hieu_luc"]
    het = m["ngay_het_hieu_luc_dt"]
    co = m["ngay_co_hieu_luc_dt"]
    bh = m["ngay_ban_hanh_dt"]
    checks = {
        "'Hết hiệu lực toàn bộ' nhưng thiếu ngày hết hiệu lực": (
            st.eq("Hết hiệu lực toàn bộ") & het.isna(),
            st.eq("Hết hiệu lực toàn bộ"),
        ),
        "'Còn hiệu lực' nhưng ngày hết hiệu lực ≤ snapshot": (
            st.eq("Còn hiệu lực") & (het <= SNAPSHOT_DATE),
            st.eq("Còn hiệu lực"),
        ),
        "'Còn hiệu lực' nhưng có ngày hết hiệu lực (bất kì)": (
            st.eq("Còn hiệu lực") & het.notna(),
            st.eq("Còn hiệu lực"),
        ),
        "'Hết hiệu lực toàn bộ' nhưng ngày hết hiệu lực > snapshot": (
            st.eq("Hết hiệu lực toàn bộ") & (het > SNAPSHOT_DATE),
            st.eq("Hết hiệu lực toàn bộ"),
        ),
        "'Chưa có hiệu lực' nhưng ngày có hiệu lực ≤ snapshot": (
            st.eq("Chưa có hiệu lực") & (co <= SNAPSHOT_DATE),
            st.eq("Chưa có hiệu lực"),
        ),
        "Ngày có hiệu lực trước ngày ban hành": (co < bh, co.notna() & bh.notna()),
        "Ngày hết hiệu lực trước ngày có hiệu lực": (het < co, het.notna() & co.notna()),
        "Thiếu ngày có hiệu lực": (co.isna(), pd.Series(True, index=m.index)),
    }
    rows = [
        {
            "kiểm tra": k,
            "số lỗi": int(bad.sum()),
            "trên tổng": int(base.sum()),
            "tỉ lệ": pct(bad.sum() / max(base.sum(), 1)),
        }
        for k, (bad, base) in checks.items()
    ]
    out += "### 5.2 Kiểm tra nhất quán nội bộ (toàn bộ dataset)\n\n" + md(
        pd.DataFrame(rows), index=False
    )

    # Đối chiếu với đồ thị: văn bản bị thay thế/bãi bỏ toàn bộ mà status vẫn còn hiệu lực.
    e = m[eligible(m)].set_index("id")
    killers = edges[edges["rel"].isin(["replaces", "repeals"])]
    killers = killers[killers["target"].isin(e.index) & killers["actor"].isin(e.index)]
    killers = killers.assign(
        actor_eff=killers["actor"].map(e["ngay_co_hieu_luc_dt"]),
        target_status=killers["target"].map(e["tinh_trang_hieu_luc"]),
    )
    killed = killers[killers["actor_eff"] <= SNAPSHOT_DATE].drop_duplicates("target")
    vc = killed["target_status"].value_counts().rename("số văn bản")
    out += (
        "\n\n### 5.3 Đối chiếu với đồ thị quan hệ (văn bản trung ương có tính quy phạm)\n\n"
        f"{len(killed)} văn bản bị một văn bản khác (đã có hiệu lực) *thay thế* hoặc *bãi bỏ/quy định "
        "hết hiệu lực*. Tình trạng ghi trong metadata của chúng:\n\n" + md(vc) + "\n\n"
        "Lưu ý: quan hệ 'Bãi bỏ' trên vbpl.vn có thể chỉ bãi bỏ một phần, nên 'Hết hiệu lực một "
        "phần' không hẳn là lỗi; 'Còn hiệu lực' thì đáng ngờ.\n\n"
    )

    rows = []
    for so, loai, st_true, co_true, het_true, note in KNOWN_FACTS:
        r = m[(m["so_ky_hieu"] == so) & (m["loai_van_ban"] == loai)]
        if r.empty:
            rows.append({"văn bản": f"{so} ({note})", "khớp": "không tìm thấy"})
            continue
        r = r.iloc[0]
        st_ok = (r["tinh_trang_hieu_luc"] in ("Còn hiệu lực", "Hết hiệu lực một phần")) == (
            st_true == "Còn hiệu lực"
        )
        co_ok = r["ngay_co_hieu_luc"] == co_true
        het_ok = (r["ngay_het_hieu_luc"] if pd.notna(r["ngay_het_hieu_luc"]) else None) == het_true
        rows.append(
            {
                "văn bản": f"{so} ({note})",
                "tình trạng (dataset)": r["tinh_trang_hieu_luc"],
                "hiệu lực (dataset)": r["ngay_co_hieu_luc"],
                "hết HL (dataset)": r["ngay_het_hieu_luc"],
                "thực tế": f"{st_true}; {co_true} → {het_true or '—'}",
                "khớp": "✓"
                if st_ok and co_ok and het_ok
                else "✗ "
                + ",".join(
                    n
                    for n, ok in [("tình trạng", st_ok), ("ngày HL", co_ok), ("ngày hết", het_ok)]
                    if not ok
                ),
            }
        )
    out += (
        "### 5.4 Đối chiếu tay với một số luật đã biết\n\n"
        + md(pd.DataFrame(rows), index=False)
        + "\n"
    )
    return out


def section_legacy(m: pd.DataFrame, legacy: pd.DataFrame) -> str:
    """So tình trạng hiệu lực với bản crawl cũ (legacy, nguồn và hệ id khác)."""
    e = m[eligible(m) & m["loai_van_ban"].isin(["Luật", "Bộ luật", "Nghị định", "Thông tư"])]
    lg = legacy.assign(
        ngay_ban_hanh_dt=pd.to_datetime(legacy["issuance_date"], errors="coerce"),
    )
    j = e.merge(
        lg[["document_number", "ngay_ban_hanh_dt", "effect_status", "effectless_date", "title"]],
        left_on=["so_ky_hieu", "ngay_ban_hanh_dt"],
        right_on=["document_number", "ngay_ban_hanh_dt"],
        suffixes=("", "_legacy"),
    ).drop_duplicates("id")
    cur = j["tinh_trang_hieu_luc"].map(
        lambda x: (
            "in force"
            if x in ("Còn hiệu lực", "Hết hiệu lực một phần")
            else "expired"
            if x == "Hết hiệu lực toàn bộ"
            else "other"
        )
    )
    tab = pd.crosstab(cur.rename("hiện tại"), j["effect_status"].rename("legacy"))
    both = cur.isin(["in force", "expired"]) & j["effect_status"].isin(["In effect", "Expired"])
    agree = ((cur == "in force") == (j["effect_status"] == "In effect"))[both].mean()
    law = j[both & j["loai_van_ban"].isin(["Luật", "Bộ luật"])]
    law_dis = law[(cur[law.index] == "in force") != (law["effect_status"] == "In effect")]
    cols = [
        "so_ky_hieu",
        "tinh_trang_hieu_luc",
        "ngay_het_hieu_luc",
        "effect_status",
        "effectless_date",
        "title_legacy",
    ]
    return (
        "### 5.5 Đối chiếu với bản crawl cũ (`legacy_metadata`)\n\n"
        f"Bản cũ: {len(legacy):,} văn bản, ngày ban hành mới nhất {legacy['issuance_date'].max()} "
        "(crawl trước bản hiện tại vài tháng), tiêu đề kiểu khác (vd 'Luật Đất đai 2024'), "
        "hệ id khác. Ghép theo số hiệu + ngày ban hành cho Luật/Bộ luật/NĐ/TT trung ương: "
        f"{len(j):,}/{len(e):,} khớp.\n\n" + md(tab) + "\n\n"
        f"Trên các cặp có trạng thái rõ ràng ở cả hai bên, tỉ lệ đồng ý: {pct(agree)}. "
        f"Luật/Bộ luật lệch nhau: {len(law_dis)}.\n\n"
        + (md(law_dis[cols].head(25), index=False) if len(law_dis) else "")
        + "\n"
    )


def section_relations(m: pd.DataFrame, rels: pd.DataFrame, edges: pd.DataFrame) -> str:
    d = m.set_index("id")["ngay_ban_hanh_dt"]
    r = rels.assign(d1=rels["doc_id"].map(d), d2=rels["other_doc_id"].map(d)).dropna(
        subset=["d1", "d2"]
    )
    g = r.assign(later=r["d1"] > r["d2"]).groupby("relationship")["later"].agg(["size", "mean"])
    tab = pd.DataFrame(
        {
            "số cạnh": rels["relationship"].value_counts(),
            "% doc_id ban hành sau other_doc_id": (g["mean"] * 100).round(1),
            "loại chuẩn": pd.Series({k: v[0].value for k, v in LABELS.items()}),
            "chiều": pd.Series({k: v[1] for k, v in LABELS.items()}),
        }
    ).sort_values("số cạnh", ascending=False)
    missing_target = (~rels["other_doc_id"].isin(m["id"])).mean()
    out = "## 6. Quan hệ giữa văn bản\n\n"
    out += (
        f"- {len(rels):,} cạnh, {rels['relationship'].nunique()} nhãn. "
        f"{pct(missing_target)} cạnh trỏ tới văn bản không có trong metadata.\n"
        "- Hai bộ nhãn trộn lẫn: nhãn hành động (doc_id tác động lên other) và nhãn vai trò (other "
        "là gì của doc_id). Chiều suy ra từ ngày ban hành rất rõ (gần 0% hoặc gần 100%), nên chuẩn "
        "hoá được về (actor → target) — xem `src/legalrag/ingest/relations.py`.\n"
        f"- Sau chuẩn hoá và bỏ trùng: {len(edges):,} cạnh.\n"
        "- Quan hệ ở mức **văn bản**, không có mức Điều/Khoản (không biết điều nào bị sửa).\n\n"
    )
    out += (
        md(tab)
        + "\n\n### Theo loại chuẩn\n\n"
        + md(edges["rel"].value_counts().rename("số cạnh"))
        + "\n"
    )
    return out


def section_domains(m: pd.DataFrame, edges: pd.DataFrame) -> str:
    out = "## 7. Phạm vi theo lĩnh vực (ước lượng)\n\n"
    out += (
        "Cách chọn: luật gốc theo tên (Luật/Bộ luật/Pháp lệnh) → văn bản hướng dẫn / sửa đổi / thay "
        "thế / hợp nhất (hop 1) → văn bản hướng dẫn / sửa đổi hop 1 (hop 2) + văn bản cũ bị luật gốc "
        "thay thế (pred). Chỉ văn bản trung ương, có tính quy phạm. Xem `src/legalrag/ingest/domains.py`.\n\n"
    )
    rows, details = [], []
    for name, pat in DOMAINS.items():
        s = scope_domain(m, edges, pat)
        st = s["tinh_trang_hieu_luc"]
        rows.append(
            {
                "lĩnh vực": name,
                "tổng": len(s),
                "anchor": int((s["hop"] == "0").sum()),
                "hop1": int((s["hop"] == "1").sum()),
                "hop2": int((s["hop"] == "2").sum()),
                "pred": int((s["hop"] == "pred").sum()),
                "còn HL (kể cả 1 phần)": int(
                    st.isin(["Còn hiệu lực", "Hết hiệu lực một phần"]).sum()
                ),
                "hết HL toàn bộ": int(st.eq("Hết hiệu lực toàn bộ").sum()),
                "Luật": int(s["loai_van_ban"].isin(["Luật", "Bộ luật"]).sum()),
                "NĐ": int(s["loai_van_ban"].eq("Nghị định").sum()),
                "TT/TTLT": int(s["loai_van_ban"].str.startswith("Thông tư").sum()),
                "hợp nhất": int(s["loai_van_ban"].eq("Văn bản hợp nhất").sum()),
                "khác": int(
                    (
                        ~s["loai_van_ban"].isin(
                            [
                                "Luật",
                                "Bộ luật",
                                "Nghị định",
                                "Thông tư",
                                "Thông tư liên tịch",
                                "Văn bản hợp nhất",
                            ]
                        )
                    ).sum()
                ),
            }
        )
        a = find_anchors(m[eligible(m)], pat).sort_values("ngay_ban_hanh_dt")
        details.append(
            f"**{name}** — luật gốc: "
            + "; ".join(
                f"{r.so_ky_hieu} ({r.nam_ban_hanh}, {r.tinh_trang_hieu_luc})"
                for r in a.itertuples()
            )
        )
    out += md(pd.DataFrame(rows), index=False) + "\n\n" + "\n\n".join(details) + "\n"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/vld"))
    ap.add_argument("--out", type=Path, default=Path("reports/data_exploration.md"))
    args = ap.parse_args()

    meta_p = args.data_dir / "data/metadata.parquet"
    rel_p = args.data_dir / "data/relationships.parquet"
    legacy_p = args.data_dir / "legacy/metadata.parquet"
    if not (meta_p.exists() and rel_p.exists() and legacy_p.exists()):
        download(
            ["data/metadata.parquet", "data/relationships.parquet", "legacy/metadata.parquet"],
            args.data_dir,
        )

    m = load_metadata(meta_p)
    rels = pd.read_parquet(rel_p)
    edges = normalize(rels)

    head = (
        "# Khám phá dữ liệu: th1nhng0/vietnamese-legal-documents\n\n"
        "_Sinh tự động bởi `scripts/explore_metadata.py` — không sửa tay._\n\n"
        "## 1. Tổng quan\n\n"
        f"- metadata: {len(m):,} văn bản, {m.shape[1] - 5} cột gốc\n"
        f"- relationships: {len(rels):,} cạnh\n"
        f"- văn bản trung ương có tính quy phạm (`eligible`): {int(eligible(m).sum()):,}\n"
    )
    parts = [
        head,
        section_missing(m),
        section_distributions(m),
        section_duplicates(m),
        section_effect(m, edges),
        section_legacy(m, pd.read_parquet(legacy_p)),
        section_relations(m, rels, edges),
        section_domains(m, edges),
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
