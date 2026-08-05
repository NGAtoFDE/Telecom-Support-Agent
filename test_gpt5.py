"""Check if GPT-5 draft_answer produces actual content with KB context."""
import sys
sys.path.insert(0, "src")

import logging
logging.disable(logging.CRITICAL)  # suppress SDK logging

from telecom_agent.config.settings import get_settings
from telecom_agent.core.enums import Alias
from telecom_agent.core.types import Message
from telecom_agent.llm.providers.azure_foundry import AzureFoundryProvider
from telecom_agent.prompts import registry

s = get_settings()
p = AzureFoundryProvider(s)

context = """[KB-110 §Overview] Slow Data / No Internet — APN Reset
If the customer reports slow data or no internet, the first step is to reset the APN settings.

[KB-110 §Steps] Slow Data / No Internet — APN Reset
1. Go to Settings > Mobile Network > Access Point Names
2. Tap the three-dot menu and select "Reset to default"
3. Restart the phone
4. Wait 2 minutes and test the connection"""

node_system = registry.render(
    "answer", s.answer_version,
    json={"message": "my wifi keeps disconnecting"},
    context=context,
)
messages = [
    Message(role="system", content="You are a telecom assistant."),
    Message(role="system", content=node_system),
    Message(role="user", content="my internet speed is slow since yesterday"),
]

print("\n=== Calling GPT-5 draft_answer with KB context (max_tokens=2500) ===")
result = p.chat(messages, alias=Alias.CHAT_MAIN, max_tokens=2500)
print(f"Draft text ({len(result.text)} chars):")
print(result.text[:800] if result.text else "(EMPTY)")
print(f"\nModel: {result.model}")
print(f"Usage: prompt={result.usage.prompt_tokens}, completion={result.usage.completion_tokens}")
