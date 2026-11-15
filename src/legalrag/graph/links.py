"""Provision-level cross-references: "khoản 2 Điều 35 của Bộ luật này", "Điều 9 của Luật Đất đai".

Edges are resolved to unit ids: references inside the same document ("của Luật này", "Nghị định
này", or a bare "Điều N") stay in the citing document; a named law resolves to the law with that
name that had been issued by the time the citing document was (a 2014 decree citing "Luật Đất
đai" means the 2013 law, not the 2024 one), unless the number is spelled out.

Used by the agent to pull in what a retrieved clause depends on (outgoing) and the decree /
circular provisions that detail it (incoming).
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass

import pandas as pd

from legalrag.eval.drafts import law_name

LAW_TYPES = ("Luật", "Bộ luật")
SELF = (
    r"(?:Bộ\s+luật|Luật|Nghị\s+định|Thông\s+tư(?:\s+liên\s+tịch)?|Quyết\s+định|Pháp\s+lệnh)\s+này"
)
_REF = (
    r"(?:điểm\s+(?P<diem>[a-zđ])\s*,?\s+)?(?:khoản\s+(?P<khoan>\d+)\s*,?\s+)?"
    r"Điều\s+(?P<dieu>\d+[a-zđ]?)(?![\d/])"
)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip().lower()


@dataclass
class Law:
    doc_key: str
    name: str  # "luật đất đai" (normalised)
    issued: pd.Timestamp | None


def ancestors(unit_id: str) -> list[str]:
    """'D#d35-k1-a' -> ['D#d35', 'D#d35-k1'] (the document key may itself contain '-')."""
    doc, frag = unit_id.split("#", 1)
    parts = frag.split("-")
    return [f"{doc}#{'-'.join(parts[:i])}" for i in range(1, len(parts))]


def _with_descendants(d: dict[str, list[str]]) -> dict[str, list[str]]:
    """Fold every key's values into its ancestors too, so a lookup on an article or clause
    covers its points."""
    out: dict[str, list[str]] = defaultdict(list)
    for k, vs in d.items():
        for a in [k, *ancestors(k)]:
            out[a] += vs
    return {k: list(dict.fromkeys(v)) for k, v in out.items()}


class Links:
    def __init__(self, out: dict[str, list[str]]):
        self.out = out
        inc: dict[str, list[str]] = defaultdict(list)
        for src, dsts in out.items():
            for d in dsts:
                inc[d].append(src)
        self.inc = dict(inc)
        self._out_all = _with_descendants(self.out)
        self._inc_all = _with_descendants(self.inc)

    @classmethod
    def build(cls, docs: pd.DataFrame, units: pd.DataFrame) -> Links:
        docs = docs.set_index("doc_key", drop=False)
        issued = docs["ngay_ban_hanh"].fillna(docs["ngay_co_hieu_luc"]).to_dict()
        laws = [
            Law(k, _norm(law_name(t)), None if pd.isna(issued[k]) else pd.Timestamp(issued[k]))
            for k, t, typ in zip(docs["doc_key"], docs["title"], docs["loai_van_ban"], strict=True)
            if typ in LAW_TYPES
        ]
        names = sorted({law.name for law in laws}, key=len, reverse=True)
        named = (
            r"(?:của\s+)?(?P<law>"
            + "|".join(re.escape(n).replace(r"\ ", r"\s+") for n in names)
            + r")(?:\s+(?:năm\s+\d{4}\s+)?(?:số\s+)?(?P<num>\d+/\d{4}/QH\d+))?"
        )
        rx = re.compile(_REF + r"\s*(?:(?:của\s+)?(?P<self>" + SELF + r")|" + named + r")?", re.I)
        by_name: dict[str, list[Law]] = defaultdict(list)
        for law in laws:
            by_name[law.name].append(law)
        ids = set(units["unit_id"])

        def target_doc(m: re.Match, doc: str) -> str | None:
            if m.group("law"):
                if m.group("num"):
                    return m.group("num")
                cands = by_name.get(_norm(m.group("law")), [])
                when = issued.get(doc)
                ok = [c for c in cands if c.issued is None or when is None or c.issued <= when]
                pick = max(ok, key=lambda c: c.issued or pd.Timestamp.min, default=None)
                return pick.doc_key if pick else None
            return doc  # "của Luật này" or bare "Điều N": same document

        out: dict[str, list[str]] = {}
        for uid, doc, text in zip(units["unit_id"], units["doc_key"], units["text"], strict=True):
            if "Điều" not in text and "điều" not in text:
                continue
            found = []
            for m in rx.finditer(text):
                # A bare "Điều N." at the very start is the article's own heading.
                if m.start() == 0 and not (m.group("khoan") or m.group("law") or m.group("self")):
                    continue
                d = target_doc(m, doc)
                if d is None:
                    continue
                t = f"{d}#d{m.group('dieu').lower()}"
                diem = m.group("diem")
                parts = [
                    m.group("khoan") and f"-k{m.group('khoan')}",
                    diem and "-" + ("dd" if diem.lower() == "đ" else diem.lower()),
                ]
                for part in parts:  # khoản then điểm, as deep as the target exists
                    if part and f"{t}{part}" in ids:
                        t += part
                    else:
                        break
                if t in ids and not uid.startswith(t):
                    found.append(t)
            if found:
                out[uid] = list(dict.fromkeys(found))
        return cls(out)

    def outgoing(self, unit_id: str) -> list[str]:
        """Provisions cited by the unit or any of its descendants."""
        return [x for x in self._out_all.get(unit_id, []) if not x.startswith(unit_id)]

    def incoming(self, unit_id: str) -> list[str]:
        """Provisions citing the unit, its descendants, or its article as a whole."""
        res = list(self._inc_all.get(unit_id, []))
        for a in ancestors(unit_id)[:1]:  # "Điều 35" cited without a clause
            res += self.inc.get(a, [])
        return [x for x in dict.fromkeys(res) if not x.startswith(unit_id)]
