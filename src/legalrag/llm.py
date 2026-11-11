"""Minimal client for an OpenAI-compatible chat endpoint (LLM_BASE_URL, LLM_MODEL, LLM_API_KEY)."""

from __future__ import annotations

from functools import lru_cache

from legalrag.config import settings


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI

    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key or "none")


def complete(prompt: str, system: str | None = None, temperature: float = 0.0, **kw) -> str:
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    resp = _client().chat.completions.create(
        model=settings.llm_model, messages=messages, temperature=temperature, **kw
    )
    return resp.choices[0].message.content or ""
