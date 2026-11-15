"""Dense embeddings (sentence-transformers) stored in Qdrant with document-level payload filters."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import Protocol

import numpy as np

DEFAULT_MODEL = "BAAI/bge-m3"


class Embedder(Protocol):
    name: str
    dim: int

    def encode(self, texts: Sequence[str], query: bool = False) -> np.ndarray: ...


class STEmbedder:
    """sentence-transformers model on GPU if available (`uv sync --group ml`)."""

    def __init__(
        self,
        name: str = DEFAULT_MODEL,
        max_length: int = 512,
        batch_size: int = 32,
        query_prefix: str = "",
        doc_prefix: str = "",
    ):
        import torch
        from sentence_transformers import SentenceTransformer

        device = "cuda" if torch.cuda.is_available() else "cpu"
        kw = {"torch_dtype": torch.float16} if device == "cuda" else {}
        self.model = SentenceTransformer(name, device=device, model_kwargs=kw)
        self.model.max_seq_length = max_length
        self.name, self.batch_size = name, batch_size
        self.query_prefix, self.doc_prefix = query_prefix, doc_prefix
        self.dim = self.model.get_embedding_dimension()

    def encode(self, texts: Sequence[str], query: bool = False) -> np.ndarray:
        prefix = self.query_prefix if query else self.doc_prefix
        return self.model.encode(
            [prefix + t for t in texts],
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=not query and len(texts) > 1000,
        ).astype(np.float32)


def collection_name(model: str) -> str:
    return "chunks_" + model.split("/")[-1].lower().replace(".", "_")


class QdrantIndex:
    def __init__(self, url: str, collection: str):
        from qdrant_client import QdrantClient

        self.client = QdrantClient(url=url, timeout=60)
        self.collection = collection

    def create(self, dim: int) -> None:
        from qdrant_client import models

        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            self.collection,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )
        self.client.create_payload_index(
            self.collection, "doc_key", field_schema=models.PayloadSchemaType.KEYWORD
        )

    def upsert(
        self, ids: Sequence[str], vectors: np.ndarray, payloads: Sequence[dict], batch: int = 512
    ) -> None:
        from qdrant_client import models

        for i in range(0, len(ids), batch):
            self.client.upsert(
                self.collection,
                points=models.Batch(
                    ids=list(ids[i : i + batch]),
                    vectors=vectors[i : i + batch].tolist(),
                    payloads=list(payloads[i : i + batch]),
                ),
                wait=True,
            )

    def search(
        self, vector: np.ndarray, k: int = 50, doc_keys: Collection[str] | None = None
    ) -> list[tuple[str, float]]:
        from qdrant_client import models

        flt = None
        if doc_keys is not None:
            flt = models.Filter(
                must=[
                    models.FieldCondition(key="doc_key", match=models.MatchAny(any=list(doc_keys)))
                ]
            )
        res = self.client.query_points(
            self.collection, query=vector.tolist(), limit=k, query_filter=flt, with_payload=False
        )
        return [(str(p.id), float(p.score)) for p in res.points]

    def count(self) -> int:
        return self.client.count(self.collection).count
