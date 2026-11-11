"""Đọc và chuẩn hoá metadata của dataset th1nhng0/vietnamese-legal-documents."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

HF_REPO = "th1nhng0/vietnamese-legal-documents"
# Ghim revision để thống kê / ingest tái lập được.
HF_REVISION = "8977887f17be2defae4c5171d55562e1cde7d695"
# Ngày dataset được làm mới lần cuối (theo dataset card); tình trạng hiệu lực tính tới ngày này.
SNAPSHOT_DATE = pd.Timestamp("2026-07-23")

DATE_COLUMNS = ["ngay_ban_hanh", "ngay_co_hieu_luc", "ngay_het_hieu_luc", "ngay_dang_cong_bao"]
# Giá trị giữ chỗ coi như thiếu dữ liệu.
PLACEHOLDERS = {"", "Chưa phân loại", "Chưa xác định", "None", "nan"}

IN_FORCE_STATUSES = {"Còn hiệu lực", "Hết hiệu lực một phần", "Ngưng hiệu lực một phần"}


def download(files: list[str], local_dir: Path) -> list[Path]:
    from huggingface_hub import hf_hub_download

    return [
        Path(
            hf_hub_download(
                HF_REPO, f, repo_type="dataset", revision=HF_REVISION, local_dir=local_dir
            )
        )
        for f in files
    ]


def parse_date(s: pd.Series) -> pd.Series:
    """Ngày dạng DD/MM/YYYY → Timestamp; sai định dạng → NaT."""
    return pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")


def is_missing(s: pd.Series) -> pd.Series:
    return s.isna() | s.astype(str).str.strip().isin(PLACEHOLDERS)


def load_metadata(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    for col in DATE_COLUMNS:
        df[f"{col}_dt"] = parse_date(df[col])
    df["nam_ban_hanh"] = df["ngay_ban_hanh_dt"].dt.year.astype("Int64")
    return df
