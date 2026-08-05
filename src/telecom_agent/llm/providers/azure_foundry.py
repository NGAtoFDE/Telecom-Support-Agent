"""Azure AI Foundry adapter — the primary provider.

Talks to the Foundry *models inference* endpoint
(``https://<resource>.services.ai.azure.com/models``) via ``azure-ai-inference``.
The endpoint routes on the ``model`` parameter, which we set to the *deployment name*
resolved from the alias (README §4.2).

The ``azure-ai-inference`` import is done lazily so the package (and the fake provider)
work in environments where the SDK / credentials are absent.
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


class AzureFoundryProvider:
    name = Provider.AZURE_FOUNDRY

    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self._chat_client = None
        self._embed_client = None

    # -- lazy clients -------------------------------------------------------
    def _chat(self):
        if self._chat_client is None:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential

            self._chat_client = ChatCompletionsClient(
                endpoint=self._s.azure_ai_endpoint,
                credential=AzureKeyCredential(self._s.azure_ai_api_key),
            )
        return self._chat_client

    def _embed(self):
        if self._embed_client is None:
            from azure.ai.inference import EmbeddingsClient
            from azure.core.credentials import AzureKeyCredential

            self._embed_client = EmbeddingsClient(
                endpoint=self._s.azure_ai_endpoint,
                credential=AzureKeyCredential(self._s.azure_ai_api_key),
            )
        return self._embed_client

    # -- chat ---------------------------------------------------------------
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
            "messages": payload,
            "model": model,
            "model_extras": {"max_completion_tokens": max_tokens},
        }
        # GPT-5 reasoning models do not support response_format: json_object.
        # The prompts already instruct the model to reply with JSON, and
        # extract_json() handles parsing robustly, so we omit it.
        try:
            resp = self._chat().complete(**kwargs)
        except Exception as exc:  # noqa: BLE001 - translated to our taxonomy below
            raise _translate(exc) from exc

        choice = resp.choices[0]
        usage = getattr(resp, "usage", None)
        return ChatResult(
            text=choice.message.content or "",
            usage=TokenUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            ),
            model=model,
            provider=self.name,
            finish_reason=getattr(choice, "finish_reason", "stop") or "stop",
        )

    # -- embeddings (ingestion only) ---------------------------------------
    def embed(self, texts: list[str], *, alias: Alias = Alias.EMBED) -> list[list[float]]:
        model = aliases.resolve(self.name, alias, self._s)
        try:
            resp = self._embed().embed(input=texts, model=model)
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc
        return [item.embedding for item in resp.data]

    def health(self) -> bool:
        try:
            self.chat(
                [Message(role="user", content="ping")],
                alias=Alias.CHAT_MINI,
                max_tokens=1000,
            )
            return True
        except ProviderError:
            return False


def _translate(exc: Exception) -> ProviderError:
    """Map SDK exceptions onto our error taxonomy so the router can react correctly."""
    status = getattr(exc, "status_code", None)
    text = str(exc).lower()
    if status == 429 or "quota" in text or "rate limit" in text:
        return ProviderQuota(str(exc))
    if "content" in text and "filter" in text:
        return ContentFiltered(str(exc))
    if "timeout" in text or "timed out" in text:
        return ProviderTimeout(str(exc))
    if status and 500 <= status < 600:
        return ProviderError(str(exc))
    return ProviderError(str(exc))
