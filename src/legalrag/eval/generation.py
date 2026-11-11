"""Answer-level metrics: citation accuracy, abstention, and LLM-judged correctness/faithfulness.

The system under test returns an `Answer`: text, cited unit ids, whether it abstained, and the
unit ids it retrieved (context). Citation and abstention metrics are deterministic; correctness
and faithfulness use an LLM judge (any OpenAI-compatible endpoint).
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from legalrag.eval.metrics import to_article
from legalrag.eval.schema import Behavior, EvalItem

# "[45/2019/QH14#d35-k2]" style citations, the format the system is asked to produce.
RE_CITE_ID = re.compile(r"\[([^\[\]\s]+#[a-z0-9\-_.đ]+)\]")
# Natural-language fallback: "khoản 2 Điều 35 Bộ luật Lao động số 45/2019/QH14".
RE_CITE_TEXT = re.compile(
    r"(?:điểm\s+([a-zđ])\s*,?\s*)?(?:khoản\s+(\d+)\s*,?\s*)?Điều\s+(\d+[a-zđ]?)"
    r"[^.;\n\[\]]{0,120}?(\d+/\d{4}/[A-ZĐ0-9\-]+)",
    re.IGNORECASE,
)
ABSTAIN_PHRASES = re.compile(
    r"không đủ căn cứ|không tìm thấy (?:quy định|căn cứ|thông tin)|nằm ngoài phạm vi|"
    r"không thể trả lời|chưa có đủ thông tin",
    re.IGNORECASE,
)


@dataclass
class Answer:
    text: str
    citations: list[str] = field(default_factory=list)
    abstained: bool | None = None  # None: infer from text
    context: list[str] = field(default_factory=list)
    context_text: str = ""


def extract_citations(text: str) -> list[str]:
    out = RE_CITE_ID.findall(text)
    for diem, khoan, dieu, so in RE_CITE_TEXT.findall(text):
        uid = f"{so}#d{dieu.lower()}"
        if khoan:
            uid += f"-k{khoan}"
            if diem:
                uid += "-" + ("dd" if diem.lower() == "đ" else diem.lower())
        out.append(uid)
    return list(dict.fromkeys(out))


def is_abstain(ans: Answer) -> bool:
    return ans.abstained if ans.abstained is not None else bool(ABSTAIN_PHRASES.search(ans.text))


def citation_scores(
    cited: Sequence[str],
    item: EvalItem,
    status_of: Callable[[str], str | None] | None = None,
) -> dict:
    """Article-level precision/recall of citations, plus citing forbidden or expired documents."""
    c = {to_article(x) for x in cited}
    g = {to_article(x) for x in item.gold_articles}
    f = {to_article(x) for x in item.forbidden_articles}
    out = {
        "n_cited": float(len(c)),
        "cite_precision": len(c & g) / len(c) if c else float("nan"),
        "cite_recall": len(c & g) / len(g) if g else float("nan"),
        "cites_forbidden": float(bool(c & f)),
    }
    if status_of is not None:
        out["cites_expired"] = float(any(status_of(x.split("#")[0]) == "expired" for x in c))
    return out


def abstention_scores(pairs: Sequence[tuple[EvalItem, Answer]]) -> dict:
    """Abstain precision/recall/F1 where the positive class is 'should abstain'."""
    tp = fp = fn = tn = 0
    for it, ans in pairs:
        should = it.expected_behavior == Behavior.ABSTAIN
        did = is_abstain(ans)
        tp += should and did
        fp += (not should) and did
        fn += should and not did
        tn += (not should) and not did
    p = tp / (tp + fp) if tp + fp else float("nan")
    r = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * p * r / (p + r) if p == p and r == r and p + r else float("nan")
    acc = (tp + tn) / len(pairs) if pairs else float("nan")
    return {
        "abstain_precision": p,
        "abstain_recall": r,
        "abstain_f1": f1,
        "abstain_accuracy": acc,
        "over_abstain_rate": fp / (fp + tn) if fp + tn else float("nan"),
    }


JUDGE_CORRECTNESS = """Bạn là giám khảo pháp lý. So sánh CÂU TRẢ LỜI với ĐÁP ÁN THAM KHẢO.
Chấm "score" từ 0 đến 1: 1 = đúng và đủ các ý pháp lý chính; 0.5 = đúng một phần hoặc thiếu
ý quan trọng; 0 = sai hoặc mâu thuẫn.
Chỉ trả về JSON: {{"score": <số>, "reason": "<ngắn gọn>"}}.

CÂU HỎI: {question}
ĐÁP ÁN THAM KHẢO: {gold}
CÂU TRẢ LỜI: {answer}"""

JUDGE_FAITHFULNESS = """Bạn kiểm tra tính trung thực. Mỗi khẳng định pháp lý trong CÂU TRẢ LỜI
phải được NGỮ CẢNH (các điều khoản đã truy xuất) hỗ trợ trực tiếp.
"score" = tỉ lệ khẳng định được hỗ trợ (0..1).
Chỉ trả về JSON: {{"score": <số>, "unsupported": ["<khẳng định không có căn cứ>"]}}.

NGỮ CẢNH:
{context}

CÂU TRẢ LỜI: {answer}"""


def _parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"judge did not return JSON: {text[:200]}")
    return json.loads(m.group(0))


class LLMJudge:
    """`complete(prompt) -> str` is any LLM call, e.g. legalrag.llm.complete."""

    def __init__(self, complete: Callable[[str], str]):
        self.complete = complete

    def correctness(self, item: EvalItem, ans: Answer) -> dict:
        if not item.gold_answer:
            return {"correctness": float("nan")}
        out = _parse_json(
            self.complete(
                JUDGE_CORRECTNESS.format(
                    question=item.question, gold=item.gold_answer, answer=ans.text
                )
            )
        )
        return {"correctness": float(out["score"]), "correctness_reason": out.get("reason", "")}

    def faithfulness(self, ans: Answer) -> dict:
        if not ans.context_text:
            return {"faithfulness": float("nan")}
        out = _parse_json(
            self.complete(JUDGE_FAITHFULNESS.format(context=ans.context_text, answer=ans.text))
        )
        return {"faithfulness": float(out["score"]), "unsupported": out.get("unsupported", [])}


def evaluate_answers(
    items: Sequence[EvalItem],
    answer: Callable[[EvalItem], Answer],
    judge: LLMJudge | None = None,
    status_of: Callable[[str], str | None] | None = None,
) -> dict:
    from legalrag.eval.metrics import summarize

    rows, pairs = [], []
    for it in items:
        ans = answer(it)
        pairs.append((it, ans))
        cited = ans.citations or extract_citations(ans.text)
        row = {"id": it.id, "category": it.category.value, "abstained": float(is_abstain(ans))}
        row |= citation_scores(cited, it, status_of)
        if judge is not None and it.expected_behavior != Behavior.ABSTAIN:
            row |= judge.correctness(it, ans)
            row |= judge.faithfulness(ans)
        rows.append(row)
    clean = [
        {k: v for k, v in r.items() if not isinstance(v, (str, list)) or k in ("id", "category")}
        for r in rows
    ]
    return {"summary": summarize(clean), "abstention": abstention_scores(pairs), "rows": rows}
