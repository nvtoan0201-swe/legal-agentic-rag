import json

from legalrag.eval.generation import (
    Answer,
    LLMJudge,
    abstention_scores,
    citation_scores,
    evaluate_answers,
    extract_citations,
)
from legalrag.eval.schema import EvalItem


def item(**kw):
    base = dict(
        id="1",
        question="q",
        category="single_hop",
        expected_behavior="answer",
        gold_articles=["36/2024/QH15#d9-k2"],
        source="t",
    )
    return EvalItem(**(base | kw))


def test_extract_citations_ids_and_text():
    text = (
        "Theo [36/2024/QH15#d9-k2] và điểm đ khoản 2 Điều 35 Bộ luật Lao động số 45/2019/QH14, ..."
    )
    assert extract_citations(text) == ["36/2024/QH15#d9-k2", "45/2019/QH14#d35-k2-dd"]


def test_citation_scores_article_level_and_forbidden():
    it = item(forbidden_articles=["23/2008/QH12#d8-k8"])
    s = citation_scores(
        ["36/2024/QH15#d9", "23/2008/QH12#d8-k1"],
        it,
        status_of=lambda k: "expired" if k == "23/2008/QH12" else "in_force",
    )
    assert s["cite_precision"] == 0.5
    assert s["cite_recall"] == 1.0
    assert s["cites_forbidden"] == 1.0  # same article d8
    assert s["cites_expired"] == 1.0


def test_abstention():
    oos = item(id="2", category="out_of_scope", expected_behavior="abstain", gold_articles=[])
    pairs = [
        (oos, Answer("Tôi không đủ căn cứ để trả lời câu hỏi này.")),
        (item(), Answer("Có vi phạm [36/2024/QH15#d9-k2].")),
        (item(id="3"), Answer("x", abstained=True)),
    ]
    s = abstention_scores(pairs)
    assert s["abstain_recall"] == 1.0
    assert s["abstain_precision"] == 0.5
    assert s["over_abstain_rate"] == 0.5


def test_evaluate_answers_with_fake_judge():
    def fake(prompt):
        return json.dumps({"score": 1, "reason": "ok", "unsupported": []})

    it = item(gold_answer="Có vi phạm.")
    res = evaluate_answers(
        [it],
        lambda i: Answer("Có vi phạm [36/2024/QH15#d9-k2].", context_text="..."),
        judge=LLMJudge(fake),
    )
    row = res["rows"][0]
    assert row["correctness"] == 1.0 and row["faithfulness"] == 1.0
    assert res["summary"]["all"]["cite_recall"] == 1.0
