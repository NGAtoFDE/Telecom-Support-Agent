"""
Shared immutable data types for the Telecom Support Agent.

This module contains lightweight data structures shared across
multiple application layers. These types improve readability,
type safety, and consistency while remaining free of business
logic.

Guidelines
----------
- Keep types immutable whenever possible.
- Avoid methods containing business logic.
- Prefer dataclasses over dictionaries for shared objects.
- Keep this module dependency-free.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .enums import MessageRole, Priority


# ==============================================================================
# Helper Factories
# ==============================================================================


def _empty_metadata() -> Mapping[str, Any]:
    """
    Return an immutable empty mapping.

    Using MappingProxyType prevents accidental mutation of metadata in
    frozen dataclasses while avoiding shared mutable defaults.
    """
    return MappingProxyType({})


# ==============================================================================
# Conversation
# ==============================================================================


@dataclass(slots=True, frozen=True)
class Message:
    """Represents a single conversation message."""

    role: MessageRole
    content: str


# ==============================================================================
# Customer
# ==============================================================================


@dataclass(slots=True, frozen=True)
class CustomerCtx:
    """Shared customer context."""

    customer_id: str
    phone_number: str
    account_id: str | None = None
    plan_name: str | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=_empty_metadata
    )


# ==============================================================================
# LLM
# ==============================================================================


@dataclass(slots=True, frozen=True)
class TokenUsage:
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


# ==============================================================================
# Ticket
# ==============================================================================


@dataclass(slots=True, frozen=True)
class Ticket:
    """Represents a support ticket."""

    ticket_id: str
    customer_id: str
    issue: str
    priority: Priority
    status: str
    assigned_to: str | None = None


__all__ = [
    "Message",
    "CustomerCtx",
    "TokenUsage",
    "Ticket",
]