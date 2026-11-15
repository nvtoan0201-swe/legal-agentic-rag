import pytest

from legalrag.baselines.rag import ABSTAIN_TEXT, ExtractiveGenerator, Generator
from legalrag.eval.schema import Behavior, Category, EvalItem
from legalrag.eval.versions import fill_current_gold
from legalrag.graph.agent import Agent, AgentConfig
from legalrag.graph.links import Links, ancestors
from legalrag.retrieval.retriever import RetrievalConfig


def test_ancestors():
    assert ancestors("126/2014/NĐ-CP#d12-k2-a") == ["126/2014/NĐ-CP#d12", "126/2014/NĐ-CP#d12-k2"]


def test_links(frames):
    docs, units, _ = frames
    docs = docs.assign(ngay_ban_hanh=docs["ngay_co_hieu_luc"])
    links = Links.build(docs, units)
    # The decree clause cites "điểm d khoản 1 Điều 35 của Bộ luật Lao động" -> the 2019 code
    # (L1), not the 2012 one, because it was issued after L1. Point d does not exist -> clause.
    assert links.outgoing("ND#d7") == ["L1#d35-k1"]
    assert links.incoming("L1#d35-k1") == ["ND#d7-k1"]
    assert links.incoming("L1#d35") == ["ND#d7-k1"]  # article-level lookup covers its clauses


def test_fill_current_gold(corpus):
    item = EvalItem(
        id="x",
        question="Nghỉ việc phải báo trước bao lâu?",
        category=Category.EXPIRED,
        expected_behavior=Behavior.ANSWER_CURRENT,
        forbidden_articles=["L0#d37"],
        source="t",
    )
    (got,) = fill_current_gold([item], corpus)
    assert got.gold_articles == ["L1#d35"] and got.meta["gold"] == "silver_same_title"


@pytest.fixture
def make_agent(frames, corpus, retriever):
    docs, units, _ = frames
    links = Links.build(docs.assign(ngay_ban_hanh=docs["ngay_co_hieu_luc"]), units)

    def make(llm=None, **cfg):
        base = dict(retrieval=RetrievalConfig(mode="bm25", k=5, rerank=True), gate_threshold=0.5)
        gen = Generator(llm) if llm else ExtractiveGenerator()
        return Agent(retriever, corpus, links, gen, llm, AgentConfig(**(base | cfg)))

    return make


def test_agent_in_force_and_expand(make_agent):
    a = make_agent(gate=False)
    s = a.search("người lao động báo trước 30 ngày")
    ids = [h.unit_id for h in s["hits"]]
    assert "L0#d37-k1" not in ids  # expired code filtered out
    assert "ND#d7-k1" in ids  # pulled in by the cross-reference to Điều 35 khoản 1
    off = make_agent(gate=False, in_force=False, expand=False).search(
        "người lao động báo trước 30 ngày"
    )
    assert "L0#d37-k1" in [h.unit_id for h in off["hits"]]


def test_agent_gate_abstains_without_llm(make_agent):
    # FakeReranker gives 0.1 unless the passage mentions "quấy rối": below the 0.5 gate.
    s = make_agent().run("thời giờ làm việc")
    assert s["answer"].abstained and s["answer"].text == ABSTAIN_TEXT
    s = make_agent().run("bị quấy rối tình dục có phải báo trước không")
    assert not s["answer"].abstained and s["answer"].citations == ["L1#d35-k2"]


def test_agent_refines_then_abstains(make_agent, fake_llm):
    llm = fake_llm("không dùng tới")
    s = make_agent(llm).run("thời giờ làm việc")
    assert s["answer"].abstained
    assert sum(p.startswith("Câu hỏi:") for p in llm.calls) == 1  # one refine round (max 2)


def test_agent_out_of_scope(make_agent, fake_llm):
    llm = fake_llm("x", analyze={"in_scope": False, "queries": []})
    s = make_agent(llm).run("đăng ký nhãn hiệu thế nào")
    assert s["answer"].abstained and len(llm.calls) == 1


def test_agent_verify_drops_bad_citations(make_agent, fake_llm):
    llm = fake_llm("Không cần báo trước [L1#d35-k2], theo luật cũ [L0#d37-k1] và [X#d1].")
    s = make_agent(llm).run("bị quấy rối tình dục có phải báo trước không")
    assert s["answer"].citations == ["L1#d35-k2"]


def test_agent_verify_retries_then_abstains(make_agent, fake_llm):
    llm = fake_llm("Theo [X#d1].")
    s = make_agent(llm).run("bị quấy rối tình dục có phải báo trước không")
    assert s["answer"].abstained
    assert any("mã không hợp lệ" in p for p in llm.calls)
