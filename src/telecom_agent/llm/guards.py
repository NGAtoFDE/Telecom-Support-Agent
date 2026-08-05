"""Cross-cutting safety rails for the LLM layer: circuit breaker, token budget,
and a lightweight prompt-injection scanner.

None of these know about prompts or providers; they operate on counters and raw text.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from telecom_agent.core.errors import BudgetExceeded


@dataclass
class CircuitBreaker:
    """Trips after ``fail_threshold`` consecutive failures, then stays open for
    ``cooldown_seconds`` before allowing a probe. Time is injectable for tests."""

    cooldown_seconds: float = 60.0
    fail_threshold: int = 2
    _failures: int = 0
    _opened_at: float | None = None
    _clock: Callable[[], float] = field(default=time.monotonic)

    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if self._clock() - self._opened_at >= self.cooldown_seconds:
            # cooldown elapsed → half-open: allow one probe
            self._opened_at = None
            self._failures = 0
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.fail_threshold:
            self._opened_at = self._clock()


@dataclass
class TokenBudget:
    """Hard per-session cap. Enforced *before* a call so we never overshoot silently."""

    cap: int
    spent: int = 0

    def would_exceed(self, incoming: int) -> bool:
        return self.spent + incoming > self.cap

    def charge(self, tokens: int) -> None:
        if self.would_exceed(tokens):
            raise BudgetExceeded(
                f"session token budget {self.cap} would be exceeded "
                f"(spent={self.spent}, incoming={tokens})"
            )
        self.spent += tokens

    @property
    def remaining(self) -> int:
        return max(0, self.cap - self.spent)


# Coarse but useful patterns. The real defence is never interpolating user text into
# tool arguments (see tools/validators.py); this is defence-in-depth + a signal to log.
_INJECTION_PATTERNS = [
    re.compile(r"ignore (all|any|previous|above).{0,20}instructions", re.I),
    re.compile(r"disregard .{0,20}(instructions|prompt|rules)", re.I),
    re.compile(r"you are now .{0,30}(dan|developer mode|unrestricted)", re.I),
    re.compile(r"reveal (the )?(system )?prompt", re.I),
    re.compile(r"\bexfiltrate\b|\bexecute\b.{0,10}\bcommand\b", re.I),
]


def scan_for_injection(text: str) -> list[str]:
    """Return the list of injection patterns matched. Empty means clean."""
    hits = [p.pattern for p in _INJECTION_PATTERNS if p.search(text or "")]
    return hits
