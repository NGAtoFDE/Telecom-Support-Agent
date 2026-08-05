"""Ticket panel: the ticket raised on the last turn (if any) plus a peek at recent tickets.

Talks to the API through the injected ApiClient only.
"""

from __future__ import annotations

import streamlit as st

_PRIORITY_COLOR = {"P1": "#dc2626", "P2": "#ea580c", "P3": "#ca8a04", "P4": "#2563eb"}
_STATUS_COLOR = {
    "OPEN": "#dc2626",
    "IN_PROGRESS": "#ca8a04",
    "RESOLVED": "#16a34a",
    "CLOSED": "#6b7280",
}


def _badge(label: str, color: str) -> str:
    return (
        f"<span style='background:{color};color:white;padding:2px 8px;border-radius:10px;"
        f"font-size:0.72em;font-weight:600;margin-right:4px'>{label}</span>"
    )


def render_ticket_panel(client, last_response: dict | None) -> None:
    st.markdown("#### 🎫 Ticket")
    ticket = (last_response or {}).get("ticket")
    if ticket:
        badges = (
            _badge(ticket.get("queue", "?"), "#334155")
            + _badge(
                ticket.get("priority", "?"), _PRIORITY_COLOR.get(ticket.get("priority"), "#334155")
            )
            + _badge(ticket.get("status", "?"), _STATUS_COLOR.get(ticket.get("status"), "#334155"))
        )
        st.markdown(f"**`{ticket.get('ticket_id')}`**", unsafe_allow_html=True)
        st.markdown(badges, unsafe_allow_html=True)
    else:
        st.caption("No ticket for the latest turn (issue resolved or awaiting info).")

    with st.expander("Recent tickets", expanded=False):
        try:
            tickets = client.list_tickets(limit=10)
        except Exception as exc:  # noqa: BLE001
            st.caption(f"Could not load tickets: {exc}")
            return
        if not tickets:
            st.caption("No tickets yet.")
        for t in tickets:
            st.markdown(
                f"`{t.get('ticket_id')}` · {t.get('queue')} · "
                f"{t.get('priority')} · {t.get('status')}"
            )
