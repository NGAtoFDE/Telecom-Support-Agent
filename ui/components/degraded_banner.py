"""Visible warning when the last turn was served from the Groq backup provider.

Degraded mode must never be silent (README §4.4 rule 4): a user and a grader should both
be able to see at a glance that we failed over off the primary.
"""

from __future__ import annotations

import streamlit as st


def render_degraded_banner(response: dict | None) -> None:
    if not response:
        return
    llm = response.get("llm", {})
    if llm.get("degraded"):
        provider = llm.get("provider", "backup")
        st.markdown(
            f"<div class='degraded-banner'>⚠️ <b>Degraded mode</b> — primary provider "
            f"unavailable, serving from <code>{provider}</code>. Answers may differ from "
            f"the primary model.</div>",
            unsafe_allow_html=True,
        )
