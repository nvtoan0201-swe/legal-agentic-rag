"""In-memory view of the processed corpus (documents, units, relations) used at query time.

The parquet files written by `make ingest` are small enough (~25 MB) to keep in memory, so the
retriever and the agent read them directly instead of round-tripping to Postgres.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from functools import cached_property
from pathlib import Path

import pandas as pd

from legalrag.eval.metrics import to_article

# Date the resolved `status` column refers to (see reports/data_quality.md).
STATUS_AS_OF = date(2026, 11, 11)


class Corpus:
    def __init__(self, docs: pd.DataFrame, units: pd.DataFrame, rels: pd.DataFrame):
        self.docs = docs.set_index("doc_key", drop=False)
        self.units = units.sort_values(["doc_key", "ordinal"]).reset_index(drop=True)
        self.rels = rels

    @classmethod
    def load(cls, processed: Path | str = "data/processed") -> Corpus:
        p = Path(processed)
        return cls(
            pd.read_parquet(p / "documents.parquet"),
            pd.read_parquet(p / "units.parquet"),
            pd.read_parquet(p / "relations.parquet"),
        )

    # -- units ---------------------------------------------------------------------------------

    @cached_property
    def _text(self) -> dict[str, str]:
        return dict(zip(self.units["unit_id"], self.units["text"], strict=True))

    @cached_property
    def _children(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = defaultdict(list)
        for uid, parent in zip(self.units["unit_id"], self.units["parent_id"], strict=True):
            if isinstance(parent, str):
                out[parent].append(uid)
        return out

    def has(self, unit_id: str) -> bool:
        return unit_id in self._text

    def text(self, unit_id: str) -> str:
        """Own text of a unit plus all of its descendants, in document order."""
        if unit_id not in self._text:
            return ""
        parts = [self._text[unit_id]]
        for c in self._children.get(unit_id, []):
            parts.append(self.text(c))
        return "\n".join(parts)

    def heading(self, unit_id: str) -> str:
        """'Điều 35. Quyền đơn phương ...' for any unit inside an article."""
        return self._text.get(to_article(unit_id), "")

    def passage(self, unit_id: str) -> str:
        """Self-contained text for a prompt: article heading + the unit with its children."""
        art = to_article(unit_id)
        body = self.text(unit_id)
        return body if art == unit_id else f"{self.heading(unit_id)}\n{body}"

    # -- documents -----------------------------------------------------------------------------

    def doc(self, doc_key: str) -> pd.Series | None:
        return self.docs.loc[doc_key] if doc_key in self.docs.index else None

    def status(self, doc_key: str) -> str | None:
        d = self.doc(doc_key)
        return None if d is None else d["status"]

    def title(self, doc_key: str) -> str:
        d = self.doc(doc_key)
        return "" if d is None else d["title"]

    def in_force(self, as_of: date | None = None) -> set[str]:
        """Documents in force at `as_of` (default: the date the status column was resolved).

        On or after STATUS_AS_OF the resolved status is authoritative (it already folds in
        overrides, replacement edges and the legacy crawl); a document must also have started.
        Before it, dates decide, falling back to the status when a date is missing.
        """
        as_of = as_of or STATUS_AS_OF
        d = self.docs
        ts = pd.Timestamp(as_of)
        started = d["ngay_co_hieu_luc"].isna() | (d["ngay_co_hieu_luc"] <= ts)
        if as_of >= STATUS_AS_OF:
            ok = started & (d["status"] == "in_force")
        else:
            # Missing end date: use the start of the replacing document. Expired documents whose
            # end date is still unknown are dropped (they ended at some point before the snapshot).
            end = d["ngay_het_hieu_luc"].fillna(d["doc_key"].map(self.replaced_on))
            ended = end.notna() & (end <= ts)
            unknown_end = end.isna() & (d["status"] == "expired")
            ok = started & ~ended & ~unknown_end & d["status"].isin(["in_force", "expired"])
        return set(d.index[ok])

    @cached_property
    def replaced_on(self) -> dict[str, pd.Timestamp]:
        """Expired doc -> earliest start date of a document that replaces / repeals it."""
        r = self.rels[self.rels["rel"].isin(["replaces", "repeals"]) & ~self.rels["suspect"]]
        r = r.dropna(subset=["actor_key", "target_key"])
        start = self.docs["ngay_co_hieu_luc"]
        r = r.assign(start=r["actor_key"].map(start)).dropna(subset=["start"])
        return r.groupby("target_key")["start"].min().to_dict()

    def related(self, doc_key: str, rels: tuple[str, ...], incoming: bool = True) -> list[str]:
        """Documents linked to `doc_key` by `rels` (incoming: they act on doc_key)."""
        r = self.rels[self.rels["rel"].isin(rels) & ~self.rels["suspect"]]
        if incoming:
            return r.loc[r["target_key"] == doc_key, "actor_key"].dropna().unique().tolist()
        return r.loc[r["actor_key"] == doc_key, "target_key"].dropna().unique().tolist()
