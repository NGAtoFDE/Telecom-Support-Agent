"""Sanitises tool arguments and blocks injected values.

The core defence against prompt injection reaching a side effect (README §6, §16): user
text is never interpolated into a tool argument unchecked. Values are coerced to the
expected enum / primitive, and free-text fields are stripped of control characters and
length-capped before they can be persisted.
"""

from __future__ import annotations

import re

from telecom_agent.core.enums import EscalationQueue, IssueCategory, Priority

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean_text(value: str, *, max_len: int = 500) -> str:
    value = _CTRL.sub("", value or "")
    value = value.replace("\r", " ").strip()
    return value[:max_len]


def coerce_category(value: str | IssueCategory) -> IssueCategory:
    try:
        return IssueCategory(str(value))
    except ValueError:
        return IssueCategory.OTHER


def coerce_priority(value: str | Priority) -> Priority:
    try:
        return Priority(str(value))
    except ValueError:
        return Priority.P4


def coerce_queue(value: str | EscalationQueue) -> EscalationQueue:
    try:
        return EscalationQueue(str(value))
    except ValueError:
        return EscalationQueue.GENERAL_L1
