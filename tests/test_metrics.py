import math

import pytest

from legalrag.eval.metrics import evaluate_retrieval, mrr, ndcg_at_k, recall_at_k, to_article
from legalrag.eval.schema import EvalItem


@pytest.mark.parametrize(
    ("uid", "art"),
    [
        ("45/2019/QH14#d35-k2-a", "45/2019/QH14#d35"),
        ("45/2019/QH14#d49a-k1", "45/2019/QH14#d49a"),
        ("X#kt1-d3-k1", "X#kt1-d3"),
        ("X#pl2", "X#pl2"),
        ("X#body", "X#body"),
    ],
)
def test_to_article(uid, art):
    assert to_article(uid) == art


def test_clauses_of_same_article_count_once():
    got = ["L#d35-k1", "L#d35-k2", "L#d36", "L#d40"]
    assert recall_at_k(got, ["L#d36"], k=2) == 1.0  # d35 collapses, d36 is 2nd
    assert recall_at_k(got, ["L#d36"], k=2, level="unit") == 0.0
    assert mrr(got, ["L#d40"]) == pytest.approx(1 / 3)


def test_ndcg():
    assert ndcg_at_k(["a#d1", "a#d2"], ["a#d1"], 5) == 1.0
    assert ndcg_at_k(["a#d2", "a#d1"], ["a#d1"], 5) == pytest.approx(1 / math.log2(3))
    assert ndcg_at_k(["a#d9"], ["a#d1", "a#d2"], 5) == 0.0
    assert math.isnan(recall_at_k(["a#d1"], [], 5))


def test_evaluate_retrieval_skips_items_without_gold():
    items = [
        EvalItem(
            id="1",
            question="q1",
            category="single_hop",
            expected_behavior="answer",
            gold_articles=["L#d1-k2"],
            source="t",
        ),
        EvalItem(
            id="2", question="q2", category="out_of_scope", expected_behavior="abstain", source="t"
        ),
    ]
    res = evaluate_retrieval(items, lambda q: ["L#d5", "L#d1"], ks=(1, 5))
    assert res["n"] == 1
    s = res["summary"]["all"]
    assert (s["recall@1"], s["recall@5"], s["mrr"]) == (0.0, 1.0, 0.5)
