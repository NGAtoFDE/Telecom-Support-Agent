"""
Shared utility functions for the Telecom Support Agent.

This module contains small, reusable, dependency-free helper functions
used across multiple application layers.

Guidelines
----------
- Keep utilities generic and stateless.
- Avoid business logic.
- Avoid framework-specific helpers.
- Keep this module dependency-free.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, TypeVar, cast
from uuid import uuid4

T = TypeVar("T")


# ==============================================================================
# Time
# ==============================================================================


def utc_now() -> datetime:
    """
    Return the current timezone-aware UTC datetime.
    """
    return datetime.now(UTC)


# ==============================================================================
# UUID
# ==============================================================================


def generate_uuid4() -> str:
    """
    Generate a random UUID version 4 string.
    """
    return str(uuid4())


# ==============================================================================
# String
# ==============================================================================


def is_blank(value: str | None) -> bool:
    """
    Return True if the value is None or contains only whitespace.
    """
    return value is None or not value.strip()


def truncate(text: str, length: int = 100) -> str:
    """
    Truncate text while preserving readability.

    Parameters
    ----------
    text:
        Input text.

    length:
        Maximum output length, including the ellipsis.

    Returns
    -------
    str
        Truncated text.
    """
    if length < 4:
        raise ValueError("length must be at least 4")

    if len(text) <= length:
        return text

    return f"{text[: length - 3]}..."


# ==============================================================================
# Validation
# ==============================================================================


def require(value: T | None, message: str) -> T:
    """
    Ensure a value is not None.

    Raises
    ------
    ValueError
        If the supplied value is None.
    """
    if value is None:
        raise ValueError(message)

    return value


# ==============================================================================
# Mapping
# ==============================================================================


def safe_get(
    mapping: Mapping[str, Any],
    key: str,
    default: T | None = None,
) -> Any | T:
    """
    Safely retrieve a value from a mapping.
    """
    return mapping.get(key, default)


def deep_merge(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Recursively merge two mappings.

    Values from the right mapping override the left mapping.
    Uses deepcopy to guarantee the original dictionaries are not mutated.
    """
    result = deepcopy(dict(left))

    for key, value in right.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, Mapping)
        ):
            # Use `cast` to explicitly tell the type checker the exact nested types
            left_node = cast(dict[str, Any], result[key])
            right_node = cast(Mapping[str, Any], value)
            
            result[key] = deep_merge(left_node, right_node)
        else:
            result[key] = deepcopy(value)

    return result


__all__ = [
    "utc_now",
    "generate_uuid4",
    "is_blank",
    "truncate",
    "require",
    "safe_get",
    "deep_merge",
]