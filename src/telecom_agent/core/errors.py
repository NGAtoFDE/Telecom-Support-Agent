"""Exception hierarchy mapped 1:1 to API error codes.

Every raised ``AppError`` carries a stable ``code`` that the API serialises into the
single error envelope defined in the contract, so the UI has exactly one error path.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class. ``code`` is the machine-readable error code exposed to clients."""

    code: str = "INTERNAL_ERROR"
    http_status: int = 500
    retryable: bool = False

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.__class__.__name__)
        self.message = message or self.__class__.__name__


# ---- client / validation ----
class ValidationFailed(AppError):
    code = "VALIDATION_FAILED"
    http_status = 422


class AuthError(AppError):
    code = "UNAUTHORIZED"
    http_status = 401


class RateLimited(AppError):
    code = "RATE_LIMITED"
    http_status = 429
    retryable = True


class NotFound(AppError):
    code = "NOT_FOUND"
    http_status = 404


# ---- retrieval / generation ----
class RetrievalEmpty(AppError):
    """Nothing scored above the retrieval floor — answer-not-found, escalate."""

    code = "RETRIEVAL_EMPTY"
    http_status = 200  # not an HTTP failure; the graph handles it by escalating
    retryable = False


class GroundednessFailed(AppError):
    code = "GROUNDEDNESS_FAILED"
    http_status = 200


class SchemaRepairFailed(AppError):
    """LLM produced malformed JSON that survived the one repair attempt."""

    code = "SCHEMA_REPAIR_FAILED"
    http_status = 200


# ---- provider / infra ----
class ProviderError(AppError):
    code = "PROVIDER_ERROR"
    http_status = 502
    retryable = True


class ProviderTimeout(ProviderError):
    code = "PROVIDER_TIMEOUT"
    retryable = True


class ProviderQuota(ProviderError):
    code = "PROVIDER_QUOTA"
    http_status = 429
    retryable = True


class ContentFiltered(ProviderError):
    """Provider content filter blocked the request/response. Do not retry — escalate."""

    code = "CONTENT_FILTERED"
    http_status = 200
    retryable = False


class AllProvidersDown(AppError):
    code = "ALL_PROVIDERS_DOWN"
    http_status = 503
    retryable = True


class BudgetExceeded(AppError):
    code = "BUDGET_EXCEEDED"
    http_status = 200


class BreakerOpen(ProviderError):
    code = "BREAKER_OPEN"
    retryable = True