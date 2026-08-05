"""
Enterprise Conversation Thread UI

Modern telecom support assistant conversation experience.
"""

from __future__ import annotations

import streamlit as st

from ui.components.citation_card import render_citations

_PRIORITY_COLOR = {
    "P1": "#dc2626",
    "P2": "#ea580c",
    "P3": "#ca8a04",
    "P4": "#2563eb",
}

_RESOLUTION_COLOR = {
    "RESOLVED": "#16a34a",
    "ESCALATED": "#dc2626",
    "NEEDS_INFO": "#ca8a04",
}


def inject_chat_styles() -> None:
    st.markdown(
        """
        <style>

        .chat-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 16px 18px;
            margin-top: 8px;
            margin-bottom: 10px;
            box-shadow: 0 2px 8px rgba(15,23,42,0.05);
        }

        .assistant-card {
            background: linear-gradient(
                180deg,
                #ffffff 0%,
                #f8fafc 100%
            );
            border-left: 4px solid #2563eb;
        }

        .user-card {
            background: #ffffff;
            border-left: 4px solid #64748b;
        }

        .assistant-title {
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.8px;
            color: #64748b;
            margin-bottom: 10px;
        }

        .message-content {
            color: #0f172a;
            line-height: 1.75;
            font-size: 15px;
        }

        .meta-row {
            margin-bottom: 12px;
        }

        .modern-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            margin-right: 6px;
            margin-bottom: 6px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }

        .source-heading {
            margin-top: 12px;
            margin-bottom: 8px;
            font-size: 13px;
            font-weight: 700;
            color: #475569;
        }

        .escalation-banner {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
            border-radius: 12px;
            padding: 10px;
            margin-bottom: 12px;
            font-size: 13px;
            font-weight: 600;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def badge(label: str, color: str) -> str:
    return f"""
    <span
    class="modern-pill"
    style="
        background:{color}15;
        color:{color};
        border:1px solid {color}50;
    ">
        {label}
    </span>
    """


def render_message_meta(meta: dict) -> None:
    badges = ""

    if meta.get("category"):
        badges += badge(
            f"📂 {meta['category']}",
            "#475569",
        )

    if meta.get("priority"):
        badges += badge(
            f"⚠️ {meta['priority']}",
            _PRIORITY_COLOR.get(
                meta["priority"],
                "#475569"
            ),
        )

    if meta.get("resolution"):
        badges += badge(
            f"✅ {meta['resolution']}",
            _RESOLUTION_COLOR.get(
                meta["resolution"],
                "#475569"
            ),
        )

    if badges:
        st.markdown(
            f"<div class='meta-row'>{badges}</div>",
            unsafe_allow_html=True,
        )


def render_thread(messages: list[dict]) -> None:

    inject_chat_styles()

    for msg in messages:

        role = msg["role"]
        is_user = role == "user"

        avatar = "👨‍💻" if is_user else "🤖"

        with st.chat_message(role, avatar=avatar):

            meta = msg.get("meta") or {}

            card_class = (
                "chat-card user-card"
                if is_user
                else "chat-card assistant-card"
            )

            st.markdown(
                f"<div class='{card_class}'>",
                unsafe_allow_html=True,
            )

            if not is_user:
                st.markdown(
                    """
                    <div class='assistant-title'>
                        TELECOM SUPPORT COPILOT
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if meta.get("resolution") == "ESCALATED":
                st.markdown(
                    """
                    <div class='escalation-banner'>
                        🚨 This issue has been escalated to the Network Operations Team
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            render_message_meta(meta)

            st.markdown(
                f"""
                <div class="message-content">
                    {msg["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

            if meta.get("citations"):

                st.markdown(
                    """
                    <div class='source-heading'>
                        📚 Knowledge Sources
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                render_citations(
                    meta["citations"]
                )

            if not is_user:

                confidence = meta.get("confidence")

                if confidence:
                    st.progress(
                        float(confidence) / 100
                    )

                    st.caption(
                        f"Confidence Score: {confidence}%"
                    )

            ticket_id = meta.get("ticket_id")

            if ticket_id:
                st.caption(
                    f"🎫 Ticket ID: {ticket_id}"
                )

            timeline = meta.get("timeline")

            if timeline:

                with st.expander(
                    "📈 Resolution Timeline",
                    expanded=False,
                ):

                    for step in timeline:
                        st.write(
                            f"• {step}"
                        )


def chat_input_box() -> str | None:

    return st.chat_input(
        "🔍 Describe issue, location, affected service, customer complaint, or ticket ID..."
    )