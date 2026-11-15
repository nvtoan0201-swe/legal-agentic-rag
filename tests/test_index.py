from datetime import date

from legalrag.index.bm25 import tokenize
from legalrag.index.chunks import build_chunks, doc_label, windows
from legalrag.retrieval.retriever import RetrievalConfig, rrf, unit_ids


def test_corpus_text_and_passage(corpus):
    assert corpus.text("L1#d35-k1").splitlines() == [
        "1. Người lao động phải báo trước như sau:",
        "a) Ít nhất 45 ngày nếu không xác định thời hạn;",
        "b) Ít nhất 30 ngày nếu có thời hạn.",
    ]
    assert corpus.passage("L1#d35-k2").startswith("Điều 35. Quyền đơn phương")


def test_in_force(corpus):
    assert corpus.in_force() == {"L1", "ND"}
    # Before the new code started, the old one (no end date, replaced by L1) was in force.
    assert corpus.in_force(date(2020, 6, 1)) == {"L0"}
    assert corpus.in_force(date(2021, 1, 15)) == {"L1"}


def test_doc_label():
    assert doc_label("Nghị định số 12/2022/NĐ-CP Quy định xử phạt", "12/2022/NĐ-CP") == (
        "Nghị định Quy định xử phạt (12/2022/NĐ-CP)"
    )


def test_windows_cut_and_overlap():
    text = " ".join(f"w{i}" for i in range(600))
    ws = windows(text, size=500, overlap=100)
    assert all(len(w) <= 500 for w in ws)
    assert ws[0].split()[-1] in ws[1]  # overlap
    assert ws[-1].endswith("w599")


def test_chunks_one_per_clause(frames):
    docs, units, _ = frames
    chunks = {c.unit_id: c for c in build_chunks(units, docs)}
    # Article 35 has clauses: no chunk of its own; points join their clause; heading prepended.
    assert set(chunks) == {"L1#d35-k1", "L1#d35-k2", "L1#d36", "ND#d7-k1", "L0#d37-k1"}
    c = chunks["L1#d35-k1"]
    assert c.text.splitlines()[0].startswith("Điều 35.")
    assert "45 ngày" in c.text and "30 ngày" in c.text
    assert c.label == "Bộ luật Lao động (L1)"
    assert c.article_id == "L1#d35"


def test_tokenize_bigrams():
    assert tokenize("Hợp đồng lao động") == [
        "hợp", "đồng", "lao", "động", "hợp_đồng", "đồng_lao", "lao_động",
    ]  # fmt: skip


def test_rrf():
    fused = rrf({"a": ["x", "y"], "b": ["y", "z"]}, {"a": 1.0, "b": 1.0}, k=60)
    assert [i for i, _ in fused] == ["y", "x", "z"]


def test_retriever_modes(retriever):
    r = retriever
    q = "nghỉ việc phải báo trước bao nhiêu ngày"
    for mode in ("bm25", "dense", "hybrid"):
        ids = unit_ids(r.search(q, RetrievalConfig(mode=mode, k=3)))
        assert {"L1#d35-k1", "L0#d37-k1"} & set(ids), mode


def test_retriever_in_force_filter(retriever):
    r = retriever
    q = "người lao động báo trước 30 ngày"
    assert "L0#d37-k1" in unit_ids(r.search(q, RetrievalConfig(mode="bm25", k=5)))
    got = unit_ids(r.search(q, RetrievalConfig(mode="hybrid", k=5, in_force_only=True)))
    assert got and all(not x.startswith("L0#") for x in got)
    old = unit_ids(
        r.search(q, RetrievalConfig(mode="bm25", k=5, in_force_only=True, as_of=date(2020, 1, 1)))
    )
    assert old == ["L0#d37-k1"]


def test_rerank_reorders(retriever):
    r = retriever
    hits = r.search("báo trước", RetrievalConfig(mode="bm25", k=5, rerank=True))
    assert hits[0].unit_id == "L1#d35-k2" and hits[0].score == 1.0
