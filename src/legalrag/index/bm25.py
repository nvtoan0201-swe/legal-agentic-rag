"""BM25 over chunks with syllable unigrams + bigrams.

Vietnamese words are mostly 1-3 syllables separated by spaces, so syllable bigrams recover most
compound words ("hợp_đồng", "lao_động") without a word segmenter.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Collection
from pathlib import Path

import numpy as np

_WORD = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    syl = _WORD.findall(unicodedata.normalize("NFC", text).lower())
    return syl + [f"{a}_{b}" for a, b in zip(syl, syl[1:], strict=False)]


class BM25Index:
    def __init__(self, retriever, chunk_ids: list[str], doc_keys: list[str]):
        self.retriever = retriever
        self.chunk_ids = chunk_ids
        self.doc_keys = np.array(doc_keys, dtype=object)

    @classmethod
    def build(cls, texts: list[str], chunk_ids: list[str], doc_keys: list[str]) -> BM25Index:
        import bm25s

        r = bm25s.BM25()
        r.index([tokenize(t) for t in texts], show_progress=False)
        return cls(r, chunk_ids, doc_keys)

    def save(self, path: Path) -> None:
        self.retriever.save(str(path), show_progress=False)
        (path / "ids.json").write_text(
            json.dumps({"chunk_ids": self.chunk_ids, "doc_keys": self.doc_keys.tolist()})
        )

    @classmethod
    def load(cls, path: Path) -> BM25Index:
        import bm25s

        r = bm25s.BM25.load(str(path), mmap=False, show_progress=False)
        ids = json.loads((path / "ids.json").read_text())
        return cls(r, ids["chunk_ids"], ids["doc_keys"])

    def search(
        self, query: str, k: int = 50, doc_keys: Collection[str] | None = None
    ) -> list[tuple[str, float]]:
        """(chunk_id, score), best first; `doc_keys` restricts the documents searched."""
        mask = None
        if doc_keys is not None:
            mask = np.isin(self.doc_keys, list(doc_keys)).astype(np.float32)
        k = min(k, len(self.chunk_ids))
        idx, scores = self.retriever.retrieve(
            [tokenize(query)], k=k, show_progress=False, weight_mask=mask
        )
        return [
            (self.chunk_ids[i], float(s)) for i, s in zip(idx[0], scores[0], strict=True) if s > 0
        ]
