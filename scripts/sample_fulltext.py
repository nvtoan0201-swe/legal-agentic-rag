"""Lấy mẫu ~20 văn bản toàn văn để xem định dạng, và ước lượng tỉ lệ rỗng / kích thước.

Không tải toàn bộ content.parquet (785 MB): chỉ đọc cột `id` để biết văn bản nằm ở row group nào,
rồi tải các row group chứa văn bản mẫu (~22 MB/row group). Toàn bộ dòng trong các row group này
được dùng làm mẫu để ước lượng tỉ lệ toàn văn rỗng và độ dài.

Kết quả: reports/fulltext_samples.md, data/samples/*.html|*.txt

    uv run python scripts/sample_fulltext.py
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from legalrag.ingest.domains import DOMAINS, eligible, scope_domain
from legalrag.ingest.html import html_to_lines
from legalrag.ingest.metadata import HF_REPO, HF_REVISION, load_metadata
from legalrag.ingest.relations import normalize

CONTENT = f"datasets/{HF_REPO}@{HF_REVISION}/data/content.parquet"

# Văn bản cố định: các luật gốc / văn bản hướng dẫn tiêu biểu của các lĩnh vực ứng viên.
FIXED = [
    "139264",  # 45/2019/QH14 Bộ luật Lao động
    "36870",  # 52/2014/QH13 Luật HN&GĐ
    "142881",  # 59/2020/QH14 Luật Doanh nghiệp
    "170620",  # 36/2024/QH15 Luật TTATGTĐB
    "175027",  # 41/2024/QH15 Luật BHXH
    "187045",  # 109/2025/QH15 Luật Thuế TNCN
    "177815",  # 31/2024/QH15 Luật Đất đai (đã biết là rỗng)
    "152668",  # 145/2020/NĐ-CP hướng dẫn BLLĐ
    "37590",  # 111/2013/TT-BTC hướng dẫn thuế TNCN
    "172779",  # 03/VBHN-VPQH hợp nhất Luật Thuế TNCN
]
# Bổ sung ngẫu nhiên trong phạm vi lĩnh vực, theo loại văn bản (số lượng).
FILL = {
    "Nghị định": 2,
    "Thông tư": 2,
    "Thông tư liên tịch": 1,
    "Nghị quyết": 1,
    "Quyết định": 1,
    "Văn bản hợp nhất": 1,
    "Luật": 1,
}
EMPTY_CHARS = 200

RE = {
    "chuong": re.compile(r"^Chương\s+([IVXLC]+|\d+)\b", re.I),
    "muc": re.compile(r"^Mục\s+\d+", re.I),
    "dieu": re.compile(r"^Điều\s+(\d+)([a-zđ]?)\s*[.:]"),
    "dieu_loose": re.compile(r"^Điều\s+(\d+|thứ)", re.I),
    "khoan": re.compile(r"^(\d+)\.\s"),
    "khoan_alt": re.compile(r"^(\d+)[)/]\s"),
    "diem": re.compile(r"^([a-zđ])\)\s"),
    "diem_alt": re.compile(r"^([a-zđ])\.\s"),
    "gach": re.compile(r"^[-–+•]\s"),
    "table": re.compile(r"^\|"),
    "phu_luc": re.compile(r"^(PHỤ LỤC|Phụ lục)\b"),
    "quoted": re.compile(r"^[“\"]"),
}


def text_len(html: str | None) -> int:
    if not html:
        return 0
    return sum(len(x) for x in html_to_lines(html))


def analyze(lines: list[str]) -> dict:
    c = {k: 0 for k in RE}
    dieu_nums: list[int] = []
    khoan_in_dieu: list[int] = []
    for ln in lines:
        for k, rx in RE.items():
            if rx.match(ln):
                c[k] += 1
        if m := RE["dieu"].match(ln):
            dieu_nums.append(int(m.group(1)))
            khoan_in_dieu.append(0)
        elif RE["khoan"].match(ln) and khoan_in_dieu:
            khoan_in_dieu[-1] += 1
    seq = all(b == a + 1 or b == a for a, b in zip(dieu_nums, dieu_nums[1:], strict=False))
    head = " ".join(lines[:8])
    return {
        "dòng": len(lines),
        "ký tự": sum(map(len, lines)),
        "chương": c["chuong"],
        "mục": c["muc"],
        "điều": c["dieu"],
        "điều (lỏng)": c["dieu_loose"],
        "điều tăng dần": "✓" if seq else "✗",
        "điều không khoản": sum(1 for k in khoan_in_dieu if k == 0),
        "khoản": c["khoan"],
        "khoản kiểu 1)": c["khoan_alt"],
        "điểm a)": c["diem"],
        "điểm a.": c["diem_alt"],
        "gạch đầu dòng": c["gach"],
        "dòng bảng": c["table"],
        "phụ lục": c["phu_luc"],
        "dòng trích dẫn “": c["quoted"],
        "có quốc hiệu": "✓" if "CỘNG HÒA XÃ HỘI CHỦ NGHĨA" in head.upper() else "",
    }


def build_rowgroup_index(fs, path: str, cache: Path) -> dict[str, int]:
    if cache.exists():
        return json.loads(cache.read_text())
    pf = pq.ParquetFile(fs.open(path))
    idx = {}
    for i in range(pf.num_row_groups):
        for x in pf.read_row_group(i, columns=["id"]).column(0).to_pylist():
            idx[x] = i
    cache.write_text(json.dumps(idx))
    return idx


def load_rowgroups(fs, groups: list[int], cache_dir: Path) -> pd.DataFrame:
    pf = None
    parts = []
    for g in groups:
        p = cache_dir / f"content_rg{g:02d}.parquet"
        if not p.exists():
            pf = pf or pq.ParquetFile(fs.open(CONTENT))
            pq.write_table(pf.read_row_group(g, columns=["id", "content_html"]), p)
        parts.append(pd.read_parquet(p).assign(rg=g))
    return pd.concat(parts, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, default=Path("reports/fulltext_samples.md"))
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()

    from huggingface_hub import HfFileSystem

    fs = HfFileSystem()
    raw = args.data_dir / "raw/vld"
    cache = args.data_dir / "cache"
    samples_dir = args.data_dir / "samples"
    cache.mkdir(parents=True, exist_ok=True)
    samples_dir.mkdir(parents=True, exist_ok=True)

    meta = load_metadata(raw / "data/metadata.parquet")
    edges = normalize(pd.read_parquet(raw / "data/relationships.parquet"))
    scope = pd.concat(
        [scope_domain(meta, edges, names).assign(domain=d) for d, names in DOMAINS.items()]
    )
    domains_of = scope.groupby("id")["domain"].agg(lambda s: ",".join(sorted(set(s))))

    idx = build_rowgroup_index(fs, CONTENT, cache / "content_rowgroups.json")
    groups = sorted({idx[i] for i in FIXED if i in idx})
    content = load_rowgroups(fs, groups, cache)
    cols = ["id", "so_ky_hieu", "loai_van_ban", "nam_ban_hanh", "tinh_trang_hieu_luc", "title"]
    df = content.merge(meta[cols + ["pham_vi"]], on="id", how="left")
    df["eligible"] = df["id"].isin(meta.loc[eligible(meta), "id"])
    df["domains"] = df["id"].map(domains_of)
    df["ký tự"] = df["content_html"].map(text_len)
    df["rỗng"] = df["ký tự"] < EMPTY_CHARS
    frac = len(content) / len(idx)

    # ---- chọn mẫu
    rng_df = df[df["domains"].notna() & ~df["rỗng"] & ~df["id"].isin(FIXED)]
    picks = list(FIXED)
    for loai, n in FILL.items():
        pool = rng_df[rng_df["loai_van_ban"] == loai]
        picks += pool.sample(min(n, len(pool)), random_state=args.seed)["id"].tolist()
    old = rng_df[rng_df["nam_ban_hanh"] < 2000]
    picks += old.sample(min(1, len(old)), random_state=args.seed)["id"].tolist()
    sample = df.set_index("id").loc[picks].reset_index()

    rows = []
    for r in sample.itertuples():
        lines = html_to_lines(r.content_html or "")
        (samples_dir / f"{r.id}.html").write_text(r.content_html or "", encoding="utf-8")
        (samples_dir / f"{r.id}.txt").write_text("\n".join(lines), encoding="utf-8")
        rows.append(
            {
                "id": r.id,
                "số hiệu": r.so_ky_hieu,
                "loại": r.loai_van_ban,
                "năm": r.nam_ban_hanh,
                "lĩnh vực": r.domains,
            }
            | analyze(lines)
        )
    sample_tab = pd.DataFrame(rows)

    # ---- thống kê trên toàn bộ dòng của các row group đã tải
    by_type = (
        df.groupby("loai_van_ban")
        .agg(
            n=("id", "size"),
            rỗng=("rỗng", "mean"),
            median_ký_tự=("ký tự", lambda s: s[s >= EMPTY_CHARS].median()),
        )
        .sort_values("n", ascending=False)
        .head(15)
    )
    by_type["rỗng"] = (by_type["rỗng"] * 100).round(1).astype(str) + "%"
    df["giai đoạn"] = pd.cut(
        df["nam_ban_hanh"].astype(float),
        [0, 1999, 2009, 2019, 2022, 2024, 2030],
        labels=["<2000", "2000–09", "2010–19", "2020–22", "2023–24", "2025–26"],
    )
    by_period = df[df["eligible"]].groupby("giai đoạn", observed=True)["rỗng"].agg(["size", "mean"])
    by_period["mean"] = (by_period["mean"] * 100).round(1).astype(str) + "%"

    # rỗng nhưng có bản trùng số hiệu (khác id) có nội dung
    el = df[df["eligible"]]
    filled = el[~el["rỗng"]].groupby(["so_ky_hieu", "loai_van_ban"]).size()
    empties = el[el["rỗng"]]
    rescued = empties.set_index(["so_ky_hieu", "loai_van_ban"]).index.isin(filled.index).mean()

    # ước lượng kích thước theo lĩnh vực
    med = df[~df["rỗng"]].groupby("loai_van_ban")["ký tự"].median()
    emp = df[df["eligible"]].groupby("loai_van_ban")["rỗng"].mean()
    dom_rows = []
    for d in DOMAINS:
        s = scope[scope["domain"] == d]
        seen = df[df["domains"].fillna("").str.contains(rf"\b{d}\b")]
        est_chars = sum(
            med.get(t, med.median()) * (1 - emp.get(t, 0.25)) for t in s["loai_van_ban"]
        )
        dom_rows.append(
            {
                "lĩnh vực": d,
                "số văn bản": len(s),
                "trong mẫu row group": len(seen),
                "% rỗng (mẫu)": f"{100 * seen['rỗng'].mean():.0f}%" if len(seen) else "—",
                "ước lượng văn bản có toàn văn": round(
                    sum(1 - emp.get(t, 0.25) for t in s["loai_van_ban"])
                ),
                "ước lượng MB text": round(
                    est_chars * 1.3 / 1e6, 1
                ),  # UTF-8 tiếng Việt ~1.3 B/ký tự
            }
        )
    dom_tab = pd.DataFrame(dom_rows)

    excerpt_ids = [i for i in ["139264", "152668", "37590"] if i in set(sample["id"])]
    excerpts = []
    for i in excerpt_ids:
        lines = (samples_dir / f"{i}.txt").read_text(encoding="utf-8").split("\n")
        start = next((k for k, ln in enumerate(lines) if RE["dieu"].match(ln)), 0)
        body = "\n".join(ln[:160] for ln in lines[max(0, start - 3) : start + 22])
        excerpts.append(f"**{i}** (từ dòng {start}):\n\n```text\n{body}\n```")
    tables = sample_tab[sample_tab["dòng bảng"] > 0]["id"].tolist()[:1]
    for i in tables:
        lines = (samples_dir / f"{i}.txt").read_text(encoding="utf-8").split("\n")
        k = next(k for k, ln in enumerate(lines) if ln.startswith("|"))
        body = "\n".join(ln[:160] for ln in lines[max(0, k - 2) : k + 8])
        excerpts.append(f"**{i}** — bảng:\n\n```text\n{body}\n```")

    report = f"""# Mẫu toàn văn: th1nhng0/vietnamese-legal-documents (config `content`)

