"""Per-session token cap and retry limits.

The hard enforcement lives in ``llm/guards.py`` (the router charges every call against a
``TokenBudget``); this module exposes the policy numbers and a helper the graph uses to
decide whether it may afford another LLM round.
"""

from __future__ import annotations

from telecom_agent.config.settings import Settings


class BudgetPolicy:
    def __init__(self, settings: Settings) -> None:
        self.session_cap = settings.session_token_budget
        self.max_attempts = settings.max_verify_attempts

    def can_retry(self, attempt: int) -> bool:
        return attempt < self.max_attempts
