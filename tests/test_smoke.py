from legalrag import __version__
from legalrag.config import Settings


def test_version():
    assert __version__ == "0.1.0"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "test-model")
    assert Settings().llm_model == "test-model"
