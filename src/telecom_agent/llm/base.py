"""The provider-agnostic contract every LLM adapter implements.

Keeping this a ``Protocol`` (structural typing) means adapters do not need to inherit a
base class — they just need the right shape. The router depends only on this protocol,
so a new vendor is a new file, not a change to the router.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from telecom_agent.core.enums import Alias, Provider
from telecom_agent.core.types import Message, TokenUsage


@dataclass
class ChatResult:
    text: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""
    provider: Provider = Provider.FAKE
    finish_reason: str = "stop"


@runtime_checkable
class ChatProvider(Protocol):
    """Structural contract. All adapters expose exactly this surface."""

    name: Provider

    def chat(
        self,
        messages: list[Message],
        *,
        alias: Alias,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> ChatResult:
        """Single non-streaming completion. Raises a subclass of ProviderError on failure."""
        ...

    def embed(self, texts: list[str], *, alias: Alias = Alias.EMBED) -> list[list[float]]:
        """Embed texts. Only providers with an embeddings endpoint implement this
        meaningfully; others raise ``NotImplementedError`` (see README §4.3)."""
        ...

    def health(self) -> bool:
        """Cheap readiness probe used by ``/readyz``."""
        ...
