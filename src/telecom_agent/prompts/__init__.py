"""Prompts are versioned assets, never inline strings. Load them via the registry."""

from telecom_agent.prompts.registry import Prompt, get_prompt, render

__all__ = ["Prompt", "get_prompt", "render"]
