"""Split the corpus into retrieval chunks.

One chunk per clause (khoản) with its points; an article without clauses is one chunk. Every chunk
starts with the article heading so a clause like "2. Trường hợp ..." is understandable alone, and
carries a short document label (title + number) because users name laws, not numbers. Long units
(annexes, attachments, undivided documents, huge clauses) are cut into overlapping windows that
keep the unit id; `part` tells them apart.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

import pandas as pd

from legalrag.eval.metrics import to_article

MAX_CHARS = 1500
OVERLAP = 200
TITLE_CHARS = 160
HEADING_CHARS = 300
_NS = uuid.UUID("6f1d3b8e-8a43-4b8e-9d3a-6c0e0f7a2b11")


@dataclass
class Chunk:
    chunk_id: str  # uuid (Qdrant point id)
    unit_id: str  # the clause / article / annex the chunk belongs to
    doc_key: str
    part: int
    label: str  # "Bộ luật Lao động (45/2019/QH14)"
    text: str  # body without the label

    @property
    def article_id(self) -> str:
        return to_article(self.unit_id)

    def full(self) -> str:
        return f"{self.label}\n{self.text}"


def doc_label(title: str, doc_key: str) -> str:
    t = re.sub(r"\s+", " ", title).strip()
    # "Nghị định số 21/2016/NĐ-CP Quy định ..." -> drop the repeated number.
    t = re.sub(r"\s*(?:số\s+)?" + re.escape(doc_key) + r"\s*", " ", t).strip()
    if len(t) > TITLE_CHARS:
        t = t[:TITLE_CHARS].rsplit(" ", 1)[0] + "…"
    return f"{t} ({doc_key})"


def windows(text: str, size: int = MAX_CHARS, overlap: int = OVERLAP) -> list[str]:
    """Cut on line breaks where possible, falling back to spaces."""
    if len(text) <= size:
        return [text]
    out, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            cut = max(
                text.rfind("\n", start + size // 2, end), text.rfind(" ", start + size // 2, end)
            )
            end = cut if cut > start else end
        out.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [w for w in out if w]


def chunk_owner(kind: str, unit_id: str, parent: str | None) -> str:
    """The unit whose chunk a unit's text goes into: points join their clause (or article)."""
    return parent if kind == "diem" and parent else unit_id


def build_chunks(units: pd.DataFrame, docs: pd.DataFrame) -> list[Chunk]:
    u = units.sort_values(["doc_key", "ordinal"])
    labels = {k: doc_label(t, k) for k, t in zip(docs["doc_key"], docs["title"], strict=True)}
    has_clause = set(u.loc[u["kind"] == "khoan", "parent_id"])

    # owner unit -> its text lines, in document order; articles with clauses only give a heading.
    lines: dict[str, list[str]] = {}
    owner_doc: dict[str, str] = {}
    for uid, doc, kind, parent, text in zip(
        u["unit_id"], u["doc_key"], u["kind"], u["parent_id"], u["text"], strict=True
    ):
        parent = parent if isinstance(parent, str) else None
        if kind == "dieu" and uid in has_clause:
            continue
        owner = chunk_owner(kind, uid, parent)
        lines.setdefault(owner, []).append(text)
        owner_doc[owner] = doc

    heading = {
        uid: text
        for uid, kind, text in zip(u["unit_id"], u["kind"], u["text"], strict=True)
        if kind == "dieu"
    }
    chunks = []
    for owner, ls in lines.items():
        body = "\n".join(ls)
        art = to_article(owner)
        head = heading.get(art, "") if art != owner else ""
        if len(head) > HEADING_CHARS:  # amending articles quote whole titles in the heading
            head = head[:HEADING_CHARS].rsplit(" ", 1)[0] + "…"
        for i, w in enumerate(windows(body, MAX_CHARS - len(head))):
            text = f"{head}\n{w}" if head else w
            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid5(_NS, f"{owner}|{i}")),
                    unit_id=owner,
                    doc_key=owner_doc[owner],
                    part=i,
                    label=labels.get(owner_doc[owner], owner_doc[owner]),
                    text=text,
                )
            )
    return chunks


def to_frame(chunks: list[Chunk]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "chunk_id": [c.chunk_id for c in chunks],
            "unit_id": [c.unit_id for c in chunks],
            "doc_key": [c.doc_key for c in chunks],
            "part": [c.part for c in chunks],
            "label": [c.label for c in chunks],
            "text": [c.text for c in chunks],
        }
    )


def from_frame(df: pd.DataFrame) -> list[Chunk]:
    return [
        Chunk(r.chunk_id, r.unit_id, r.doc_key, int(r.part), r.label, r.text)
        for r in df.itertuples(index=False)
    ]
