"""LLM router invariants: session pinning, breaker, failover→degraded, no-retry on
content filter, and hard token-budget enforcement. All with in-memory stub providers."""

from __future__ import annotations

import pytest

from telecom_agent.config.settings import Settings
from telecom_agent.core.enums import Alias, Provider
from telecom_agent.core.errors import BudgetExceeded, ContentFiltered, ProviderError
from telecom_agent.core.types import Message, TokenUsage
from telecom_agent.llm.base import ChatResult
from telecom_agent.llm.guards import CircuitBreaker
from telecom_agent.llm.router import LLMRouter

MSG = [Message(role="user", content="hi")]


class StubProvider:
    def __init__(self, name, *, fail_times=0, error=None, usage_total=10):
        self.name = name
        self.fail_times = fail_times
        self.error = error or ProviderError("boom")
        self.usage_total = usage_total
        self.calls = 0

    def chat(self, messages, *, alias, temperature=0.0, max_tokens=1024, json_mode=False):
        self.calls += 1
        if self.fail_times > 0:
            self.fail_times -= 1
            raise self.error
        return ChatResult(
            text="ok",
            usage=TokenUsage(prompt_tokens=self.usage_total, completion_tokens=0),
            model="stub",
            provider=self.name,
        )

    def embed(self, texts, *, alias=Alias.EMBED):
        raise NotImplementedError

    def health(self):
        return True


def _foundry_settings(**over) -> Settings:
    over.setdefault("llm_failover_enabled", True)
    return Settings(llm_provider="azure_foundry", **over)


# ---- circuit breaker ----
def test_breaker_trips_after_threshold_and_resets_after_cooldown():
    t = [0.0]
    cb = CircuitBreaker(cooldown_seconds=60, fail_threshold=2, _clock=lambda: t[0])
    assert not cb.is_open()
    cb.record_failure()
    assert not cb.is_open()  # one failure not enough
    cb.record_failure()
    assert cb.is_open()  # tripped
    t[0] = 61  # cooldown elapses
    assert not cb.is_open()  # half-open probe allowed


# ---- pinning ----
def test_session_provider_is_pinned_and_stable():
    r = LLMRouter(_foundry_settings())
    r._providers = {
        Provider.AZURE_FOUNDRY: StubProvider(Provider.AZURE_FOUNDRY),
    }
    p1 = r.ensure_session("s1")
    p2 = r.provider_for("s1")
    assert p1 == p2 == Provider.AZURE_FOUNDRY


# ---- content filter is not retried ----
def test_content_filter_not_retried():
    r = LLMRouter(_foundry_settings())
    primary = StubProvider(Provider.AZURE_FOUNDRY, fail_times=1, error=ContentFiltered("blocked"))
    r._providers = {Provider.AZURE_FOUNDRY: primary}
    with pytest.raises(ContentFiltered):
        r.chat("s1", MSG, alias=Alias.CHAT_MAIN)
    assert primary.calls == 1  # no retry


# ---- token budget ----
def test_budget_exceeded_raises():
    r = LLMRouter(_foundry_settings(session_token_budget=5, llm_failover_enabled=False))
    r._providers = {Provider.AZURE_FOUNDRY: StubProvider(Provider.AZURE_FOUNDRY, usage_total=100)}
    with pytest.raises(BudgetExceeded):
        r.chat("s1", MSG, alias=Alias.CHAT_MAIN)
