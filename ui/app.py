"""Telecom Support Agent — Streamlit support console.

A pure API client (README §8): it renders chat, citations, the ticket panel, a feedback
widget, a degraded-mode banner and a debug drawer, and it never imports from the
``telecom_agent`` package. Run with:  ``streamlit run ui/app.py``

Environment:
    API_BASE_URL   default http://localhost:8000
    API_KEY        default dev-key-change-me
"""

from __future__ import annotations

import sys
from pathlib import Path

# `streamlit run ui/app.py` puts ui/ on sys.path, not the repo root. Add the repo root so
# the `ui` package (and its components) import cleanly regardless of the launch directory.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st  # noqa: E402

from ui import state  # noqa: E402
from ui.api_client import ApiClient, ApiError  # noqa: E402
from ui.components.chat_panel import chat_input_box, render_thread  # noqa: E402
from ui.components.debug_drawer import render_debug_drawer  # noqa: E402
from ui.components.degraded_banner import render_degraded_banner  # noqa: E402
from ui.components.feedback_widget import render_feedback_widget  # noqa: E402
from ui.components.ticket_panel import render_ticket_panel  # noqa: E402

st.set_page_config(page_title="Telecom Support Agent", page_icon="📡", layout="wide")


def _load_css() -> None:
    css_path = Path(__file__).parent / "theme" / "styles.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True
        )


def main() -> None:
    _load_css()
    state.bootstrap()
    client = ApiClient()
    ss = st.session_state

    # ---- header ----
    st.markdown("<h2 class='console-title'>📡 Telecom Support Agent</h2>", unsafe_allow_html=True)
    st.caption("Network issue triage & escalation · synthetic data only · not a real service")
    render_degraded_banner(ss.get(state.LAST_RESPONSE))

    # ---- sidebar ----
    with st.sidebar:
        st.markdown("### Session")
        st.code(ss[state.SESSION_ID], language=None)
        if st.button("🔄 New conversation", use_container_width=True):
            state.reset_conversation()
            st.rerun()

        st.divider()
        # readiness indicator
        try:
            ready = client.readyz()
            ok = ready.get("ready", False)
            st.markdown(f"**API:** {'🟢 ready' if ok else '🟠 degraded/not ready'}")
            with st.expander("readiness checks"):
                st.json(ready.get("checks", {}))
        except ApiError as exc:
            st.markdown(f"**API:** 🔴 unreachable — {exc.message}")

        st.divider()
        render_ticket_panel(client, ss.get(state.LAST_RESPONSE))
        st.divider()
        render_feedback_widget(client)

    # ---- main column: chat ----
    left, right = st.columns([3, 2])
    with left:
        render_thread(ss[state.MESSAGES])

    with right:
        render_debug_drawer(client)

    # ---- input ----
    prompt = chat_input_box()
    if prompt:
        ss[state.MESSAGES].append({"role": "user", "content": prompt})
        with st.spinner("Triaging…"):
            try:
                resp = client.chat(prompt, session_id=ss[state.SESSION_ID])
            except ApiError as exc:
                ss[state.MESSAGES].append(
                    {
                        "role": "assistant",
                        "content": f"⚠️ {exc.message} (code: `{exc.code}`)",
                    }
                )
                st.rerun()
                return

        resp["_last_message"] = prompt
        ss[state.LAST_RESPONSE] = resp
        ss[state.LAST_TRACE_ID] = resp.get("trace_id", "")
        ss[state.SESSION_ID] = resp.get("session_id", ss[state.SESSION_ID])
        ss[state.DEGRADED] = resp.get("llm", {}).get("degraded", False)
        ss[state.MESSAGES].append(
            {
                "role": "assistant",
                "content": resp.get("answer", ""),
                "meta": {
                    "category": resp.get("category"),
                    "priority": resp.get("priority"),
                    "resolution": resp.get("resolution"),
                    "citations": resp.get("citations", []),
                },
            }
        )
        st.rerun()


if __name__ == "__main__":
    main()
