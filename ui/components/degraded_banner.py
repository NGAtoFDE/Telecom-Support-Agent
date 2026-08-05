"""
Enterprise Degraded Mode Banner

Shows a highly visible failover alert when the
backup LLM provider is serving requests.

Requirement:
Degraded mode must never be silent.
"""

from __future__ import annotations

import streamlit as st


def _inject_styles() -> None:
    st.markdown(
        """
        <style>

        .degraded-alert {
            background: linear-gradient(
                90deg,
                #fef3c7,
                #fde68a
            );
            border: 1px solid #f59e0b;
            border-left: 6px solid #d97706;
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(217,119,6,0.15);
        }

        .degraded-title {
            font-size: 15px;
            font-weight: 700;
            color: #92400e;
            margin-bottom: 6px;
        }

        .degraded-text {
            font-size: 13px;
            color: #78350f;
            line-height: 1.6;
        }

        .provider-chip {
            display:inline-block;
            padding:4px 10px;
            border-radius:999px;
            background:#ffffff;
            border:1px solid #f59e0b;
            color:#92400e;
            font-weight:600;
            font-size:12px;
            margin-top:8px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_degraded_banner(
    response: dict | None,
) -> None:

    if not response:
        return

    llm = response.get("llm", {})

    if not llm.get("degraded"):
        return

    _inject_styles()

    provider = llm.get(
        "provider",
        "backup provider"
    )

    alias = llm.get(
        "alias",
        "unknown model"
    )

    st.markdown(
        f"""
        <div class="degraded-alert">

            <div class="degraded-title">
                ⚠️ Service Degradation Detected
            </div>

            <div class="degraded-text">
                The primary AI provider is currently unavailable.
                Requests are being automatically served through a
                backup model to maintain service continuity.
                Response quality, reasoning patterns and output
                formatting may differ from the primary model.
            </div>

            <div class="provider-chip">
                Active Provider: {provider}
            </div>

            <div class="provider-chip">
                Model: {alias}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )