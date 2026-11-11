from legalrag.ingest.parser import parse, roman_to_int


def ids(doc):
    return [u.unit_id.split("#", 1)[1] for u in doc.units]


def by_id(doc, local):
    return next(u for u in doc.units if u.unit_id.endswith("#" + local))


def test_basic_hierarchy():
    lines = [
        "| QUỐC HỘI | CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM |",
        "LUẬT",
        "Căn cứ Hiến pháp;",
        "Chương I",
        "NHỮNG QUY ĐỊNH CHUNG",
        "Mục 1. HỢP ĐỒNG",
        "Điều 1. Phạm vi điều chỉnh",
        "Luật này quy định về lao động.",
        "Điều 2. Đối tượng áp dụng",
        "1. Người lao động.",
        "2. Người sử dụng lao động gồm:",
        "a) Doanh nghiệp;",
        "b) Hộ gia đình;",
        "đ) không đúng thứ tự nên là nội dung",
        "c) Cá nhân.",
        "d) Tổ chức khác.",
        "đ) Hợp tác xã.",
    ]
    doc = parse(lines, "X")
    assert ids(doc) == [
        "d1",
        "d2",
        "d2-k1",
        "d2-k2",
        "d2-k2-a",
        "d2-k2-b",
        "d2-k2-c",
        "d2-k2-d",
        "d2-k2-dd",
    ]
    d1 = by_id(doc, "d1")
    assert d1.title == "Phạm vi điều chỉnh"
    assert d1.chuong == "Chương I. NHỮNG QUY ĐỊNH CHUNG"
    assert d1.muc == "Mục 1. HỢP ĐỒNG"
    assert by_id(doc, "d2-k2-b").lines[-1] == "đ) không đúng thứ tự nên là nội dung"
    assert by_id(doc, "d2-k2-a").parent_id == "X#d2-k2"
    assert doc.preamble[-1] == "Căn cứ Hiến pháp;"
    assert doc.clean


def test_article_without_khoan_and_diem_directly_under_article():
    doc = parse(["Điều 1. Áp dụng", "Văn bản áp dụng cho:", "a) Cơ quan;", "b) Tổ chức."], "X")
    assert ids(doc) == ["d1", "d1-a", "d1-b"]
    assert by_id(doc, "d1").text == "Điều 1. Áp dụng\nVăn bản áp dụng cho:"


def test_typo_and_colon_and_inserted_article():
    lines = [
        "Điều 1: Tên",
        "nội dung",
        "Điêu 2. Có lỗi dấu",
        "x",
        "Điều 2a. Bổ sung",
        "y",
        "Điều 3",
        "Tiêu đề ở dòng sau",
    ]
    assert ids(parse(lines, "X")) == ["d1", "d2", "d2a", "d3"]


def test_prose_reference_is_not_an_article():
    lines = ["Điều 1. Tên", "Điều 5 của Luật này quy định như sau.", "Điều 2. Tên"]
    doc = parse(lines, "X")
    assert ids(doc) == ["d1", "d2"]
    assert doc.issues == {}


def test_amending_law_quotes_are_body_text():
    lines = [
        "Điều 1. Sửa đổi, bổ sung một số điều của Luật X",
        "1. Sửa đổi, bổ sung Điều 4 như sau:",
        "“Điều 4. Nội dung mới",
        "1. Khoản một mới.",
        "2. Khoản hai mới.”.",
        "2. Bổ sung Điều 2 như sau:",
        '"Điều 2. Định nghĩa',
        'a) mục a."',
        "Điều 2. Hiệu lực thi hành",
        "Luật này có hiệu lực từ ngày 01/01/2026.",
    ]
    doc = parse(lines, "X")
    assert ids(doc) == ["d1", "d1-k1", "d1-k2", "d2"]
    assert "“Điều 4. Nội dung mới" in by_id(doc, "d1-k1").lines
    assert doc.clean


def test_missing_opening_quote_is_rejected_by_numbering():
    lines = [
        "Điều 1. Sửa đổi Luật X",
        "1. Sửa đổi Điều 55 như sau:",
        "Điều 55. Nhiệm vụ",
        "nội dung",
        "Điều 2. Hiệu lực thi hành",
        "...",
    ]
    doc = parse(lines, "X")
    assert ids(doc) == ["d1", "d1-k1", "d2"]
    assert doc.issues["rejected_article"] == 1
    assert not doc.clean  # flagged for review


def test_unclosed_quote_recovers_at_own_article():
    lines = [
        "Điều 1. Sửa đổi Luật X",
        "“Điều 7. Nội dung",
        "không đóng ngoặc",
        "Điều 2. Hiệu lực thi hành",
        "...",
    ]
    doc = parse(lines, "X")
    assert ids(doc) == ["d1", "d2"]
    assert doc.issues["unclosed_quote_recovered"] == 1


