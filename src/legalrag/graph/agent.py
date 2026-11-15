"""Agentic RAG as a LangGraph state machine.

    analyze -> retrieve -> expand -> grade --(enough evidence)--> generate -> verify -> END
                  ^                    |                              |
                  +---- refine <-------+ (weak, rounds left)          +-> abstain (no valid cite)
                                       +-> abstain (weak, no rounds left)

Each component can be switched off in `AgentConfig` so its contribution can be measured
(scripts/eval_agent.py). Components that need an LLM (analyze/refine, generate, verify retry)
degrade to deterministic behaviour when no LLM is given, so the retrieval side of the agent can be
evaluated offline.

- analyze: LLM reads the question, decides if it is in scope, extracts the date it is asked at,
  and writes 1-3 search queries (one per legal issue for multi-part questions).
- retrieve: hybrid + rerank per query, restricted to documents in force at `as_of`.
- expand: follows cross-references of the top hits (what they cite, and decree / circular
  provisions that cite them), then reranks the union against the question.
- grade: abstains when the best rerank score is below a threshold tuned on dev questions.
- verify: drops citations that are not in the context or point to expired documents; if nothing
  valid is left, regenerates once with feedback, then abstains.
"""

from __future__ import annotations

import contextlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any, TypedDict

from legalrag.baselines.rag import ABSTAIN_TEXT, Passage, passages, render_context
from legalrag.eval.generation import Answer, extract_citations, is_abstain
from legalrag.eval.metrics import to_article
from legalrag.graph.links import Links, ancestors
from legalrag.retrieval.retriever import Hit, RetrievalConfig, Retriever


@dataclass
class AgentConfig:
    analyze: bool = True  # LLM query analysis + decomposition (skipped without LLM)
    in_force: bool = True
    expand: bool = True
    gate: bool = True
    gate_threshold: float = 0.1
    verify: bool = True
    max_rounds: int = 2  # retrieval rounds, refine needs the LLM
    k: int = 8  # passages given to the generator
    expand_top: int = 4  # hits whose links are followed
    expand_per_hit: int = 6
    retrieval: RetrievalConfig = field(
        default_factory=lambda: RetrievalConfig(mode="hybrid", k=20, rerank=True)
    )


class State(TypedDict, total=False):
    question: str
    as_of: date | None
    queries: list[str]
    in_scope: bool
    rounds: int
    hits: list[Hit]
    top_score: float
    passages: list[Passage]
    draft: str
    retried: bool
    answer: Answer
    trace: list[str]


ANALYZE = """Phân tích câu hỏi pháp luật dưới đây. Corpus chỉ gồm văn bản về: lao động,
bảo hiểm xã hội, hôn nhân và gia đình, giao thông đường bộ, đất đai, thuế thu nhập cá nhân.
Trả về JSON duy nhất:
{{"in_scope": true/false,           // câu hỏi có thuộc các lĩnh vực trên không
  "as_of": "YYYY-MM-DD" hoặc null,  // nếu câu hỏi nêu rõ thời điểm áp dụng
  "queries": ["..."]}}             // 1-3 truy vấn ngắn, mỗi truy vấn một vấn đề pháp lý
CÂU HỎI: {question}"""

REFINE = """Câu hỏi: {question}
Các điều khoản tìm được chưa đủ liên quan:
{found}
Viết lại 1-2 câu truy vấn khác (dùng thuật ngữ pháp lý, từ đồng nghĩa) để tìm đúng điều khoản.
Trả về JSON: {{"queries": ["..."]}}"""

RETRY = """Câu trả lời trước trích dẫn mã không hợp lệ: {bad}.
Chỉ được trích dẫn các mã có trong danh sách ĐIỀU KHOẢN, và chỉ từ văn bản còn hiệu lực.
Hãy trả lời lại."""


def _json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        return json.loads(re.sub(r"//[^\n]*", "", m.group(0))) if m else {}
    except json.JSONDecodeError:
        return {}


