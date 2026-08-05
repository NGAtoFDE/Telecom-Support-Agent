"""
Enterprise Feedback Widget

Captures user satisfaction for a specific trace_id.

Features:
- Thumbs up/down
- Optional comments
- Duplicate submission prevention
- Enterprise UI
"""

from __future__ import annotations

import streamlit as st

from ui import state


def _inject_styles() -> None:
    st.markdown(
        """
        <style>

        .feedback-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 18px;
            margin-top: 12px;
            box-shadow: 0 2px 8px rgba(15,23,42,0.05);
        }

        .feedback-title {
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 4px;
        }

        .feedback-subtitle {
            color: #64748b;
            font-size: 13px;
            margin-bottom: 12px;
        }

        .success-box {
            background: #ecfdf5;
            border: 1px solid #86efac;
            border-radius: 12px;
            padding: 12px;
            color: #166534;
            font-weight: 600;
        }

        .trace-chip {
            display: inline-block;
            background: #f1f5f9;
            color: #475569;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 12px;
            margin-top: 10px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_feedback_widget(client) -> None:

    ss = st.session_state

    trace_id = ss.get(state.LAST_TRACE_ID) or ""

    if not trace_id:
        return

    _inject_styles()

    already_sent = trace_id in ss.get(
        state.FEEDBACK_SENT,
        set(),
    )

    with st.container():

        st.markdown(
            """
            <div class="feedback-card">

                <div class="feedback-title">
                    💬 Response Feedback
                </div>

                <div class="feedback-subtitle">
                    Help improve response quality by rating this answer.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if already_sent:

            st.markdown(
                """
                <div class="success-box">
                    ✅ Thanks! Feedback has already been recorded for this response.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption(
                f"Trace ID: {trace_id}"
            )

            return

        sentiment = None

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "👍 Helpful",
                use_container_width=True,
                key=f"up_{trace_id}",
            ):
                sentiment = "up"

        with col2:
            if st.button(
                "👎 Not Helpful",
                use_container_width=True,
                key=f"down_{trace_id}",
            ):
                sentiment = "down"

        comment = st.text_area(
            "Additional Feedback",
            key=f"comment_{trace_id}",
            height=90,
            placeholder=(
                "Tell us what worked well, "
                "what was missing, or how the response can improve..."
            ),
        )

        st.caption(
            f"Trace ID: {trace_id}"
        )

        if sentiment:

            try:

                with st.spinner(
                    "Submitting feedback..."
                ):

                    client.send_feedback(
                        trace_id,
                        ss.get(
                            state.SESSION_ID,
                            "",
                        ),
                        sentiment,
                        comment,
                    )

                ss[state.FEEDBACK_SENT].add(
                    trace_id
                )

                st.success(
                    "✅ Feedback submitted successfully."
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Unable to submit feedback: {exc}"
                )