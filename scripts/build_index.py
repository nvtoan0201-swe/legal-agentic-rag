"""Build retrieval indexes: chunks.parquet, BM25, and dense vectors in Qdrant.

    uv run python -I scripts/build_index.py                 # chunks + BM25 + bge-m3
    uv run python -I scripts/build_index.py --model AITeamVN/Vietnamese_Embedding --skip-bm25

Embeddings are cached in data/index/emb_<model>.npy so Qdrant can be refilled without the GPU.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from legalrag.config import settings
from legalrag.index.bm25 import BM25Index
from legalrag.index.chunks import build_chunks, to_frame
from legalrag.index.dense import DEFAULT_MODEL, QdrantIndex, STEmbedder, collection_name


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--skip-bm25", action="store_true")
    ap.add_argument("--skip-dense", action="store_true")
    ap.add_argument("--limit", type=int, help="first N chunks only (smoke test)")
    args = ap.parse_args()

    data = Path(settings.data_dir)
    out = data / "index"
    out.mkdir(parents=True, exist_ok=True)

    t = time.time()
    docs = pd.read_parquet(data / "processed/documents.parquet")
    units = pd.read_parquet(data / "processed/units.parquet")
    df = to_frame(build_chunks(units, docs))
    if args.limit:
        df = df.head(args.limit)
    df.to_parquet(out / "chunks.parquet", index=False)
    full = (df["label"] + "\n" + df["text"]).tolist()
    print(f"chunks: {len(df):,} ({time.time() - t:.0f}s)")

    if not args.skip_bm25:
        t = time.time()
        BM25Index.build(full, df["chunk_id"].tolist(), df["doc_key"].tolist()).save(out / "bm25")
        print(f"bm25: done ({time.time() - t:.0f}s)")

    if not args.skip_dense:
        t = time.time()
        cache = out / f"emb_{collection_name(args.model)}.npy"
        if cache.exists() and np.load(cache, mmap_mode="r").shape[0] == len(df):
            vecs = np.load(cache)
            print(f"embeddings: cached {cache}")
        else:
            emb = STEmbedder(args.model, max_length=args.max_length, batch_size=args.batch_size)
            # Longest first keeps padding low inside each batch.
            order = np.argsort([-len(x) for x in full])
            enc = emb.encode([full[i] for i in order])
            vecs = np.empty_like(enc)
            vecs[order] = enc
            np.save(cache, vecs)
            print(f"embeddings: {vecs.shape} ({time.time() - t:.0f}s)")
        q = QdrantIndex(settings.qdrant_url, collection_name(args.model))
        q.create(vecs.shape[1])
        payloads = [
            {"unit_id": u, "doc_key": d, "part": int(p)}
            for u, d, p in zip(df["unit_id"], df["doc_key"], df["part"], strict=True)
        ]
        q.upsert(df["chunk_id"].tolist(), vecs, payloads)
        print(f"qdrant {q.collection}: {q.count():,} points ({time.time() - t:.0f}s)")


if __name__ == "__main__":
    main()