class Agent:
    def __init__(
        self,
        retriever: Retriever,
        corpus,
        links: Links | None = None,
        generate: Callable[[str, list[Passage]], str] | None = None,
        complete: Callable[..., str] | None = None,
        cfg: AgentConfig | None = None,
    ):
        """`generate(question, passages)` writes the answer (baselines.rag.Generator or the
        extractive fallback); `complete(prompt, system=None)` is the raw LLM for analyze / refine
        / retry. Without `complete` those steps are skipped."""
        self.retriever, self.corpus, self.links = retriever, corpus, links
        self.generate, self.complete = generate, complete
        self.cfg = cfg or AgentConfig()
        self._owner = self._chunk_owners()
        self.graph = self._build()

    # -- helpers -------------------------------------------------------------------------------

    def _chunk_owners(self) -> dict[str, list[str]]:
        """unit id -> chunk ids holding it (points map to their clause, articles to clauses)."""
        own: dict[str, list[str]] = {}
        for cid, c in self.retriever.chunks.items():
            own.setdefault(c.unit_id, []).append(cid)
            art = to_article(c.unit_id)
            if art != c.unit_id:
                own.setdefault(f"{art}*", []).append(cid)
        return own

    def _chunks_for(self, unit_id: str) -> list[str]:
        if unit_id in self._owner:
            return self._owner[unit_id][:1]
        for a in reversed(ancestors(unit_id)):
            if a in self._owner:
                return self._owner[a][:1]
        return self._owner.get(f"{unit_id}*", [])[:3]  # article split into clauses

    def _rcfg(self, s: State) -> RetrievalConfig:
        return replace(self.cfg.retrieval, in_force_only=self.cfg.in_force, as_of=s.get("as_of"))

    def _allowed(self, s: State) -> set[str] | None:
        return self.corpus.in_force(s.get("as_of")) if self.cfg.in_force else None

    def _rerank(self, question: str, hits: list[Hit]) -> list[Hit]:
        if self.retriever.reranker is None:
            return hits
        return self.retriever.rerank(question, hits)

    # -- nodes ---------------------------------------------------------------------------------

    def analyze(self, s: State) -> dict:
        trace = list(s.get("trace", []))
        if not (self.cfg.analyze and self.complete):
            return {"queries": [s["question"]], "in_scope": True, "rounds": 0, "trace": trace}
        out = _json(self.complete(ANALYZE.format(question=s["question"])))
        queries = [q for q in out.get("queries", []) if isinstance(q, str) and q.strip()][:3]
        upd: dict[str, Any] = {
            "queries": [s["question"], *queries],
            "in_scope": out.get("in_scope", True) is not False,
            "rounds": 0,
        }
        if not s.get("as_of") and out.get("as_of"):
            with contextlib.suppress(TypeError, ValueError):
                upd["as_of"] = date.fromisoformat(out["as_of"])
        trace.append(f"analyze: in_scope={upd['in_scope']} queries={queries}")
        return upd | {"trace": trace}

    def retrieve(self, s: State) -> dict:
        cfg = self._rcfg(s)
        pool: dict[str, Hit] = {h.chunk_id: h for h in s.get("hits", [])}
        for q in s["queries"]:
            for h in self.retriever.candidates(q, cfg, self.retriever.allowed_docs(cfg))[
                : cfg.rerank_candidates
            ]:
                pool.setdefault(h.chunk_id, h)
        hits = list(pool.values())
        hits = self._rerank(s["question"], hits) if cfg.rerank else hits
        hits = hits[: cfg.k]
        trace = s.get("trace", []) + [
            f"retrieve r{s.get('rounds', 0)}: {len(s['queries'])} queries -> "
            f"{[h.unit_id for h in hits[:5]]}"
        ]
        return {"hits": hits, "rounds": s.get("rounds", 0) + 1, "trace": trace}

    def expand(self, s: State) -> dict:
        if not (self.cfg.expand and self.links):
            return {}
        hits = s["hits"]
        allowed = self._allowed(s)
        have = {h.chunk_id for h in hits}
        new: list[Hit] = []
        for h in hits[: self.cfg.expand_top]:
            linked = [("out", u) for u in self.links.outgoing(h.unit_id)] + [
                ("in", u) for u in self.links.incoming(h.unit_id)
            ]
            n = 0
            for rel, u in linked:
                if allowed is not None and u.split("#")[0] not in allowed:
                    continue
                for cid in self._chunks_for(u):
                    if cid not in have:
                        have.add(cid)
                        new.append(self.retriever.hit(cid, 0.0, f"graph:{rel}"))
                        n += 1
                if n >= self.cfg.expand_per_hit:
                    break
        if not new:
            return {}
        if self.cfg.retrieval.rerank and self.retriever.reranker is not None:
            # Rerank scores depend only on (question, passage): score the new passages and merge.
            new = self._rerank(s["question"], new)
            merged = sorted(hits + new, key=lambda h: -h.score)[: self.cfg.retrieval.k]
        else:
            merged = (hits + new)[: self.cfg.retrieval.k]
        added = [h.unit_id for h in merged if h.source.endswith(("graph:in", "graph:out"))]
        return {
            "hits": merged,
            "trace": s.get("trace", []) + [f"expand: +{len(new)} linked, kept {added}"],
        }

    def grade(self, s: State) -> dict:
        top = max((h.score for h in s["hits"]), default=0.0)
        return {"top_score": top, "trace": s.get("trace", []) + [f"grade: top={top:.3f}"]}

    def route_grade(self, s: State) -> str:
        if not s.get("in_scope", True):
            return "abstain"
        if not self.cfg.gate or self.retriever.reranker is None:
            return "generate"
        if s["top_score"] >= self.cfg.gate_threshold:
            return "generate"
        if self.complete and self.cfg.analyze and s["rounds"] < self.cfg.max_rounds:
            return "refine"
        return "abstain"

    def refine(self, s: State) -> dict:
        found = "\n".join(f"- {h.text.splitlines()[0]} | {h.text[:150]}" for h in s["hits"][:5])
        out = _json(self.complete(REFINE.format(question=s["question"], found=found)))
        qs = [q for q in out.get("queries", []) if isinstance(q, str) and q.strip()][:2]
        return {
            "queries": qs or s["queries"],
            "trace": s.get("trace", []) + [f"refine: {qs}"],
        }

    def gen(self, s: State) -> dict:
        ps = passages(s["hits"][: self.cfg.k], self.corpus)
        return {"passages": ps, "draft": self.generate(s["question"], ps)}

    def verify(self, s: State) -> dict:
        ps, draft = s["passages"], s["draft"]
        ans = self._answer(draft, ps)
        if not self.cfg.verify or is_abstain(ans):
            return {"answer": ans}
        ctx = {to_article(p.unit_id) for p in ps} | {p.unit_id for p in ps}
        live = self._allowed(s)
        bad = [
            c
            for c in ans.citations
            if (c not in ctx and to_article(c) not in ctx)
            or (live is not None and c.split("#")[0] not in live)
        ]
        good = [c for c in ans.citations if c not in bad]
        trace = s.get("trace", []) + [f"verify: {len(good)} ok, bad={bad}"]
        if good:
            ans.citations = good
            return {"answer": ans, "trace": trace}
        if self.complete and not s.get("retried"):
            prompt = (
                "ĐIỀU KHOẢN:\n"
                + render_context(ps)
                + f"\n\nCÂU HỎI: {s['question']}\n\n"
                + RETRY.format(bad=", ".join(bad) or "(không có trích dẫn)")
            )
            from legalrag.baselines.rag import SYSTEM

            draft2 = self.complete(prompt, system=SYSTEM)
            return {"draft": draft2, "retried": True, "trace": trace + ["verify: retry"]}
        return {"answer": self._abstain(ps), "trace": trace + ["verify: no valid citation"]}

    def route_verify(self, s: State) -> str:
        return "verify" if "answer" not in s else "end"

    def abstain(self, s: State) -> dict:
        return {"answer": self._abstain(passages(s.get("hits", [])[: self.cfg.k], self.corpus))}

    # -- plumbing ------------------------------------------------------------------------------

    def _answer(self, text: str, ps: list[Passage]) -> Answer:
        ans = Answer(
            text=text,
            citations=extract_citations(text),
            context=[p.unit_id for p in ps],
            context_text=render_context(ps),
        )
        ans.abstained = is_abstain(ans)
        return ans

    def _abstain(self, ps: list[Passage]) -> Answer:
        return Answer(
            text=ABSTAIN_TEXT,
            abstained=True,
            context=[p.unit_id for p in ps],
            context_text=render_context(ps),
        )

    def _build(self):
        from langgraph.graph import END, START, StateGraph

        g = StateGraph(State)
        g.add_node("analyze", self.analyze)
        g.add_node("retrieve", self.retrieve)
        g.add_node("expand", self.expand)
        g.add_node("grade", self.grade)
        g.add_node("refine", self.refine)
        g.add_node("generate", self.gen)
        g.add_node("verify", self.verify)
        g.add_node("abstain", self.abstain)
        g.add_edge(START, "analyze")
        g.add_conditional_edges(
            "analyze", lambda s: "retrieve" if s.get("in_scope", True) else "abstain"
        )
        g.add_edge("retrieve", "expand")
        g.add_edge("expand", "grade")
        g.add_conditional_edges("grade", self.route_grade, ["generate", "refine", "abstain"])
        g.add_edge("refine", "retrieve")
        g.add_edge("generate", "verify")
        g.add_conditional_edges("verify", self.route_verify, {"verify": "verify", "end": END})
        g.add_edge("abstain", END)
        return g.compile()

    def run(self, question: str, as_of: date | None = None) -> State:
        if self.generate is None:
            raise ValueError("Agent needs a generator (baselines.rag.Generator or Extractive)")
        return self.graph.invoke(
            {"question": question, "as_of": as_of, "trace": []}, {"recursion_limit": 30}
        )

    def search(self, question: str, as_of: date | None = None) -> State:
        """Retrieval side only (analyze -> retrieve -> expand -> grade), for retrieval eval."""
        s: State = {"question": question, "as_of": as_of, "trace": []}
        s |= self.analyze(s)
        while True:
            s |= self.retrieve(s)
            s |= self.expand(s)
            s |= self.grade(s)
            route = self.route_grade(s)
            if route != "refine":
                s["route"] = route  # type: ignore[typeddict-unknown-key]
                return s
            s |= self.refine(s)
