"""Groq adapter — the backup provider (chat only).

Groq exposes an OpenAI-compatible API at ``https://api.groq.com/openai/v1``, so we reuse
the ``openai`` SDK pointed at that base URL. Groq has **no embeddings endpoint** — the
``embed`` method raises, which is correct and intentional (README §4.3): embeddings only
ever run at ingestion time on the Foundry path.
"""

from __future__ import annotations

from telecom_agent.config.settings import Settings
from telecom_agent.core.enums import Alias, Provider
from telecom_agent.core.errors import (
    ContentFiltered,
    ProviderError,
    ProviderQuota,
    ProviderTimeout,
)
from telecom_agent.core.types import Message, TokenUsage
from telecom_agent.llm import aliases
from telecom_agent.llm.base import ChatResult


class GroqProvider:
    name = Provider.GROQ

    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self._client = None

    def _openai(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(
                base_url=self._s.groq_base_url,
                api_key=self._s.groq_api_key,
                timeout=self._s.llm_request_timeout_seconds,
            )
        return self._client

    def chat(
        self,
        messages: list[Message],
        *,
        alias: Alias,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> ChatResult:
        model = aliases.resolve(self.name, alias, self._s)
        payload = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: dict = {
            "model": model,
            "messages": payload,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            resp = self._openai().chat.completions.create(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc

        choice = resp.choices[0]
        usage = resp.usage
        return ChatResult(
            text=choice.message.content or "",
            usage=TokenUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            ),
            model=model,
            provider=self.name,
            finish_reason=choice.finish_reason or "stop",
        )

    def embed(self, texts: list[str], *, alias: Alias = Alias.EMBED) -> list[list[float]]:
        raise NotImplementedError(
            "Groq has no embeddings endpoint. Embeddings run at ingestion time on the "
            "Foundry `embed` deployment only (README §4.3)."
        )

    def health(self) -> bool:
        """Readiness probe: confirm the configured chat model still exists (README risk
        row: 'Groq model deprecated / 404 → readyz fails loudly at deploy, not demo')."""
        try:
            models = {m.id for m in self._openai().models.list().data}
            wanted = {
                aliases.resolve(self.name, Alias.CHAT_MAIN, self._s),
                aliases.resolve(self.name, Alias.CHAT_MINI, self._s),
            }
            return wanted.issubset(models)
        except Exception:  # noqa: BLE001
            return False


def _translate(exc: Exception) -> ProviderError:
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    text = str(exc).lower()
    if status == 429 or "rate limit" in text or "quota" in text:
        return ProviderQuota(str(exc))
    if "content" in text and ("filter" in text or "policy" in text):
        return ContentFiltered(str(exc))
    if "timeout" in text or "timed out" in text:
        return ProviderTimeout(str(exc))
    return ProviderError(str(exc))
