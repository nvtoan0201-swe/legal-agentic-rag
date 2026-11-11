"""Split a legal document (list of text lines) into Chương → Mục → Điều → Khoản → Điểm units.

Numbering must be sequential: an out-of-order "Điều N" / "N." / "a)" line is treated as body text,
which is how quoted articles inside amending documents are kept out of the structure. Lines
inside “...” quotes are always body text.

Unit ids: "{doc_key}#d35-k2-a", "{doc_key}#pl1" (appendix), "{doc_key}#kt1" (text attached
after the signature block), "{doc_key}#kt1-d3" (article of that attachment), "{doc_key}#body"
(document with no articles).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
DIEM_LETTERS = "abcdđeghiklmnopqrstuvxy"  # Vietnamese order, no f/j/w/z

RE_CHUONG = re.compile(r"^Ch[uư][oơ]ng\s+([IVXLC]+|\d+)\b\s*[.:\-–]?\s*(.*)$")
RE_MUC = re.compile(r"^Mục\s+(\d+|[IVXLC]+)\b\s*[.:\-–]?\s*(.*)$")
# Tolerates diacritic typos seen in the source ("Điêu 38").
RE_DIEU = re.compile(r"^Đi[eêềếểễệ]u\s+(\d+)([a-zđ]?)\s*(?:[.:\-–]\s*(.*)|$)")
RE_KHOAN = re.compile(r"^(\d+)\.\s+(\S.*)$")
RE_DIEM = re.compile(r"^([a-zđ])[).]\s+(\S.*)$")
RE_APPENDIX = re.compile(r"^(?:PHỤ LỤC|Phụ lục|Mẫu số|MẪU SỐ)\b\s*([IVXLC]+|\d+)?")
RE_END = re.compile(
    r"^(?:\|\s*)?Nơi nhận\b|^(?:Luật|Bộ luật|Pháp lệnh|Nghị quyết) này (?:đã )?được Quốc hội"
)
RE_SIGNATURE = re.compile(
    r"^\|.*\b(?:TM\.|KT\.|Q\.|CHỦ TỊCH|BỘ TRƯỞNG|THỦ TƯỚNG|CHÁNH ÁN|VIỆN TRƯỞNG|TỔNG KIỂM TOÁN)"
)
# Titles of an amending document's own articles (used to close a quote that was never closed).
RE_OWN_TITLE = re.compile(
    r"hiệu lực|thi hành|sửa đổi|bổ sung|bãi bỏ|chuyển tiếp|tổ chức thực hiện|trách nhiệm",
    re.IGNORECASE,
)


def roman_to_int(s: str) -> int:
    if s.isdigit():
        return int(s)
    total = 0
    for a, b in zip(s, s[1:] + " ", strict=True):
        v = ROMAN[a]
        total += -v if b != " " and ROMAN[b] > v else v
    return total


@dataclass
class Unit:
    unit_id: str
    kind: str  # dieu | khoan | diem | phu_luc | dinh_kem | body
    number: str
    parent_id: str | None
    ordinal: int
    title: str = ""
    lines: list[str] = field(default_factory=list)
    chuong: str = ""
    muc: str = ""

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


@dataclass
class ParsedDoc:
    units: list[Unit]
    preamble: list[str]
    issues: dict[str, int]
    body_chars: int
    dropped_chars: int

    @property
    def articles(self) -> list[Unit]:
        return [u for u in self.units if u.kind == "dieu"]

    @property
    def clean(self) -> bool:
        return bool(self.articles) and not any(
            self.issues.get(k)
            for k in (
                "article_gap",
                "first_article_not_1",
                "empty_article",
                "rejected_article",
                "unbalanced_quote",
                "duplicate_id",
            )
        )


def _quote_delta(line: str, depth: int) -> int:
    depth += line.count("“") - line.count("”")
    if line.count('"') % 2:
        depth = 0 if depth > 0 else 1
    return max(0, min(depth, 1))


class _Parser:
    def __init__(self, doc_key: str):
        self.key = doc_key
        self.units: list[Unit] = []
        self.preamble: list[str] = []
        self.issues: dict[str, int] = {}
        self.ids: set[str] = set()
        self.mode = "preamble"  # preamble | body | appendix | end
        self.part = 0
        self.chuong = self.muc = ""
        self.pending_title: str | None = None  # "chuong" / "muc" waiting for a title line
        self.dieu: Unit | None = None
        self.khoan: Unit | None = None
        self.diem: Unit | None = None
        self.appendix: Unit | None = None
        self.attachment: Unit | None = None
        self.last_dieu: tuple[int, str] | None = None
        self.last_khoan = 0
        self.last_diem = -1
        self.quote = 0
        self.body_chars = 0
        self.dropped_chars = 0  # signature / recipient lines, intentionally discarded

    def issue(self, name: str) -> None:
        self.issues[name] = self.issues.get(name, 0) + 1

    def add(self, kind: str, local: str, number: str, parent: Unit | None, title="") -> Unit:
        uid = f"{self.key}#{local}"
        if uid in self.ids:
            self.issue("duplicate_id")
            n = 2
            while f"{uid}_{n}" in self.ids:
                n += 1
            uid = f"{uid}_{n}"
        self.ids.add(uid)
        u = Unit(
            uid,
            kind,
            number,
            parent.unit_id if parent else None,
            len(self.units),
            title,
            chuong=self.chuong,
            muc=self.muc,
        )
        self.units.append(u)
        return u

    def prefix(self) -> str:
        return f"kt{self.part}-" if self.part else ""

    # -- structural checks -------------------------------------------------------------
    def accept_dieu(self, num: int, suffix: str, title: str) -> bool:
        if self.last_dieu is None:
            if num != 1:
                self.issue("first_article_not_1")
            return True
        last, last_suffix = self.last_dieu
        if num == last and suffix > last_suffix:
            return True  # inserted article, e.g. 49a after 49
        if num == last + 1:
            return True
        if num == last + 2 and self.quote == 0:
            self.issue("article_gap")
            return True
        return False

    def attach(self, line: str) -> None:
        """Text after the signature block (attached regulation, list, ...) that has no articles."""
        if RE_SIGNATURE.match(line) or RE_END.match(line):
            self.dropped_chars += len(line)
            return
        if self.attachment is None:
            self.attachment = self.add("dinh_kem", f"kt{self.part + 1}", str(self.part + 1), None)
        self.attachment.lines.append(line)

    def start_part(self) -> None:
        self.attachment = None
        self.part += 1
        self.last_dieu = None
        self.chuong = self.muc = ""
        self.dieu = self.khoan = self.diem = self.appendix = None
        self.mode = "body"

    def feed(self, line: str) -> None:
        self.body_chars += len(line)

        if self.quote:
            self.quote = _quote_delta(line, self.quote)
            m = RE_DIEU.match(line)
            # Recover from a quote that was never closed: next own article of the document.
            if not (
                m
                and self.last_dieu
                and int(m.group(1)) == self.last_dieu[0] + 1
                and RE_OWN_TITLE.search(m.group(3) or "")
            ):
                self.append(line)
                return
            self.quote = 0
            self.issue("unclosed_quote_recovered")

        if line.startswith(("“", '"')):
            self.quote = _quote_delta(line, 0)
            self.append(line)
            return

        if self.mode in ("body", "preamble") and (
            RE_END.match(line) or (self.last_dieu and RE_SIGNATURE.match(line))
        ):
            self.mode = "end"
            self.dropped_chars += len(line)
            return

        if RE_APPENDIX.match(line) and len(line) <= 160 and (self.last_dieu or self.mode == "end"):
            m = RE_APPENDIX.match(line)
            if line.upper().startswith("PHỤ LỤC") or self.appendix is None:
                n = (
                    str(roman_to_int(m.group(1)))
                    if m.group(1)
                    else str(sum(u.kind == "phu_luc" for u in self.units) + 1)
                )
                self.appendix = self.add("phu_luc", f"pl{n}", n, None, title=line)
                self.mode = "appendix"
            self.appendix.lines.append(line)
            return

        if self.mode == "appendix":
            self.appendix.lines.append(line)
            return

        if self.mode == "end":
            if RE_CHUONG.match(line) or ((m := RE_DIEU.match(line)) and m.group(1) == "1"):
                self.start_part()
            else:
                self.attach(line)
                return

        if m := RE_CHUONG.match(line):
            self.mode = "body"
            self.chuong = f"Chương {m.group(1)}" + (f". {m.group(2)}" if m.group(2) else "")
            self.muc = ""
            self.pending_title = None if m.group(2) else "chuong"
            self.close_dieu()
            return
        if (m := RE_MUC.match(line)) and self.mode == "body":
            self.muc = f"Mục {m.group(1)}" + (f". {m.group(2)}" if m.group(2) else "")
            self.pending_title = None if m.group(2) else "muc"
            self.close_dieu()
            return
        if self.pending_title and self.dieu is None and not RE_DIEU.match(line):
            if self.pending_title == "chuong":
                self.chuong += f". {line}"
            else:
                self.muc += f". {line}"
            self.pending_title = None
            return
        self.pending_title = None

        if m := RE_DIEU.match(line):
            num, suffix, title = int(m.group(1)), m.group(2), (m.group(3) or "").strip()
            if self.accept_dieu(num, suffix, title):
                self.mode = "body"
                self.close_dieu()
                self.dieu = self.add(
                    "dieu", f"{self.prefix()}d{num}{suffix}", f"{num}{suffix}", None, title
                )
                self.dieu.lines.append(line)
                self.last_dieu = (num, suffix)
                return
            self.issue("rejected_article")

        if self.dieu is not None:
            if (m := RE_KHOAN.match(line)) and int(m.group(1)) == self.last_khoan + 1:
                self.last_khoan += 1
                self.khoan = self.add(
                    "khoan", f"{self.dieu_local()}-k{m.group(1)}", m.group(1), self.dieu
                )
                self.khoan.lines.append(line)
                self.diem, self.last_diem = None, -1
                return
            m = RE_DIEM.match(line)
            nxt = DIEM_LETTERS[self.last_diem + 1] if self.last_diem + 1 < len(DIEM_LETTERS) else ""
            if m and m.group(1) == nxt:
                self.last_diem += 1
                parent = self.khoan or self.dieu
                letter = "dd" if nxt == "đ" else nxt
                local = parent.unit_id.split("#", 1)[1]
                self.diem = self.add("diem", f"{local}-{letter}", nxt, parent)
                self.diem.lines.append(line)
                return

        self.append(line)

    def dieu_local(self) -> str:
        return self.dieu.unit_id.split("#", 1)[1]

    def close_dieu(self) -> None:
        self.dieu = self.khoan = self.diem = None
        self.last_khoan, self.last_diem = 0, -1

    def append(self, line: str) -> None:
        target = self.diem or self.khoan or self.dieu
        if target is not None:
            target.lines.append(line)
        elif self.mode == "appendix" and self.appendix is not None:
            self.appendix.lines.append(line)
        elif self.mode in ("preamble", "body"):
            self.preamble.append(line)
        elif self.mode == "end":
            self.attach(line)

    def finish(self) -> ParsedDoc:
        if self.quote:
            self.issue("unbalanced_quote")
        for u in self.units:
            if u.kind == "dieu":
                own = [ln for ln in u.lines[1:]]
                children = any(c.parent_id == u.unit_id for c in self.units)
                if not own and not children and not u.title:
                    self.issue("empty_article")
        if not any(u.kind == "dieu" for u in self.units):
            self.issue("no_articles")
            body = self.add("body", "body", "", None)
            body.lines = list(self.preamble)
        return ParsedDoc(
            self.units, self.preamble, self.issues, self.body_chars, self.dropped_chars
        )


def parse(lines: list[str], doc_key: str) -> ParsedDoc:
    p = _Parser(doc_key)
    for line in lines:
        p.feed(line.strip())
    return p.finish()
