"""
Enterprise Application Configuration.

This module provides a centralized, strongly typed, immutable configuration
system for the Telecom Support Agent.

Features
--------
- Pydantic Settings V2
- Nested configuration using env_nested_delimiter
- Strong typing using Enums and Literals
- Immutable configuration models
- Secret management using SecretStr
- Cross-field validation
- Cached singleton configuration

Environment Variable Convention
-------------------------------
APP__NAME=Telecom Support Agent
DATABASE__URL=postgresql://user:password@localhost:5432/telecom
AZURE__API_KEY=xxxxxxxxxxxxxxxx
RAG__CHUNK_SIZE=1024
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


# ==============================================================================
# Enums
# ==============================================================================


class EnvironmentType(str, Enum):
    """Supported application environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Supported logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ==============================================================================
# Configuration Models
# ==============================================================================


class AppSettings(BaseModel):
    """Application configuration."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(
        default="Telecom Support Agent",
        description="Application name.",
    )

    version: str = Field(
        default="1.0.0",
        description="Application version.",
    )

    environment: EnvironmentType = Field(
        default=EnvironmentType.DEVELOPMENT,
        description="Application runtime environment.",
    )

    debug: bool = Field(
        default=False,
        description="Enable debug mode.",
    )


class APISettings(BaseModel):
    """FastAPI server configuration."""

    model_config = ConfigDict(frozen=True)

    host: str = Field(
        default="0.0.0.0",
        description="Host address.",
    )

    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Listening port.",
    )

    prefix: str = Field(
        default="/api/v1",
        description="API route prefix.",
    )


class DatabaseSettings(BaseModel):
    """Database configuration."""

    model_config = ConfigDict(frozen=True)

    url: str = Field(
        description="Database connection string.",
    )

    echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging.",
    )


class AzureSettings(BaseModel):
    """Azure AI Foundry configuration."""

    model_config = ConfigDict(frozen=True)

    endpoint: str = Field(
        description="Azure AI endpoint.",
    )

    api_key: SecretStr = Field(
        description="Azure API Key.",
    )

    chat_model: str = Field(
        description="Azure chat deployment name.",
    )

    api_version: str = Field(
        default="2024-05-01-preview",
        description="Azure API version.",
    )


class GroqSettings(BaseModel):
    """Groq LLM configuration."""

    model_config = ConfigDict(frozen=True)

    api_key: SecretStr = Field(
        description="Groq API Key.",
    )

    chat_model: str = Field(
        description="Groq model name.",
    )


class EmbeddingSettings(BaseModel):
    """Embedding model configuration."""

    model_config = ConfigDict(frozen=True)

    model_name: str = Field(
        description="Embedding model name.",
    )

    device: Literal["cpu", "cuda", "mps"] = Field(
        default="cpu",
        description="Execution device.",
    )

    normalize_embeddings: bool = Field(
        default=True,
        description="Normalize embedding vectors.",
    )

    batch_size: int = Field(
        default=32,
        gt=0,
        description="Embedding batch size.",
    )


class RAGSettings(BaseModel):
    """Retrieval-Augmented Generation configuration."""

    model_config = ConfigDict(frozen=True)

    chunk_size: int = Field(
        gt=0,
        description="Chunk size.",
    )

    chunk_overlap: int = Field(
        ge=0,
        description="Chunk overlap.",
    )

    top_k: int = Field(
        gt=0,
        description="Number of retrieved documents.",
    )

    vector_index_path: Path = Field(
        description="FAISS index directory.",
    )

    bm25_index_path: Path = Field(
        description="BM25 index directory.",
    )

    @model_validator(mode="after")
    def validate_chunk_overlap(self):
        """
        Ensure overlap is smaller than chunk size.
        """

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        return self

class LoggingSettings(BaseModel):
    """Application logging configuration."""

    model_config = ConfigDict(frozen=True)

    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level.",
    )

    json_logs: bool = Field(
        default=True,
        description="Enable JSON formatted logs.",
    )


class SecuritySettings(BaseModel):
    """Security configuration."""

    model_config = ConfigDict(frozen=True)

    api_key: SecretStr = Field(
        description="Application API key.",
    )

    rate_limit_per_minute: int = Field(
        default=60,
        gt=0,
        description="Maximum requests allowed per minute.",
    )


# ==============================================================================
# Root Settings
# ==============================================================================


class Settings(BaseSettings):
    """
    Root application settings.

    Environment variables are automatically mapped into nested configuration
    models using the '__' delimiter.

    Example
    -------
    APP__NAME=Telecom Support Agent
    DATABASE__URL=postgresql://...
    AZURE__API_KEY=xxxx
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    app: AppSettings = Field(default_factory=AppSettings)
    api: APISettings = Field(default_factory=APISettings)
    database: DatabaseSettings
    azure: AzureSettings
    groq: GroqSettings
    embedding: EmbeddingSettings
    rag: RAGSettings
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings


# ==============================================================================
# Cached Settings Instance
# ==============================================================================


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns the application settings.

    The configuration is loaded only once during the application's lifetime,
    making repeated imports inexpensive.
    """

    # type: ignore tells the IDE to stop complaining about missing constructor 
    # arguments, because Pydantic handles the injection dynamically at runtime.
    return Settings() # type: ignore


# Global singleton instance
settings = get_settings()