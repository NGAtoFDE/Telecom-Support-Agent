"""Expandable source view: shows the doc_id, title, section and score for each citation
the assistant actually referenced."""

from __future__ import annotations

import streamlit as st


def render_citations(citations: list[dict]) -> None:
    if not citations:
        return
    with st.expander(f"📚 Sources ({len(citations)})", expanded=False):
        for c in citations:
            score = c.get("score", 0.0)
            st.markdown(
                f"**`{c.get('doc_id', '?')}`** · §{c.get('section', '?')} "
                f"— {c.get('title', '')}  \n"
                f"<span style='color:#6b7280;font-size:0.85em'>relevance {score:.2f}</span>",
                unsafe_allow_html=True,
            )
            st.progress(min(max(float(score), 0.0), 1.0))
