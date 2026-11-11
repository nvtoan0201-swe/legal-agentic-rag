import pytest

from legalrag.ingest.domains import DOMAINS, anchor_regex


@pytest.mark.parametrize(
    ("domain", "title", "expected"),
    [
        ("lao_dong", "Bộ Luật lao động số 45/2019/QH14", True),
        ("lao_dong", "Luật An toàn, vệ sinh lao động số 84/2015/QH13", False),
        ("dat_dai", "Đất đai", True),
        ("dat_dai", "Luật Sửa đổi, bổ sung một số điều của Luật Đất đai số 10/1998/QH10", True),
        ("doanh_nghiep", "doanh nghiệp", True),
        ("doanh_nghiep", "Luật Thuế thu nhập doanh nghiệp số 14/2008/QH12", False),
        ("doanh_nghiep", "Luật Hỗ trợ doanh nghiệp nhỏ và vừa số 04/2017/QH14", False),
        ("giao_thong_duong_bo", "Trật tự, an toàn giao thông đường bộ", True),
        ("thue_tncn", "Luật sửa đổi... của Luật Thuế thu nhập cá nhân, Luật Thuế GTGT", True),
    ],
)
def test_anchor_regex(domain, title, expected):
    assert bool(anchor_regex(DOMAINS[domain]).search(title)) is expected


def test_omnibus_amendments_are_not_anchors():
    import pandas as pd

    from legalrag.ingest.domains import find_anchors

    meta = pd.DataFrame(
        {
            "title": [
                "Luật Doanh nghiệp số 59/2020/QH14",
                "Luật sửa đổi, bổ sung một số điều của Luật Đầu tư, Luật Doanh nghiệp",
                "Luật Sửa đổi, bổ sung một số điều của Luật Doanh nghiệp số 37/2013/QH13",
                "Văn bản hợp nhất số 03/VBHN-VPQH Luật Doanh nghiệp",
                "Văn bản hợp nhất số 1/VBHN-BTC Thông tư hướng dẫn Luật Doanh nghiệp",
            ],
            "loai_van_ban": ["Luật", "Luật", "Luật", "Văn bản hợp nhất", "Văn bản hợp nhất"],
        }
    )
    got = find_anchors(meta, DOMAINS["doanh_nghiep"]).index.tolist()
    assert got == [0, 2, 3]
