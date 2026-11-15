from legalrag.baselines.rag import ExtractiveGenerator, Generator, NaiveRAG, passages
from legalrag.retrieval.retriever import RetrievalConfig


def test_passages_mark_expired(retriever, corpus):
    r = retriever
    hits = r.search("báo trước 30 ngày", RetrievalConfig(mode="bm25", k=5))
    ps = {p.unit_id: p for p in passages(hits, corpus)}
    assert "ĐÃ HẾT HIỆU LỰC" in ps["L0#d37-k1"].label
    assert ps["L1#d35-k1"].text.startswith("Điều 35.")  # full passage from the corpus


def test_naive_rag(retriever, corpus, fake_llm):
    r = retriever
    llm = fake_llm("Phải báo trước ít nhất 45 ngày [L1#d35-k1].")
    rag = NaiveRAG(r, Generator(llm), corpus, RetrievalConfig(mode="bm25", k=5))
    res = rag.run("nghỉ việc báo trước bao lâu")
    assert res.answer.citations == ["L1#d35-k1"] and not res.answer.abstained
    assert "[L1#d35-k1]" in llm.calls[0]


def test_extractive_generator(retriever, corpus):
    r = retriever
    rag = NaiveRAG(r, ExtractiveGenerator(), corpus, RetrievalConfig(mode="bm25", k=3))
    ans = rag.run("quấy rối tình dục").answer
    assert ans.citations == ["L1#d35-k2"]