_Sinh tự động bởi `scripts/sample_fulltext.py` — không sửa tay._

Đã tải {len(groups)}/35 row group ({len(content):,} văn bản, {100 * frac:.0f}% corpus) chứa các văn bản
mẫu cố định. Thống kê rỗng/độ dài dưới đây tính trên toàn bộ các dòng đó. "Rỗng" = text sau khi bỏ
HTML < {EMPTY_CHARS} ký tự.

## 1. Định dạng

- Cột `content_html`: HTML thô của vbpl.vn, không phải markdown. Nội dung bọc trong
  `<table class="detailcontent">`, mỗi đoạn là một `<p>`, tiêu đề Điều/Chương in `<strong>`.
- Chuyển sang dòng văn bản bằng `legalrag.ingest.html.html_to_lines` (bảng → `| ô | ô |`).

## 2. {len(sample_tab)} văn bản mẫu

{sample_tab.to_markdown(index=False)}

Chú thích cột: `điều` = dòng khớp `^Điều N.`; `điều (lỏng)` = mọi dòng bắt đầu bằng "Điều N/thứ" (kể
cả `Điều 5:`); `điều không khoản` = điều không có dòng `^N. `; `dòng trích dẫn “` = dòng mở ngoặc
kép, thường là nội dung sửa đổi được trích lại trong văn bản sửa đổi/hợp nhất.

