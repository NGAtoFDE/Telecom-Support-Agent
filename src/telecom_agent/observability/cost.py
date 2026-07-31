"""Token accounting and USD estimation per provider.

Prices are per-million-token rates kept in one table so the cost model and the API's
``est_cost_usd`` agree. Groq figures are the published rates cited in README §18; Foundry
figures are placeholders to be replaced with your deployment's actual pricing on Day 1.
"""

from __future__ import annotations

from telecom_agent.core.enums import Alias, Provider
from telecom_agent.core.types import TokenUsage

# (input_usd_per_1M, output_usd_per_1M)
_PRICES: dict[tuple[Provider, Alias], tuple[float, float]] = {
    (Provider.GROQ, Alias.CHAT_MAIN): (0.15, 0.60),  # openai/gpt-oss-120b
    (Provider.GROQ, Alias.CHAT_MINI): (0.05, 0.08),  # llama-3.1-8b-instant
    # Placeholders — replace from the Azure pricing page for your chosen deployments.
    (Provider.AZURE_FOUNDRY, Alias.CHAT_MAIN): (2.50, 10.00),
    (Provider.AZURE_FOUNDRY, Alias.CHAT_MINI): (0.15, 0.60),
    (Provider.AZURE_FOUNDRY, Alias.EMBED): (0.02, 0.0),
    (Provider.FAKE, Alias.CHAT_MAIN): (0.0, 0.0),
    (Provider.FAKE, Alias.CHAT_MINI): (0.0, 0.0),
    (Provider.FAKE, Alias.EMBED): (0.0, 0.0),
}


def estimate_cost(provider: Provider, alias: Alias, usage: TokenUsage) -> float:
    inp, out = _PRICES.get((provider, alias), (0.0, 0.0))
    return round(
        usage.prompt_tokens / 1_000_000 * inp + usage.completion_tokens / 1_000_000 * out,
        6,
    )
