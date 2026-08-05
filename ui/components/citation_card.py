"""
Enterprise Knowledge Source Viewer

Displays citations referenced by the assistant
in a modern expandable source panel.
"""

from __future__ import annotations

import streamlit as st


def inject_citation_styles() -> None:
    st.markdown(
        """
        <style>

        .source-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 14px;
            margin-bottom: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }

        .source-header {
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:8px;
        }

        .source-title {
            font-size:15px;
            font-weight:600;
            color:#0f172a;
        }

        .doc-id {
            background:#f1f5f9;
            color:#475569;
            padding:4px 10px;
            border-radius:999px;
            font-size:11px;
            font-weight:600;
        }

        .source-meta {
            font-size:13px;
            color:#64748b;
            margin-bottom:10px;
        }

        .relevance-label {
            font-size:12px;
            color:#64748b;
            margin-bottom:4px;
            font-weight:600;
        }

        .score-pill {
            display:inline-block;
            padding:4px 10px;
            border-radius:999px;
            font-size:12px;
            font-weight:600;
            margin-top:6px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def get_score_color(score: float) -> str:

    if score >= 0.85:
        return "#16a34a"

    if score >= 0.70:
        return "#2563eb"

    if score >= 0.50:
        return "#ca8a04"

    return "#dc2626"


def get_doc_icon(title: str) -> str:

    title = title.lower()

    if ".pdf" in title:
        return "📕"

    if ".docx" in title:
        return "📘"

    if ".xlsx" in title:
        return "📗"

    if ".csv" in title:
        return "📊"

    return "📄"


def render_citations(citations: list[dict]) -> None:

    if not citations:
        return

    inject_citation_styles()

    with st.expander(
        f"📚 Knowledge Sources ({len(citations)})",
        expanded=False,
    ):

        st.caption(
            "Reference documents used to generate this response"
        )

        for citation in citations:

            score = float(
                citation.get("score", 0.0)
            )

            score_color = get_score_color(score)

            title = citation.get(
                "title",
                "Unknown Document"
            )

            doc_id = citation.get(
                "doc_id",
                "N/A"
            )

            section = citation.get(
                "section",
                "N/A"
            )

            icon = get_doc_icon(title)

            st.markdown(
                f"""
                <div class="source-card">

                    <div class="source-header">
                        <div class="source-title">
                            {icon} {title}
                        </div>

                        <div class="doc-id">
                            {doc_id}
                        </div>
                    </div>

                    <div class="source-meta">
                        Section: <b>{section}</b>
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="relevance-label">
                    Relevance Score ({score:.2f})
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.progress(
                min(max(score, 0.0), 1.0)
            )

            st.markdown(
                f"""
                <span
                class="score-pill"
                style="
                    background:{score_color}20;
                    color:{score_color};
                    border:1px solid {score_color}50;
                ">
                    Match Confidence: {score:.0%}
                </span>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)