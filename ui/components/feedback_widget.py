"""Thumbs up/down + comment, posted with the trace_id of the last turn (README §14).

Guards against duplicate submissions per trace_id using the FEEDBACK_SENT set in state.
"""

from __future__ import annotations

import streamlit as st

from ui import state


def render_feedback_widget(client) -> None:
    ss = st.session_state
    trace_id = ss.get(state.LAST_TRACE_ID) or ""
    if not trace_id:
        return

    st.markdown("#### 💬 Was this helpful?")
    already = trace_id in ss.get(state.FEEDBACK_SENT, set())
    if already:
        st.caption("Thanks — feedback recorded for this turn.")
        return

    col1, col2 = st.columns(2)
    thumbs: str | None = None
    if col1.button("👍 Yes", use_container_width=True, key=f"up_{trace_id}"):
        thumbs = "up"
    if col2.button("👎 No", use_container_width=True, key=f"down_{trace_id}"):
        thumbs = "down"

    comment = st.text_input(
        "Optional comment",
        key=f"cmt_{trace_id}",
        label_visibility="collapsed",
        placeholder="Add a comment (optional)",
    )

    if thumbs:
        try:
            client.send_feedback(trace_id, ss.get(state.SESSION_ID, ""), thumbs, comment)
            ss[state.FEEDBACK_SENT].add(trace_id)
            st.success("Feedback sent.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not send feedback: {exc}")
