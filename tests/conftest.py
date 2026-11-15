import json

import numpy as np
import pandas as pd
import pytest

from legalrag.index.bm25 import BM25Index
from legalrag.index.chunks import build_chunks
from legalrag.retrieval.retriever import Retriever
from legalrag.store import Corpus


def _docs():
    return pd.DataFrame(
        {
            "doc_key": ["L1", "ND", "L0"],
            "title": [
                "Bộ luật Lao động số L1",
                "Nghị định số ND quy định chi tiết Bộ luật Lao động",
                "Bộ luật Lao động số L0",
            ],
            "loai_van_ban": ["Bộ luật", "Nghị định", "Bộ luật"],
            "status": ["in_force", "in_force", "expired"],
            "core": [True, True, True],
            "domains": [["lao_dong"]] * 3,
            "ngay_co_hieu_luc": pd.to_datetime(["2021-01-01", "2021-02-01", "2013-05-01"]),
            "ngay_het_hieu_luc": pd.to_datetime([None, None, None]),
        }
    )


def _units():
    rows = [
        # unit_id, doc_key, kind, parent_id, text
        ("L1#d35", "L1", "dieu", None, "Điều 35. Quyền đơn phương chấm dứt hợp đồng lao động"),
        ("L1#d35-k1", "L1", "khoan", "L1#d35", "1. Người lao động phải báo trước như sau:"),
        (
            "L1#d35-k1-a",
            "L1",
            "diem",
            "L1#d35-k1",
            "a) Ít nhất 45 ngày nếu không xác định thời hạn;",
        ),
        ("L1#d35-k1-b", "L1", "diem", "L1#d35-k1", "b) Ít nhất 30 ngày nếu có thời hạn."),
        ("L1#d35-k2", "L1", "khoan", "L1#d35", "2. Không cần báo trước khi bị quấy rối tình dục."),
        ("L1#d36", "L1", "dieu", None, "Điều 36. Thời giờ làm việc bình thường không quá 8 giờ."),
        ("ND#d7", "ND", "dieu", None, "Điều 7. Thời hạn báo trước"),
        (
            "ND#d7-k1",
            "ND",
            "khoan",
            "ND#d7",
            "1. Thời hạn báo trước theo điểm d khoản 1 Điều 35 của Bộ luật Lao động là 120 ngày.",
        ),
        ("L0#d37", "L0", "dieu", None, "Điều 37. Quyền đơn phương chấm dứt hợp đồng lao động"),
        ("L0#d37-k1", "L0", "khoan", "L0#d37", "1. Người lao động báo trước ít nhất 30 ngày."),
    ]
    df = pd.DataFrame(rows, columns=["unit_id", "doc_key", "kind", "parent_id", "text"])
    df["ordinal"] = df.groupby("doc_key").cumcount()
    return df


def _rels():
    return pd.DataFrame(
        {
            "actor_key": ["ND", "L1"],
            "target_key": ["L1", "L0"],
            "rel": ["guides", "replaces"],
            "suspect": [False, False],
        }
    )


@pytest.fixture
def frames():
    return _docs(), _units(), _rels()


@pytest.fixture
def corpus(frames):
    return Corpus(*frames)


class FakeEmbedder:
    """Bag of words over a fixed vocabulary."""

    name, dim = "fake", 8
    vocab = ["báo", "trước", "ngày", "giờ", "làm", "việc", "quấy", "rối"]

    def encode(self, texts, query=False):
        v = np.array([[t.lower().count(w) for w in self.vocab] for t in texts], dtype=np.float32)
        return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


class FakeDense:
    def __init__(self, chunks, emb):
        self.ids = [c.chunk_id for c in chunks]
        self.docs = [c.doc_key for c in chunks]
        self.m = emb.encode([c.full() for c in chunks])

    def search(self, vec, k=50, doc_keys=None):
        s = self.m @ vec
        order = [i for i in np.argsort(-s) if doc_keys is None or self.docs[i] in doc_keys]
        return [(self.ids[i], float(s[i])) for i in order[:k]]


class FakeReranker:
    def score(self, query, texts):
        return [1.0 if "quấy rối" in t else 0.1 for t in texts]


@pytest.fixture
def retriever(frames, corpus):
    docs, units, _ = frames
    chunks = build_chunks(units, docs)
    emb = FakeEmbedder()
    bm25 = BM25Index.build(
        [c.full() for c in chunks], [c.chunk_id for c in chunks], [c.doc_key for c in chunks]
    )
    return Retriever(chunks, bm25, FakeDense(chunks, emb), emb, FakeReranker(), corpus.in_force)


class FakeLLM:
    """Scripted LLM: answers by prompt type, records calls."""

    def __init__(self, answer: str, analyze: dict | None = None):
        self.answer, self.analyze_out, self.calls = answer, analyze, []

    def __call__(self, prompt: str, system: str | None = None, **kw) -> str:
        self.calls.append(prompt)
        if prompt.startswith("Phân tích câu hỏi"):
            return json.dumps(self.analyze_out or {"in_scope": True, "queries": []})
        if prompt.startswith("Câu hỏi:"):  # refine
            return json.dumps({"queries": ["báo trước"]})
        return self.answer


@pytest.fixture
def fake_llm():
    return FakeLLM
