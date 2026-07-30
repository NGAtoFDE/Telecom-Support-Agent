"""
Application-wide exception hierarchy for the Telecom Support Agent.

This module defines structured exceptions shared across all application
layers. Each exception contains a human-readable message, a machine-readable
error code, and optional contextual metadata for logging, debugging,
and API responses.

Guidelines
----------
- Raise custom exceptions instead of built-in exceptions.
- Keep exceptions free of business logic.
- Let the API layer map exceptions to HTTP responses.
- Keep this module dependency-free.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, ClassVar, final


class TelecomAgentError(Exception):
    """
    Base exception for the Telecom Support Agent.

    Parameters
    ----------
    message:
        Human-readable error message.

    error_code:
        Machine-readable error identifier.

    details:
        Additional structured metadata useful for debugging,
        logging, tracing, and API responses.
    """

    __slots__ = ("message", "error_code", "details")

    default_message: ClassVar[str] = (
        "An unexpected application error occurred."
    )
    default_error_code: ClassVar[str] = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.error_code = error_code or self.default_error_code
        
        # ADD [str, Any] HERE
        self.details = MappingProxyType[str, Any](dict(details or {}))
        
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a readable string representation."""
        return f"[{self.error_code}] {self.message}"

    def __repr__(self) -> str:
        """Return a detailed developer-friendly representation."""
        return (
            f"{self.__class__.__name__}("
            f"error_code={self.error_code!r}, "
            f"message={self.message!r}, "
            f"details={dict(self.details)!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the exception into a JSON-compatible dictionary."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": dict(self.details),
        }

    def __reduce__(self)-> tuple[type, tuple[str], dict[str, Any]]:
        """Support pickling."""
        return (
            self.__class__,
            (self.message,),
            {
                "error_code": self.error_code,
                "details": dict(self.details),
            },
        )

    def __setstate__(self, state: dict[str, Any] | None) -> None:
        """Restore state from pickling safely."""
        if state is None:
            self.error_code = self.default_error_code
            # ADD [str, Any] HERE
            self.details = MappingProxyType[str, Any]({})
            return

        self.error_code = state.get("error_code", self.default_error_code)
        
        # Explicitly type the fallback dictionary to satisfy strict mode, 
        # then wrap it with explicitly typed MappingProxyType
        raw_details: dict[str, Any] = state.get("details", {})
        self.details = MappingProxyType[str, Any](raw_details)


# ==============================================================================
# Configuration
# ==============================================================================


@final
class ConfigurationError(TelecomAgentError):
    """Raised when application configuration is invalid."""

    __slots__ = ()

    default_message: ClassVar[str] = "Invalid application configuration."
    default_error_code: ClassVar[str] = "CONFIGURATION_ERROR"


# ==============================================================================
# Validation
# ==============================================================================


@final
class ValidationError(TelecomAgentError):
    """Raised when validation fails."""

    __slots__ = ()

    default_message: ClassVar[str] = "Validation failed."
    default_error_code: ClassVar[str] = "VALIDATION_ERROR"


# ==============================================================================
# Authentication & Authorization
# ==============================================================================


@final
class AuthenticationError(TelecomAgentError):
    """Raised when authentication fails."""

    __slots__ = ()

    default_message: ClassVar[str] = "Authentication failed."
    default_error_code: ClassVar[str] = "AUTHENTICATION_ERROR"


@final
class AuthorizationError(TelecomAgentError):
    """Raised when authorization fails."""

    __slots__ = ()

    default_message: ClassVar[str] = "Authorization failed."
    default_error_code: ClassVar[str] = "AUTHORIZATION_ERROR"


# ==============================================================================
# Resources
# ==============================================================================


@final
class ResourceNotFoundError(TelecomAgentError):
    """Raised when a requested resource does not exist."""

    __slots__ = ()

    default_message: ClassVar[str] = "Requested resource was not found."
    default_error_code: ClassVar[str] = "RESOURCE_NOT_FOUND"


# ==============================================================================
# Database / Storage
# ==============================================================================


@final
class DatabaseError(TelecomAgentError):
    """Raised when a database operation fails."""

    __slots__ = ()

    default_message: ClassVar[str] = "Database operation failed."
    default_error_code: ClassVar[str] = "DATABASE_ERROR"


