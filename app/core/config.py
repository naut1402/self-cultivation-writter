"""App configuration. Loads from environment / .env and exports provider keys
into os.environ so LiteLLM can pick them up."""

from __future__ import annotations

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # v0: local SQLite. v1: swap to a Postgres URL with no code change.
    database_url: str = "sqlite:///./scw.db"

    # Provider keys — only the one(s) you use are required.
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    openrouter_api_key: str | None = None

    # OpenAI-compatible endpoints (LM Studio, vLLM, Groq, Together, DeepSeek-direct, …):
    # use an `openai/<model>` slug and point here.
    openai_base_url: str | None = None
    # Local Ollama: use an `ollama_chat/<model>` slug.
    ollama_base_url: str = "http://localhost:11434"


settings = Settings()

# LiteLLM reads credentials from os.environ; mirror the loaded settings there.
for _name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY"):
    _val = getattr(settings, _name.lower(), None)
    if _val:
        os.environ.setdefault(_name, _val)
