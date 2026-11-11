from legalrag.ingest.html import html_to_lines

HTML = """<table class="detailcontent" id="content"><tr><td><div align="justify">
<p align="center"><strong>LUẬT</strong></p>
<p><strong>Điều 1. Phạm vi</strong></p>
<p>\t1. Khoản một;<br>a) điểm a</p>
<table><tr><td>STT</td><td>Tên</td></tr><tr><td>1</td><td>Mức&nbsp;phạt</td></tr></table>
<p> </p>
</div></td></tr></table>"""


def test_html_to_lines():
    assert html_to_lines(HTML) == [
        "LUẬT",
        "Điều 1. Phạm vi",
        "1. Khoản một;",
        "a) điểm a",
        "| STT | Tên |",
        "| 1 | Mức phạt |",
    ]


def test_empty_shell():
    shell = '<table class="detailcontent" id="content"><tr><td><div> </div></td></tr></table>'
    assert html_to_lines(shell) == []
