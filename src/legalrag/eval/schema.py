"""Canonical eval item format (one JSON object per line)."""

from __future__ import annotations

import json
from datetime import date
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

UNIT_ID = r"^[^#\s]+#[a-z0-9\-_.đ]+$"


class Category(StrEnum):
    SINGLE_HOP = "single_hop"  # one provision answers the question
    MULTI_HOP = "multi_hop"  # needs >= 2 provisions, usually a law + its guiding decree/circular
    EXPIRED = "expired"  # the obvious provision is from an expired document
    OUT_OF_SCOPE = "out_of_scope"  # not covered by the corpus: the system must abstain


class Behavior(StrEnum):
    ANSWER = "answer"
    ABSTAIN = "abstain"
    # For EXPIRED items: answer from the current document, or say that the asked one has expired.
    ANSWER_CURRENT = "answer_current"


class EvalItem(BaseModel):
    id: str
    question: str
    category: Category
    expected_behavior: Behavior
    gold_articles: list[str] = Field(
        default_factory=list, description="unit ids, e.g. 45/2019/QH14#d35-k2"
    )
    gold_answer: str | None = None
    # Provisions that must NOT be cited as the current rule (e.g. articles of an expired law).
    forbidden_articles: list[str] = Field(default_factory=list)
    domain: str | None = None
    as_of: date | None = Field(None, description="date the question is asked at (effect status)")
    source: str  # thangvip/vietnamese-legal-qa | manual | llm_draft
    reviewed: bool = False
    notes: str = ""
    meta: dict = Field(default_factory=dict)

    @field_validator("gold_articles", "forbidden_articles")
    @classmethod
    def _unit_ids(cls, v: list[str]) -> list[str]:
        import re

        bad = [x for x in v if not re.match(UNIT_ID, x)]
        if bad:
            raise ValueError(f"not unit ids: {bad}")
        return v


def read_jsonl(path: Path) -> list[EvalItem]:
    items = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip() and not line.lstrip().startswith("//"):
            try:
                items.append(EvalItem.model_validate_json(line))
            except ValueError as e:
                raise ValueError(f"{path}:{n}: {e}") from e
    return items


def write_jsonl(items: list[EvalItem], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(
                json.dumps(it.model_dump(mode="json", exclude_defaults=False), ensure_ascii=False)
                + "\n"
            )
