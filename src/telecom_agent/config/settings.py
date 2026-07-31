"""Pydantic Settings — fails fast on obviously broken configuration.

Every environment variable the app reads is declared here with a default. The app
factory calls :func:`get_settings` once and dependency-injects the result; nothing
reads ``os.environ`` directly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from telecom_agent.core.enums import Provider


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------- app ----------
    app_env: Literal["local", "dev", "prod"] = "local"
    api_key: str = "dev-key-change-me"
    log_level: str = "INFO"

    # ---------- LLM routing ----------
    llm_provider: Literal["azure_foundry", "groq", "fake"] = "fake"
    llm_failover_enabled: bool = True
    llm_breaker_cooldown_seconds: int = 60
    llm_request_timeout_seconds: int = 20
    session_token_budget: int = 12_000

    # ---------- Azure AI Foundry (primary) ----------
    azure_ai_endpoint: str = "https://example.services.ai.azure.com/models"
    azure_ai_api_key: str = ""
    azure_ai_deployment_chat_main: str = "chat-main"
    azure_ai_deployment_chat_mini: str = "chat-mini"
    azure_ai_deployment_embed: str = "embed"

    # ---------- Groq (backup) ----------
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_api_key: str = ""
    groq_model_chat_main: str = "openai/gpt-oss-120b"
    groq_model_chat_mini: str = "llama-3.1-8b-instant"

    # ---------- data ----------
    kb_dir: str = "./data/kb"
    index_dir: str = "./data/index"
    database_url: str = "sqlite:///./data/app.db"
    auto_ingest: bool = True  # build the index on first startup if missing (dev convenience)
    retrieval_top_k: int = 8
    retrieval_score_floor: float = 0.35

    # ---------- thresholds (mirrors agent/policies/thresholds.py defaults) ----------
    clarify_confidence_floor: float = 0.60
    groundedness_floor: float = 0.75
    max_verify_attempts: int = 2

    # ---------- prompt versions ----------
    classifier_version: str = "v2"
    answer_version: str = "v1"
    verifier_version: str = "v1"
    system_version: str = "base"

    # ---------- observability ----------
    applicationinsights_connection_string: str = Field(default="")

    # ---------- ui ----------
    api_base_url: str = "http://localhost:8000"

    # ---------- derived helpers ----------
    @property
    def default_provider(self) -> Provider:
        return {
            "azure_foundry": Provider.AZURE_FOUNDRY,
            "groq": Provider.GROQ,
            "fake": Provider.FAKE,
        }[self.llm_provider]

    @property
    def telemetry_enabled(self) -> bool:
        return bool(self.applicationinsights_connection_string)


@lru_cache
def get_settings() -> Settings:
    """Cached so the whole process shares one immutable Settings instance."""
    return Settings()