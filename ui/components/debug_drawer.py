"""Debug drawer — 'demo gold': classification, provider, tokens, cost and latency for the
last turn. Calls /classify separately so the confidence is always shown even on escalate
paths where the chat response omits it.
"""

from __future__ import annotations

import streamlit as st

from ui import state


def render_debug_drawer(client) -> None:
    ss = st.session_state
    resp = ss.get(state.LAST_RESPONSE)
    if not resp:
        return

    with st.expander("🔍 Debug drawer (demo)", expanded=False):
        llm = resp.get("llm", {})
        usage = resp.get("usage", {})

        c1, c2, c3 = st.columns(3)
        c1.metric("Category", resp.get("category") or "—")
        c2.metric("Priority", resp.get("priority") or "—")
        c3.metric("Resolution", resp.get("resolution") or "—")

        c4, c5, c6 = st.columns(3)
        c4.metric("Provider", llm.get("provider", "—"))
        c5.metric("Degraded", "yes" if llm.get("degraded") else "no")
        c6.metric("Latency (ms)", resp.get("latency_ms", 0))

        c7, c8, c9 = st.columns(3)
        c7.metric("Prompt tok", usage.get("prompt_tokens", 0))
        c8.metric("Compl. tok", usage.get("completion_tokens", 0))
        c9.metric("Est. cost $", f"{usage.get('est_cost_usd', 0.0):.5f}")

        st.caption(f"alias: `{llm.get('alias', '—')}` · trace_id: `{resp.get('trace_id', '')}`")

        # Classification detail (with confidence), fetched on demand.
        if st.button("Re-run classification (show confidence)", key="dbg_classify"):
            try:
                cls = client.classify(resp.get("_last_message", ""), ss.get(state.SESSION_ID))
                st.json(cls)
            except Exception as exc:  # noqa: BLE001
                st.caption(f"classify failed: {exc}")
