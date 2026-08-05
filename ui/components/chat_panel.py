"""Message thread + input box.

Renders the running conversation, attaching category/priority/resolution badges and the
citation card to each assistant turn. The input box lives here; app.py owns the API call.
"""

from __future__ import annotations

import streamlit as st

from ui.components.citation_card import render_citations

_PRIORITY_COLOR = {"P1": "#dc2626", "P2": "#ea580c", "P3": "#ca8a04", "P4": "#2563eb"}
_RESOLUTION_COLOR = {"RESOLVED": "#16a34a", "ESCALATED": "#dc2626", "NEEDS_INFO": "#ca8a04"}


def _badge(label: str, color: str) -> str:
    # Use hex for border/text, and add transparency for background (e.g. 15% opacity)
    return (
        f"<span class='modern-badge' style='background: {color}25; color: {color}; border: 1px solid {color}50;'>{label}</span>"
    )


def render_thread(messages: list[dict]) -> None:
    for msg in messages:
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
            meta = msg.get("meta") or {}
            if meta:
                badges = ""
                if meta.get("category"):
                    badges += _badge(meta["category"], "#334155")
                if meta.get("priority"):
                    badges += _badge(
                        meta["priority"], _PRIORITY_COLOR.get(meta["priority"], "#334155")
                    )
                if meta.get("resolution"):
                    badges += _badge(
                        meta["resolution"], _RESOLUTION_COLOR.get(meta["resolution"], "#334155")
                    )
                if badges:
                    st.markdown(badges, unsafe_allow_html=True)
            st.markdown(msg["content"])
            if meta.get("citations"):
                render_citations(meta["citations"])


def chat_input_box() -> str | None:
    return st.chat_input("Describe the customer's issue (e.g. 'no data since morning in Pune')")
