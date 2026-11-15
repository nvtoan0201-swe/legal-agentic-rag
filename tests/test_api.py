from fastapi.testclient import TestClient

from legalrag.api import app as api
from legalrag.baselines.rag import ExtractiveGenerator
from legalrag.graph.agent import Agent, AgentConfig
from legalrag.graph.links import Links
from legalrag.retrieval.retriever import RetrievalConfig


def test_ask_and_search(monkeypatch, frames, corpus, retriever):
    docs, units, _ = frames
    links = Links.build(docs.assign(ngay_ban_hanh=docs["ngay_co_hieu_luc"]), units)
    cfg = AgentConfig(retrieval=RetrievalConfig(mode="bm25", k=5, rerank=True), gate_threshold=0.5)
    agent = Agent(retriever, corpus, links, ExtractiveGenerator(), None, cfg)
    monkeypatch.setattr(api, "_system", lambda: (agent, "extractive"))
    client = TestClient(api.app)

    assert "Agentic RAG" in client.get("/").text
    r = client.post("/ask", json={"question": "bị quấy rối tình dục có phải báo trước không"})
    j = r.json()
    assert r.status_code == 200 and not j["abstained"] and j["mode"] == "extractive"
    assert j["citations"][0]["unit_id"] == "L1#d35-k2" and j["citations"][0]["status"] == "in_force"

    r = client.post("/ask", json={"question": "thời giờ làm việc"})
    assert r.json()["abstained"]  # below the evidence gate

    hits = client.post("/search", json={"question": "báo trước"}).json()
    assert hits and all(h["status"] == "in_force" for h in hits)
