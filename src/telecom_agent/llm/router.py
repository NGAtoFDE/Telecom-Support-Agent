"""The LLM router: provider selection, per-session pinning, failover and circuit breaker.

Design rules it enforces (README §4.4), each existing because violating it causes a
specific bug:

1. **Pin the provider per session, not per call.** Once a session is pinned, every node
   in that session uses the same provider so the classifier and verifier reason with the
   same model.
2. **Stamp provider + model on every result** (carried on :class:`ChatResult`).
3. **Prompts stay provider-agnostic;** JSON is validated by the caller, not by a
   vendor-specific feature.

Contains no prompt text.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from telecom_agent.config.settings import Settings
from telecom_agent.core.enums import Alias, Provider
from telecom_agent.core.errors import (
    AllProvidersDown,
    BreakerOpen,
    ContentFiltered,
    ProviderError,
)
from telecom_agent.core.types import Message
from telecom_agent.llm.base import ChatProvider, ChatResult
from telecom_agent.llm.guards import CircuitBreaker, TokenBudget
from telecom_agent.llm.providers.fake import FakeProvider


@dataclass
class _SessionLLM:
    provider: Provider
    degraded: bool = False
    budget: TokenBudget = field(default=None)  # type: ignore[assignment]


def build_provider(kind: Provider, settings: Settings) -> ChatProvider:
    if kind == Provider.FAKE:
        return FakeProvider()
    if kind == Provider.AZURE_FOUNDRY:
        from telecom_agent.llm.providers.azure_foundry import AzureFoundryProvider

        return AzureFoundryProvider(settings)
    raise ValueError(f"unknown provider {kind}")


class LLMRouter:
    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self._primary_kind = settings.default_provider
        self._providers: dict[Provider, ChatProvider] = {}
        self._breakers: dict[Provider, CircuitBreaker] = {
            self._primary_kind: CircuitBreaker(settings.llm_breaker_cooldown_seconds),
        }
        self._sessions: dict[str, _SessionLLM] = {}

    # -- provider instances (lazy, cached) ---------------------------------
    def _provider(self, kind: Provider) -> ChatProvider:
        if kind not in self._providers:
            self._providers[kind] = build_provider(kind, self._s)
        return self._providers[kind]

    # -- session lifecycle --------------------------------------------------
    def ensure_session(self, session_id: str) -> Provider:
        """Pin a provider for the session if not already pinned. Called by load_session."""
        if session_id not in self._sessions:
            start = self._primary_kind
            degraded = False
            self._sessions[session_id] = _SessionLLM(
                provider=start,
                degraded=degraded,
                budget=TokenBudget(cap=self._s.session_token_budget),
            )
        return self._sessions[session_id].provider

    def provider_for(self, session_id: str) -> Provider:
        self.ensure_session(session_id)
        return self._sessions[session_id].provider

    def is_degraded(self, session_id: str) -> bool:
        return self._sessions.get(session_id, _SessionLLM(self._primary_kind)).degraded

    def budget_remaining(self, session_id: str) -> int:
        s = self._sessions.get(session_id)
        return s.budget.remaining if s and s.budget else self._s.session_token_budget

    def _breaker_open(self, kind: Provider) -> bool:
        b = self._breakers.get(kind)
        return bool(b and b.is_open())

    # -- the call -----------------------------------------------------------
    def chat(
        self,
        session_id: str,
        messages: list[Message],
        *,
        alias: Alias,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> ChatResult:
        """Run a chat completion on the session's pinned provider."""
        self.ensure_session(session_id)
        sess = self._sessions[session_id]
        kind = sess.provider

        if self._breaker_open(kind):
            raise BreakerOpen(f"{kind} breaker open")
            
        try:
            result = self._attempt(kind, messages, alias, temperature, max_tokens, json_mode)
            self._breakers[kind].record_success()
            if sess.budget:
                sess.budget.charge(result.usage.total)
            return result
        except ProviderError as exc:
            self._breakers[kind].record_failure()
            raise

        raise AllProvidersDown(str(last_exc) if last_exc else "no provider succeeded")

    def _attempt(
        self,
        kind: Provider,
        messages: list[Message],
        alias: Alias,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> ChatResult:
        """One provider, with up to 2 retries on transient errors (backoff omitted in
        tests via the fake provider; real backoff lives in the adapters' timeout config)."""
        provider = self._provider(kind)
        attempts = 3  # 1 + 2 retries
        last: ProviderError | None = None
        for _ in range(attempts):
            try:
                return provider.chat(
                    messages,
                    alias=alias,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )
            except ContentFiltered:
                raise
            except ProviderError as exc:
                last = exc
                if not exc.retryable:
                    raise
        assert last is not None
        raise last

    # -- readiness ----------------------------------------------------------
    def health(self) -> dict[str, bool]:
        """Probe every configured provider for ``/readyz``."""
        out: dict[str, bool] = {}
        for kind in filter(None, [self._primary_kind]):
            try:
                out[kind.value] = self._provider(kind).health()
            except Exception:  # noqa: BLE001
                out[kind.value] = False
        return out
