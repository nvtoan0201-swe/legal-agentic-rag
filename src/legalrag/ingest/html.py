"""HTML toàn văn (vbpl.vn) → các dòng văn bản thuần.

Nội dung nằm trong `<table class="detailcontent">`, mỗi đoạn là một `<p>`. Bảng bên trong nội
dung được giữ dưới dạng dòng `| ô | ô |` để parser nhận ra.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

BLOCK_TAGS = ["p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "blockquote"]
_WS = re.compile(r"[ \t ​﻿]+")


def _cell_text(cell: Tag) -> str:
    return _WS.sub(" ", cell.get_text(" ", strip=True))


def html_to_lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    for wrapper in soup.select("table.detailcontent, table#content"):
        cells = wrapper.find_all("td", recursive=True, limit=1)
        if cells:
            cell = cells[0].extract()
            wrapper.replace_with(cell)
            cell.unwrap()
    for tr in soup.find_all("tr"):
        cells = [_cell_text(c) for c in tr.find_all(["td", "th"], recursive=False)]
        tr.replace_with(soup.new_string("\n| " + " | ".join(cells) + " |\n"))
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for tag in soup.find_all(BLOCK_TAGS):
        tag.insert_after("\n")
    lines = (_WS.sub(" ", ln).strip() for ln in soup.get_text().split("\n"))
    return [ln for ln in lines if ln]


def html_to_text(html: str) -> str:
    return "\n".join(html_to_lines(html))
