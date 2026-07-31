"""
Core package for the Telecom Support Agent.

This package contains the foundational building blocks shared across the
entire application, including:

- Enumerations
- Exception hierarchy
- Shared data types
- Generic utility functions
"""

from .enums import (
    ComputeDevice,
    DocumentType,
    EmbeddingProvider,
    Environment,
    EscalationQueue,
    HealthStatus,
    IssueCategory,
    LLMProvider,
    LogFormat,
    MessageRole,
    Priority,
    ResponseStatus,
    RetrieverType,
    VectorStoreType,
)
from .errors import (
    AgentError,
    AgentMemoryError,
    AuthenticationError,
    AuthorizationError,
    AzureLLMError,
    CacheError,
    ConfigurationError,
    DatabaseError,
    EmbeddingError,
    GroqLLMError,
    InternalServerError,
    LLMError,
    PromptError,
    RateLimitError,
    ResourceNotFoundError,
    RetrievalError,
    TelecomAgentError,
    ToolExecutionError,
    ValidationError,
    VectorStoreError,
)
from .types import (
    CustomerCtx,
    Message,
    Ticket,
    TokenUsage,
)
from .utils import (
    deep_merge,
    generate_uuid4,
    is_blank,
    require,
    safe_get,
    truncate,
    utc_now,
)

__all__ = [
    # Enums
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

    # Errors
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

    # Types
    "Message",
    "CustomerCtx",
    "TokenUsage",
    "Ticket",

    # Utilities
    "utc_now",
    "generate_uuid4",
    "is_blank",
    "truncate",
    "require",
    "safe_get",
    "deep_merge",
]