@final
class CacheError(TelecomAgentError):
    """Raised when a cache operation fails."""

    __slots__ = ()

    default_message: ClassVar[str] = "Cache operation failed."
    default_error_code: ClassVar[str] = "CACHE_ERROR"


# ==============================================================================
# Embeddings / Retrieval
# ==============================================================================


@final
class EmbeddingError(TelecomAgentError):
    """Raised when embedding generation fails."""

    __slots__ = ()

    default_message: ClassVar[str] = "Embedding generation failed."
    default_error_code: ClassVar[str] = "EMBEDDING_ERROR"


@final
class VectorStoreError(TelecomAgentError):
    """Raised when vector store operations fail."""

    __slots__ = ()

    default_message: ClassVar[str] = "Vector store operation failed."
    default_error_code: ClassVar[str] = "VECTOR_STORE_ERROR"


@final
class RetrievalError(TelecomAgentError):
    """Raised when document retrieval fails."""

    __slots__ = ()

    default_message: ClassVar[str] = "Document retrieval failed."
    default_error_code: ClassVar[str] = "RETRIEVAL_ERROR"


# ==============================================================================
# Prompt
# ==============================================================================


@final
class PromptError(TelecomAgentError):
    """Raised when prompt generation fails."""

    __slots__ = ()

    default_message: ClassVar[str] = "Prompt generation failed."
    default_error_code: ClassVar[str] = "PROMPT_ERROR"


# ==============================================================================
# LLM
# ==============================================================================


class LLMError(TelecomAgentError):
    """Base exception for LLM providers."""

    __slots__ = ()

    default_message: ClassVar[str] = "LLM request failed."
    default_error_code: ClassVar[str] = "LLM_ERROR"


@final
class AzureLLMError(LLMError):
    """Raised when Azure AI requests fail."""

    __slots__ = ()

    default_message: ClassVar[str] = "Azure AI request failed."
    default_error_code: ClassVar[str] = "AZURE_LLM_ERROR"


@final
class GroqLLMError(LLMError):
    """Raised when Groq requests fail."""

    __slots__ = ()

    default_message: ClassVar[str] = "Groq request failed."
    default_error_code: ClassVar[str] = "GROQ_LLM_ERROR"


# ==============================================================================
# Agent
# ==============================================================================


class AgentError(TelecomAgentError):
    """Base exception for agent execution."""

    __slots__ = ()

    default_message: ClassVar[str] = "Agent execution failed."
    default_error_code: ClassVar[str] = "AGENT_ERROR"


@final
class ToolExecutionError(AgentError):
    """Raised when tool execution fails."""

    __slots__ = ()

    default_message: ClassVar[str] = "Tool execution failed."
    default_error_code: ClassVar[str] = "TOOL_EXECUTION_ERROR"


@final
class AgentMemoryError(AgentError):
    """Raised when conversation memory operations fail."""

    __slots__ = ()

    default_message: ClassVar[str] = "Memory operation failed."
    default_error_code: ClassVar[str] = "MEMORY_ERROR"


# ==============================================================================
# API
# ==============================================================================


@final
class RateLimitError(TelecomAgentError):
    """Raised when rate limits are exceeded."""

    __slots__ = ()

    default_message: ClassVar[str] = "Rate limit exceeded."
    default_error_code: ClassVar[str] = "RATE_LIMIT_ERROR"


@final
class InternalServerError(TelecomAgentError):
    """Raised for unexpected internal failures."""

    __slots__ = ()

    default_message: ClassVar[str] = "Internal server error."
    default_error_code: ClassVar[str] = "INTERNAL_SERVER_ERROR"


__all__ = [
    "TelecomAgentError",
    "ConfigurationError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "ResourceNotFoundError",
    "DatabaseError",
    "CacheError",
    "EmbeddingError",
    "VectorStoreError",
    "RetrievalError",
    "PromptError",
    "LLMError",
    "AzureLLMError",
    "GroqLLMError",
    "AgentError",
    "ToolExecutionError",
    "AgentMemoryError",
    "RateLimitError",
    "InternalServerError",
]