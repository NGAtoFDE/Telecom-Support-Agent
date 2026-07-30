"""
Shared enumerations used throughout the Telecom Support Agent.

This module defines application-wide enumerations shared across multiple
layers of the application. These enums provide type safety, eliminate
hardcoded string literals, and improve code readability.

Guidelines
----------
- Use StrEnum + auto() for readable string values.
- Keep enums lightweight and dependency-free.
- Shared enums may represent infrastructure or domain concepts when
  they are used across multiple application layers.
- Requires Python 3.11+.
"""

from enum import StrEnum, auto


# ==============================================================================
# Application
# ==============================================================================


class Environment(StrEnum):
    """Supported application environments."""

    DEVELOPMENT = auto()
    TESTING = auto()
    STAGING = auto()
    PRODUCTION = auto()


# ==============================================================================
# AI Providers
# ==============================================================================


class LLMProvider(StrEnum):
    """Supported Large Language Model providers."""

    AZURE = auto()
    GROQ = auto()


class EmbeddingProvider(StrEnum):
    """Supported embedding model providers."""

    HUGGINGFACE = auto()


class ComputeDevice(StrEnum):
    """Supported inference devices."""

    CPU = auto()
    CUDA = auto()
    MPS = auto()


# ==============================================================================
# Retrieval
# ==============================================================================


class VectorStoreType(StrEnum):
    """Supported vector store implementations."""

    FAISS = auto()


class RetrieverType(StrEnum):
    """Supported document retrieval strategies."""

    VECTOR = auto()
    BM25 = auto()
    HYBRID = auto()


# ==============================================================================
# Conversation
# ==============================================================================


class MessageRole(StrEnum):
    """Supported chat message roles."""

    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()
    TOOL = auto()


class ResponseStatus(StrEnum):
    """Response execution status."""

    SUCCESS = auto()
    PARTIAL_SUCCESS = auto()
    ERROR = auto()


# ==============================================================================
# Telecom Domain
# ==============================================================================


class IssueCategory(StrEnum):
    """Supported customer issue categories."""

    BILLING = auto()
    NETWORK = auto()
    SIM = auto()
    DEVICE = auto()
    RECHARGE = auto()
    ROAMING = auto()
    UNKNOWN = auto()


class Priority(StrEnum):
    """Support ticket priority."""

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class EscalationQueue(StrEnum):
    """Support escalation queues."""

    L1 = auto()
    L2 = auto()
    L3 = auto()


# ==============================================================================
# Documents
# ==============================================================================


class DocumentType(StrEnum):
    """Supported knowledge base document formats."""

    PDF = auto()
    DOCX = auto()
    TXT = auto()
    HTML = auto()
    CSV = auto()
    JSON = auto()

    # Explicit value because auto() would generate "markdown"
    MARKDOWN = "md"


# ==============================================================================
# Logging
# ==============================================================================


class LogFormat(StrEnum):
    """Supported logging formats."""

    JSON = auto()
    TEXT = auto()


# ==============================================================================
# Health
# ==============================================================================


class HealthStatus(StrEnum):
    """Application health status."""

    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()


__all__ = [
    "Environment",
    "LLMProvider",
    "EmbeddingProvider",
    "ComputeDevice",
    "VectorStoreType",
    "RetrieverType",
    "MessageRole",
    "ResponseStatus",
    "IssueCategory",
    "Priority",
    "EscalationQueue",
    "DocumentType",
    "LogFormat",
    "HealthStatus",
]