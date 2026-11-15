"""Non-agentic RAG baseline: retrieve top-k once, stuff the passages into one prompt, answer.

No query rewriting, no effect-status filter, no cross-reference expansion, no evidence gate and
no citation check. Every agent component is measured against this.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from legalrag.eval.generation import Answer, extract_citations, is_abstain
from legalrag.retrieval.retriever import Hit, RetrievalConfig, Retriever

ABSTAIN_TEXT = "Không đủ căn cứ trong các văn bản được cung cấp để trả lời câu hỏi này."

SYSTEM = f"""Bạn là trợ lý tra cứu pháp luật Việt Nam. Chỉ dựa vào các ĐIỀU KHOẢN được cung cấp.
Quy tắc:
- Trả lời ngắn gọn, đúng trọng tâm câu hỏi, bằng tiếng Việt.
- Mỗi ý pháp lý phải kèm trích dẫn đúng mã điều khoản trong ngoặc vuông,
  ví dụ [45/2019/QH14#d35-k1].
  Chỉ dùng mã có trong danh sách được cung cấp, không tự đặt mã.
- Ưu tiên văn bản còn hiệu lực; nếu điều khoản thuộc văn bản đã hết hiệu lực thì nói rõ.
- Nếu các điều khoản không đủ căn cứ để trả lời, chỉ trả lời đúng câu: "{ABSTAIN_TEXT}"
"""

USER = """ĐIỀU KHOẢN:
{context}

CÂU HỎI: {question}"""


@dataclass
class Passage:
    unit_id: str
    label: str  # document label + effect status
    text: str

    def render(self) -> str:
        return f"[{self.unit_id}] {self.label}\n{self.text}"


def passages(hits: Sequence[Hit], corpus=None, max_chars: int = 2500) -> list[Passage]:
    """One passage per cited unit (several chunks of a unit collapse), with status in the label."""
    out, seen = [], set()
    for h in hits:
        if h.unit_id in seen:
            continue
        seen.add(h.unit_id)
        label, text = h.text.split("\n", 1) if "\n" in h.text else ("", h.text)
        if corpus is not None:
            st = corpus.status(h.doc_key)
            if st and st != "in_force":
                label += " — ĐÃ HẾT HIỆU LỰC" if st == "expired" else f" — {st}"
            full = corpus.passage(h.unit_id)
            text = full if full and len(full) <= max_chars else text
        out.append(Passage(h.unit_id, label, text[:max_chars]))
    return out


def render_context(ps: Sequence[Passage]) -> str:
    return "\n\n".join(p.render() for p in ps)


class Generator:
    """Answer from passages with an LLM: `complete(prompt, system=...) -> str`."""

    def __init__(self, complete: Callable[..., str]):
        self.complete = complete

    def __call__(self, question: str, ps: Sequence[Passage]) -> str:
        if not ps:
            return ABSTAIN_TEXT
        return self.complete(
            USER.format(context=render_context(ps), question=question), system=SYSTEM
        )


class ExtractiveGenerator:
    """No-LLM fallback for demos and offline runs: quote the best passage with its citation.

    Not a real answer generator; it only shows what the retriever found.
    """

    def __init__(self, n: int = 1):
        self.n = n

    def __call__(self, question: str, ps: Sequence[Passage]) -> str:
        if not ps:
            return ABSTAIN_TEXT
        return "\n\n".join(f"Theo {p.label} [{p.unit_id}]:\n{p.text}" for p in ps[: self.n])


@dataclass
class RAGResult:
    answer: Answer
    hits: list[Hit] = field(default_factory=list)


class NaiveRAG:
    def __init__(
        self,
        retriever: Retriever,
        generate: Callable[[str, Sequence[Passage]], str],
        corpus=None,
        cfg: RetrievalConfig | None = None,
    ):
        self.retriever, self.generate, self.corpus = retriever, generate, corpus
        self.cfg = cfg or RetrievalConfig(mode="hybrid", k=8, rerank=True)

    def run(self, question: str) -> RAGResult:
        hits = self.retriever.search(question, self.cfg)
        ps = passages(hits, self.corpus)
        text = self.generate(question, ps)
        cited = extract_citations(text)
        ans = Answer(
            text=text,
            citations=cited,
            context=[p.unit_id for p in ps],
            context_text=render_context(ps),
        )
        ans.abstained = is_abstain(ans)
        return RAGResult(ans, hits)
