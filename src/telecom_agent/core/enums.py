"""Single source of truth for every taxonomy in the system.

Nothing else in the codebase is allowed to define these string values inline. A node,
a prompt renderer, a routing table and an eval runner must all agree on the exact same
set of categories, priorities, queues and providers — so they all import from here.
"""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """str + Enum so values JSON-serialise as their plain string form."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return str(self.value)


class IssueCategory(StrEnum):
    NETWORK_COVERAGE = "NETWORK_COVERAGE"
    DATA_SLOW = "DATA_SLOW"
    CALL_DROP = "CALL_DROP"
    BILLING_DISPUTE = "BILLING_DISPUTE"
    RECHARGE_PAYMENT_FAILED = "RECHARGE_PAYMENT_FAILED"
    SIM_ACTIVATION = "SIM_ACTIVATION"
    SIM_SWAP_PORTING = "SIM_SWAP_PORTING"
    ROAMING = "ROAMING"
    VAS_SUBSCRIPTION = "VAS_SUBSCRIPTION"
    DEVICE_CONFIG = "DEVICE_CONFIG"
    ACCOUNT_KYC = "ACCOUNT_KYC"
    OTHER = "OTHER"


class Priority(StrEnum):
    """P1 no service / suspected outage · P2 severely degraded ·
    P3 billing or provisioning dispute · P4 informational."""

    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class EscalationQueue(StrEnum):
    NOC_L2 = "NOC_L2"
    BILLING_OPS = "BILLING_OPS"
    SIM_PROVISIONING = "SIM_PROVISIONING"
    ROAMING_PARTNER_DESK = "ROAMING_PARTNER_DESK"
    RETENTION = "RETENTION"
    GENERAL_L1 = "GENERAL_L1"


class Resolution(StrEnum):
    RESOLVED = "RESOLVED"
    NEEDS_INFO = "NEEDS_INFO"
    ESCALATED = "ESCALATED"


class Provider(StrEnum):
    AZURE_FOUNDRY = "AZURE_FOUNDRY"
    GROQ = "GROQ"
    FAKE = "FAKE"


class Alias(StrEnum):
    """Stable model aliases used everywhere in code; mapped to concrete model ids
    per provider in ``llm/aliases.py``. A model upgrade is a portal/config change,
    never a code change."""

    CHAT_MAIN = "chat-main"
    CHAT_MINI = "chat-mini"
    EMBED = "embed"


class TicketStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


# Convenience: all category / priority / queue string values, handy for validators & evals.
CATEGORY_VALUES = tuple(c.value for c in IssueCategory)
PRIORITY_VALUES = tuple(p.value for p in Priority)
QUEUE_VALUES = tuple(q.value for q in EscalationQueue)