def test_appendix_forms_do_not_create_articles():
    lines = [
        "Điều 1. Tên",
        "nội dung",
        "Điều 2. Hiệu lực",
        "...",
        "| Nơi nhận: - Như Điều 2; | TM. CHÍNH PHỦ THỦ TƯỚNG |",
        "Phụ lục I",
        "MẪU QUYẾT ĐỊNH",
        "Điều 1. Thu hồi giấy phép ...",
        "Mẫu số 02/PLI",
        "Điều 1. Trích tiền ký quỹ ...",
        "PHỤ LỤC II",
        "| STT | Nghề |",
        "| 1 | Khai thác mỏ |",
    ]
    doc = parse(lines, "X")
    assert ids(doc) == ["d1", "d2", "pl1", "pl2"]
    assert "Điều 1. Trích tiền ký quỹ ..." in by_id(doc, "pl1").lines
    assert "| 1 | Khai thác mỏ |" in by_id(doc, "pl2").lines
    assert doc.clean


def test_attached_regulation_after_signature():
    lines = [
        "QUYẾT ĐỊNH:",
        "Điều 1. Ban hành kèm theo Quyết định này Quy chế.",
        "Điều 2. Hiệu lực.",
        "| | BỘ TRƯỞNG Nguyễn Văn A |",
        "QUY CHẾ",
        "(Ban hành kèm theo Quyết định số 1/2020/QĐ-BXX)",
        "Chương I",
        "QUY ĐỊNH CHUNG",
        "Điều 1. Phạm vi",
        "1. Khoản.",
    ]
    doc = parse(lines, "X")
    assert ids(doc) == ["d1", "d2", "kt1", "kt1-d1", "kt1-d1-k1"]
    assert by_id(doc, "kt1").lines == ["QUY CHẾ", "(Ban hành kèm theo Quyết định số 1/2020/QĐ-BXX)"]


def test_attachment_without_articles_is_kept():
    lines = [
        "Điều 1. Ban hành kèm theo Thông tư này Quy định.",
        "Điều 2. Hiệu lực.",
        "| Nơi nhận: - Như trên; | KT. BỘ TRƯỞNG |",
        "QUY ĐỊNH",
        "I. PHẠM VI",
        "1. Nội dung quan trọng.",
    ]
    doc = parse(lines, "X")
    assert ids(doc) == ["d1", "d2", "kt1"]
    assert by_id(doc, "kt1").lines == ["QUY ĐỊNH", "I. PHẠM VI", "1. Nội dung quan trọng."]


def test_tables_stay_inside_their_unit():
    lines = [
        "Điều 1. Mức phạt",
        "1. Phạt tiền theo bảng:",
        "| Hành vi | Mức |",
        "| A | 1 triệu |",
        "2. Khoản hai.",
    ]
    doc = parse(lines, "X")
    assert by_id(doc, "d1-k1").lines[1:] == ["| Hành vi | Mức |", "| A | 1 triệu |"]


def test_nested_sub_points_attach_to_point():
    lines = [
        "Điều 1. Cư trú",
        "1. Cá nhân cư trú:",
        "b) Có nơi ở:",
        "a) sai thứ tự",
        "b.1) Nơi ở thường xuyên;",
        "b.1.1) Công dân Việt Nam;",
    ]
    doc = parse(lines, "X")
    # "b)" without a preceding "a)" is still accepted? No: numbering must start at a.
    assert ids(doc) == ["d1", "d1-k1", "d1-k1-a"]
    assert by_id(doc, "d1-k1-a").lines[-1] == "b.1.1) Công dân Việt Nam;"


def test_document_without_articles_becomes_body_unit():
    doc = parse(["NGHỊ QUYẾT", "Phê duyệt quy hoạch.", "| Chỉ tiêu | Diện tích |"], "X")
    assert ids(doc) == ["body"]
    assert doc.issues["no_articles"] == 1
    assert not doc.clean


def test_gap_of_one_is_flagged_not_dropped():
    doc = parse(["Điều 1. A", "x", "Điều 3. C", "y"], "X")
    assert ids(doc) == ["d1", "d3"]
    assert doc.issues["article_gap"] == 1


def test_legacy_style_chapter():
    doc = parse(["Chương 1:", "NHỮNG QUY ĐỊNH CHUNG", "Điều 1. Phạm vi", "x"], "X")
    assert by_id(doc, "d1").chuong == "Chương 1. NHỮNG QUY ĐỊNH CHUNG"


def test_roman():
    assert [roman_to_int(x) for x in ["I", "IV", "IX", "XIV", "XL", "12"]] == [1, 4, 9, 14, 40, 12]
