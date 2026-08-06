"""Embedding client used ONLY by ``ingest.py`` (README §4.3: embeddings never touch the
query path). Returns a callable ``embed(texts) -> vectors``.

Provider selection:
- ``azure_foundry`` → the Foundry ``embed`` deployment (the real, production path).
- ``fake`` → deterministic offline pseudo-embeddings, so ingestion works with no cloud.
- ``groq`` → Groq has no embeddings; we fall back to the fake embedder and warn, because
  a Groq-primary configuration still needs *some* way to build an index locally.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from telecom_agent.config.settings import Settings
from telecom_agent.core.enums import Alias, Provider
from telecom_agent.llm.providers.fake import FakeProvider

log = logging.getLogger(__name__)

Embedder = Callable[[list[str]], list[list[float]]]


def get_embedder(settings: Settings) -> Embedder:
    provider = settings.default_provider
    if provider == Provider.AZURE_FOUNDRY:
        from telecom_agent.llm.providers.azure_foundry import AzureFoundryProvider

        client = AzureFoundryProvider(settings)
        return lambda texts: client.embed(texts, alias=Alias.EMBED)


    return FakeProvider().embed