## 3. Trích đoạn

{chr(10).join(excerpts)}

## 4. Tỉ lệ toàn văn rỗng (trên {len(content):,} văn bản đã tải)

Tổng: {100 * df["rỗng"].mean():.1f}% rỗng; văn bản trung ương có tính quy phạm:
{100 * df.loc[df["eligible"], "rỗng"].mean():.1f}%.

### Theo loại

{by_type.to_markdown()}

### Theo giai đoạn ban hành (văn bản trung ương có tính quy phạm)

{by_period.rename(columns={"size": "n", "mean": "rỗng"}).to_markdown()}

Trong số văn bản rỗng (trung ương, quy phạm), {100 * rescued:.0f}% có một bản ghi khác cùng số hiệu
và loại, có nội dung, trong cùng mẫu (vd 59/2020/QH14: id 142847 rỗng, id 142881 đủ).

## 5. Ước lượng theo lĩnh vực

Ước lượng = Σ (1 − tỉ lệ rỗng theo loại) × trung vị ký tự theo loại. Thô, chỉ để so sánh lĩnh vực.

{dom_tab.to_markdown(index=False)}

## 6. Bản crawl cũ (`legacy_content`)

`legacy/content.parquet` (plain text, 3,5 GB) chỉ có một row group, nên không đọc từng phần được.
Muốn dùng làm nguồn dự phòng cho văn bản rỗng thì phải tải trọn file; id của bản cũ khác hệ id
hiện tại, phải ghép theo số hiệu + loại + ngày ban hành.
"""
    args.out.write_text(report, encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
