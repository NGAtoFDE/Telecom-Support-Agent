"""Streamlit session-state keys in one typed place.

Keeping every ``st.session_state`` key here (rather than sprinkled through components)
means there is a single list of what persists across reruns, and a single bootstrap call.
"""

from __future__ import annotations

import uuid

import streamlit as st

# session_state keys
SESSION_ID = "session_id"
MESSAGES = "messages"  # list[dict]: {role, content, meta?}
LAST_TRACE_ID = "last_trace_id"
LAST_RESPONSE = "last_response"  # the full /v1/chat response dict
DEGRADED = "degraded"
FEEDBACK_SENT = "feedback_sent"  # trace_ids we've already sent feedback for


def bootstrap() -> None:
    """Initialise session state once per browser session."""
    ss = st.session_state
    if SESSION_ID not in ss:
        ss[SESSION_ID] = "sess_" + uuid.uuid4().hex[:8]
    ss.setdefault(MESSAGES, [])
    ss.setdefault(LAST_TRACE_ID, "")
    ss.setdefault(LAST_RESPONSE, None)
    ss.setdefault(DEGRADED, False)
    ss.setdefault(FEEDBACK_SENT, set())


def reset_conversation() -> None:
    ss = st.session_state
    ss[SESSION_ID] = "sess_" + uuid.uuid4().hex[:8]
    ss[MESSAGES] = []
    ss[LAST_TRACE_ID] = ""
    ss[LAST_RESPONSE] = None
    ss[DEGRADED] = False
    ss[FEEDBACK_SENT] = set()
