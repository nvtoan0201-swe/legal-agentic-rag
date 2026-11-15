"""Retriever: BM25 / dense / hybrid (RRF) candidates, optional cross-encoder rerank, optional
in-force filter. Returns hits at chunk level; `unit_id` is the clause / article to cite.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Protocol

import pandas as pd

from legalrag.index.chunks import Chunk, from_frame

RRF_K = 60


@dataclass
class Hit:
    chunk_id: str
    unit_id: str
    doc_key: str
    text: str  # label + chunk text
    score: float
    source: str = ""  # bm25 | dense | hybrid | rerank | graph:<rel>


@dataclass
class RetrievalConfig:
    mode: str = "hybrid"  # bm25 | dense | hybrid
    k: int = 10  # hits returned
    candidates: int = 50  # per retriever before fusion / rerank
    rerank: bool = False
    rerank_candidates: int = 30
    in_force_only: bool = False
    as_of: date | None = None
    weights: dict[str, float] = field(default_factory=lambda: {"bm25": 1.0, "dense": 1.0})


class Reranker(Protocol):
    def score(self, query: str, texts: Sequence[str]) -> list[float]: ...


class CrossEncoderReranker:
    def __init__(self, name: str | None = None, max_length: int = 512):
        import torch
        from sentence_transformers import CrossEncoder

        from legalrag.config import settings

        device = "cuda" if torch.cuda.is_available() else "cpu"
        kw = {"torch_dtype": torch.float16} if device == "cuda" else {}
        self.model = CrossEncoder(
            name or settings.reranker_model, device=device, max_length=max_length, model_kwargs=kw
        )

    def score(self, query: str, texts: Sequence[str]) -> list[float]:
        if not texts:
            return []
        # bge-reranker uses a sigmoid head: scores in [0, 1], comparable across queries (the
        # agent thresholds them to decide whether there is enough evidence).
        s = self.model.predict([(query, t) for t in texts], batch_size=16, show_progress_bar=False)
        return [float(x) for x in s]


def rrf(rankings: dict[str, list[str]], weights: dict[str, float], k: int = RRF_K) -> list[tuple]:
    """Weighted reciprocal rank fusion -> [(id, score)] best first."""
    score: dict[str, float] = {}
    for name, ids in rankings.items():
        w = weights.get(name, 1.0)
        for rank, x in enumerate(ids, 1):
            score[x] = score.get(x, 0.0) + w / (k + rank)
    return sorted(score.items(), key=lambda kv: -kv[1])


class Retriever:
    def __init__(
        self,
        chunks: Sequence[Chunk],
        bm25=None,
        dense=None,
        embedder=None,
        reranker: Reranker | None = None,
        in_force: Callable[[date | None], set[str]] | None = None,
    ):
        """`in_force(as_of) -> set[doc_key]`, usually Corpus.in_force."""
        self.chunks = {c.chunk_id: c for c in chunks}
        self.bm25, self.dense, self.embedder = bm25, dense, embedder
        self.reranker = reranker
        self.in_force = in_force

    @classmethod
    def from_disk(
        cls,
        index_dir: Path | str = "data/index",
        qdrant_url: str | None = None,
        model: str | None = None,
        reranker: bool | str = True,
        corpus=None,
    ) -> Retriever:
        from legalrag.config import settings
        from legalrag.index.bm25 import BM25Index
        from legalrag.index.dense import DEFAULT_MODEL, QdrantIndex, STEmbedder, collection_name

        index_dir = Path(index_dir)
        model = model or settings.embed_model or DEFAULT_MODEL
        chunks = from_frame(pd.read_parquet(index_dir / "chunks.parquet"))
        rr = None
        if reranker:
            rr = CrossEncoderReranker(*([reranker] if isinstance(reranker, str) else []))
        return cls(
            chunks,
            bm25=BM25Index.load(index_dir / "bm25"),
            dense=QdrantIndex(qdrant_url or settings.qdrant_url, collection_name(model)),
            embedder=STEmbedder(model),
            reranker=rr,
            in_force=corpus.in_force if corpus is not None else None,
        )

    def hit(self, cid: str, score: float, source: str) -> Hit:
        c = self.chunks[cid]
        return Hit(cid, c.unit_id, c.doc_key, c.full(), score, source)

    def candidates(
        self, query: str, cfg: RetrievalConfig, doc_keys: Collection[str] | None
    ) -> list[Hit]:
        rankings: dict[str, list[str]] = {}
        scores: dict[str, dict[str, float]] = {}
        if cfg.mode in ("bm25", "hybrid"):
            res = self.bm25.search(query, cfg.candidates, doc_keys)
            rankings["bm25"] = [c for c, _ in res]
            scores["bm25"] = dict(res)
        if cfg.mode in ("dense", "hybrid"):
            vec = self.embedder.encode([query], query=True)[0]
            res = self.dense.search(vec, cfg.candidates, doc_keys)
            rankings["dense"] = [c for c, _ in res]
            scores["dense"] = dict(res)
        if cfg.mode == "hybrid":
            return [self.hit(c, s, "hybrid") for c, s in rrf(rankings, cfg.weights)]
        (name,) = rankings
        return [self.hit(c, scores[name][c], name) for c in rankings[name]]

    def rerank(self, query: str, hits: list[Hit], n: int | None = None) -> list[Hit]:
        hits = hits[:n] if n else hits
        s = self.reranker.score(query, [h.text for h in hits])
        out = [
            replace(h, score=x, source=f"rerank<{h.source}") for h, x in zip(hits, s, strict=True)
        ]
        return sorted(out, key=lambda h: -h.score)

    def allowed_docs(self, cfg: RetrievalConfig) -> set[str] | None:
        if not cfg.in_force_only:
            return None
        if self.in_force is None:
            raise ValueError("in_force_only needs a corpus (Retriever(in_force=corpus.in_force))")
        return self.in_force(cfg.as_of)

    def search(self, query: str, cfg: RetrievalConfig | None = None) -> list[Hit]:
        cfg = cfg or RetrievalConfig()
        hits = self.candidates(query, cfg, self.allowed_docs(cfg))
        if cfg.rerank and self.reranker is not None:
            hits = self.rerank(query, hits, cfg.rerank_candidates)
        return hits[: cfg.k]


def unit_ids(hits: Sequence[Hit]) -> list[str]:
    return [h.unit_id for h in hits]
