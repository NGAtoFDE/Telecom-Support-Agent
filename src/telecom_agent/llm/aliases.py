"""Maps stable code-level aliases to concrete per-provider model ids / deployment names.

README §4.2: Foundry routes on *deployment name*, Groq on *model id*. Code only ever
names ``chat-main`` / ``chat-mini`` / ``embed``; this module is the one place the mapping
to real identifiers lives, driven entirely by settings.
"""

from __future__ import annotations

from telecom_agent.config.settings import Settings
from telecom_agent.core.enums import Alias, Provider


def resolve(provider: Provider, alias: Alias, settings: Settings) -> str:
    """Return the concrete model id / deployment name for ``(provider, alias)``."""
    if provider == Provider.AZURE_FOUNDRY:
        return {
            Alias.CHAT_MAIN: settings.azure_ai_deployment_chat_main,
            Alias.CHAT_MINI: settings.azure_ai_deployment_chat_mini,
            Alias.EMBED: settings.azure_ai_deployment_embed,
        }[alias]
    # fake
    return f"fake-{alias.value}"
