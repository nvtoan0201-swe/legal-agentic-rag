import pandas as pd

from legalrag.ingest.corpus import assign_keys, dedupe


def frame(rows):
    df = pd.DataFrame(rows, columns=["id", "so_ky_hieu", "loai_van_ban", "ngay_ban_hanh"])
    df["ngay_ban_hanh_dt"] = pd.to_datetime(df["ngay_ban_hanh"], format="%d/%m/%Y")
    df["domains"] = [["a"]] * len(df)
    return df


def test_dedupe_prefers_row_with_text():
    df = frame(
        [("1", "59/2020/QH14", "Luật", "17/06/2020"), ("2", "59/2020/QH14", "Luật", "17/06/2020")]
    )
    kept, alias = dedupe(df, has_text={"2"})
    assert kept["id"].tolist() == ["2"]
    assert alias == {"1": "2"}


def test_keys_are_disambiguated_only_when_needed():
    df = frame(
        [
            ("1", "45/2019/QH14", "Bộ luật", "20/11/2019"),
            ("2", "Không số", "Luật", "23/06/1994"),
            ("3", "01/CT", "Chỉ thị", "01/01/1990"),
            ("4", "01/CT", "Chỉ thị", "05/05/1995"),
        ]
    )
    assert assign_keys(df).tolist() == [
        "45/2019/QH14",
        "KS@1994-06-23",
        "01/CT@1990-01-01",
        "01/CT@1995-05-05",
    ]
