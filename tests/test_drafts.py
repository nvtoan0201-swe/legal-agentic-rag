import json

import pandas as pd

from legalrag.eval.drafts import draft_item, guide_pairs, law_name, version_pairs


def test_law_name():
    assert law_name("Bộ Luật lao động số 45/2019/QH14") == "Bộ Luật lao động"
    assert law_name("Đất đai") == "Luật Đất đai"


def corpus():
    docs = pd.DataFrame(
        {
            "doc_key": ["L1", "ND", "L0"],
            "title": [
                "Luật Hôn nhân và gia đình số L1",
                "Nghị định hướng dẫn",
                "Luật Hôn nhân và gia đình số L0",
            ],
            "loai_van_ban": ["Luật", "Nghị định", "Luật"],
            "status": ["in_force", "in_force", "expired"],
            "core": [True, True, True],
            "domains": [["hon_nhan_gia_dinh"]] * 3,
        }
    )
    units = pd.DataFrame(
        [
            ("L1#d34", "L1", "dieu", "Đăng ký tài sản chung", "Điều 34. Đăng ký tài sản chung", 0),
            ("L1#d34-k1", "L1", "khoan", "", "1. Phải ghi tên cả hai vợ chồng.", 1),
            ("ND#d12", "ND", "dieu", "Đăng ký", "Điều 12. Đăng ký", 0),
            (
                "ND#d12-k1",
                "ND",
                "khoan",
                "",
                "1. Tài sản theo khoản 1 Điều 34 của Luật Hôn nhân và gia đình.",
                1,
            ),
            ("L0#d27", "L0", "dieu", "Đăng ký tài sản chung", "Điều 27. Đăng ký tài sản chung", 0),
            ("L0#d27-k1", "L0", "khoan", "", "1. Ghi tên một người cũng được.", 1),
        ],
        columns=["unit_id", "doc_key", "kind", "title", "text", "ordinal"],
    )
    rels = pd.DataFrame(
        {
            "actor_key": ["ND", "L1"],
            "target_key": ["L1", "L0"],
            "rel": ["guides", "replaces"],
            "suspect": [False, False],
        }
    )
    return docs, units, rels


def test_guide_pairs_follow_explicit_citations():
    pairs = guide_pairs(*corpus())
    assert [(p.a, p.b) for p in pairs] == [("L1#d34-k1", "ND#d12")]
    assert "Phải ghi tên cả hai" in pairs[0].a_text


def test_version_pairs_match_titles_with_changed_text():
    pairs = version_pairs(*corpus())
    assert [(p.a, p.b) for p in pairs] == [("L0#d27", "L1#d34")]


def test_draft_item_with_fake_llm():
    p = version_pairs(*corpus())[0]

    def fake(prompt):
        return (
            "```json\n"
            + json.dumps({"question": "Q?", "answer": "A [L1#d34]", "difference": "d"})
            + "\n```"
        )

    it = draft_item(p, fake, 0)
    assert it.category.value == "expired" and it.gold_articles == ["L1#d34"]
    assert it.forbidden_articles == ["L0#d27"] and not it.reviewed
