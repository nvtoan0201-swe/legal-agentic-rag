import pandas as pd

from legalrag.eval.legal_qa import build_items, explode, map_articles, similarity

ART = "Điều 9. Các hành vi bị nghiêm cấm\n2. Điều khiển phương tiện mà trong máu có nồng độ cồn."


def qa_frame():
    pair = {
        "question": "Theo Điều 9, có được lái xe khi có cồn?",
        "answer": "Không.",
        "question_type": "factual",
        "difficulty": "easy",
    }
    return pd.DataFrame(
        {
            "doc_name": [
                "Luật Trật tự, an toàn giao thông đường bộ của Quốc hội, số 36/2024/QH15",
                "Luật sửa đổi Luật Đất đai số 31/2024/QH15 của Quốc hội, số 43/2024/QH15",
                "Dự thảo Luật Đường bộ",
                "Luật Lưu trữ của Quốc hội, số 33/2024/QH15",
                "Luật X của Quốc hội, số 36/2024/QH15",
            ],
            "doc_type_name": ["Luật"] * 5,
            "article_content": [
                ART,
                "Điều 1. Sửa đổi ...",
                "Điều 1. ...",
                "Điều 2. Lưu trữ ...",
                "Điều 9. Một nội dung hoàn toàn khác về thuế tài nguyên khoáng sản.",
            ],
            "generated_qa_pairs": [[pair]] * 5,
            "generation_time": [1.0] * 5,
        }
    )


def corpus():
    docs = pd.DataFrame(
        {
            "doc_key": ["36/2024/QH15", "43/2024/QH15"],
            "core": [True, False],
            "status": ["in_force", "in_force"],
            "title": ["Trật tự, an toàn giao thông đường bộ", "L"],
            "domains": [["giao_thong_duong_bo"], ["dat_dai"]],
        }
    )
    art_text = {"36/2024/QH15#d9": ART, "43/2024/QH15#d1": "Điều 1. Sửa đổi ..."}
    return docs, art_text


def test_number_is_taken_from_the_end_of_doc_name():
    p = explode(qa_frame())
    assert p["so_ky_hieu"].tolist()[:2] == ["36/2024/QH15", "43/2024/QH15"]


def test_mapping_statuses_and_items():
    docs, art_text = corpus()
    m = map_articles(explode(qa_frame()), docs, art_text)
    assert m["match"].tolist() == [
        "ok",
        "not_core",
        "draft_law",
        "not_in_corpus",
        "content_mismatch",
    ]
    items = build_items(m, docs, {}, n_out_of_scope=5)
    cats = sorted((i.category.value, tuple(i.gold_articles)) for i in items)
    assert cats == [("out_of_scope", ()), ("single_hop", ("36/2024/QH15#d9",))]
    sh = next(i for i in items if i.category.value == "single_hop")
    assert sh.meta["mentions_article"] and sh.domain == "giao_thong_duong_bo"


def test_similarity():
    assert similarity(ART, ART + " thêm") == 1.0
    assert similarity("a b c", "x y z") == 0.0
