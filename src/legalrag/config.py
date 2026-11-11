"""Cấu hình đọc từ biến môi trường / file .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_base_url: str = "http://localhost:8000/v1"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""

    postgres_dsn: str = "postgresql://legalrag:legalrag@localhost:5432/legalrag"
    qdrant_url: str = "http://localhost:6333"

    data_dir: str = "data"
    hf_corpus: str = "th1nhng0/vietnamese-legal-documents"
    hf_qa: str = "thangvip/vietnamese-legal-qa"


settings = Settings()
