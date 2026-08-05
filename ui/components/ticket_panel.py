"""
Enterprise Ticket Panel

Displays:
- Active incident from latest interaction
- Queue / Priority / Status badges
- Incident status guidance
- Recent ticket history

Uses only the injected ApiClient.
"""

from __future__ import annotations

import streamlit as st

_PRIORITY_COLOR = {
    "P1": "#dc2626",
    "P2": "#ea580c",
    "P3": "#ca8a04",
    "P4": "#2563eb",
}

_STATUS_COLOR = {
    "OPEN": "#dc2626",
    "IN_PROGRESS": "#ca8a04",
    "RESOLVED": "#16a34a",
    "CLOSED": "#6b7280",
}


def _inject_styles() -> None:
    st.markdown(
        """
        <style>

        .ticket-header{
            margin-bottom:12px;
        }

        .ticket-card{
            background:white;
            border:1px solid #e2e8f0;
            border-radius:16px;
            padding:16px;
            margin-bottom:16px;
            box-shadow:0 2px 10px rgba(15,23,42,0.05);
        }

        .ticket-id{
            font-size:20px;
            font-weight:700;
            color:#0f172a;
            margin-bottom:10px;
        }

        .ticket-chip{
            display:inline-block;
            padding:5px 10px;
            border-radius:999px;
            color:white;
            font-size:12px;
            font-weight:600;
            margin-right:6px;
            margin-bottom:6px;
        }

        .empty-ticket{
            background:#f8fafc;
            border:1px dashed #cbd5e1;
            border-radius:14px;
            padding:18px;
            text-align:center;
            color:#64748b;
        }

        .recent-card{
            background:#f8fafc;
            border:1px solid #e2e8f0;
            border-radius:12px;
            padding:12px;
            margin-bottom:8px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def _chip(label: str, color: str) -> str:
    return (
        f"<span class='ticket-chip' "
        f"style='background:{color};'>"
        f"{label}</span>"
    )


def render_ticket_panel(client, last_response: dict | None) -> None:

    _inject_styles()

    st.markdown("### 🎫 Incident Management")

    ticket = (last_response or {}).get("ticket")

    # =====================================================
    # CURRENT TICKET
    # =====================================================

    if ticket:

        ticket_id = ticket.get("ticket_id", "N/A")
        queue = ticket.get("queue", "Unknown")
        priority = ticket.get("priority", "P4")
        status = ticket.get("status", "OPEN")

        st.markdown(
            f"""
            <div class="ticket-card">

                <div class="ticket-id">
                    🎫 {ticket_id}
                </div>

                {_chip(queue, "#334155")}
                {_chip(priority, _PRIORITY_COLOR.get(priority, "#334155"))}
                {_chip(status, _STATUS_COLOR.get(status, "#334155"))}

            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Priority", priority)

        with col2:
            st.metric("Status", status)

        if status == "OPEN":
            st.error(
                "🚨 Incident created and awaiting assignment."
            )

        elif status == "IN_PROGRESS":
            st.warning(
                "🛠 Support team is actively investigating."
            )

        elif status == "RESOLVED":
            st.success(
                "✅ Incident resolved successfully."
            )

        elif status == "CLOSED":
            st.info(
                "📁 Incident has been closed."
            )

    else:

        st.markdown(
            """
            <div class="empty-ticket">
                ✅ No ticket generated for the latest interaction.<br>
                The issue was resolved automatically or requires more information.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # =====================================================
    # RECENT INCIDENTS
    # =====================================================

    with st.expander("📋 Recent Incidents", expanded=False):

        try:
            tickets = client.list_tickets(limit=10)

        except Exception as exc:
            st.error(
                f"Unable to load tickets: {exc}"
            )
            return

        if not tickets:
            st.info("No incident history available.")
            return

        for t in tickets:

            ticket_id = t.get("ticket_id", "N/A")
            queue = t.get("queue", "Unknown")
            priority = t.get("priority", "P4")
            status = t.get("status", "OPEN")

            st.markdown(
                f"""
                <div class="recent-card">
                    <b>{ticket_id}</b><br><br>
                    {_chip(queue, "#334155")}
                    {_chip(priority, _PRIORITY_COLOR.get(priority, "#334155"))}
                    {_chip(status, _STATUS_COLOR.get(status, "#334155"))}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # =====================================================
    # QUICK SUMMARY
    # =====================================================

    with st.expander("📊 Ticket Summary", expanded=False):

        try:
            tickets = client.list_tickets(limit=50)

            total = len(tickets)

            open_count = sum(
                1 for t in tickets
                if t.get("status") == "OPEN"
            )

            progress_count = sum(
                1 for t in tickets
                if t.get("status") == "IN_PROGRESS"
            )

            resolved_count = sum(
                1 for t in tickets
                if t.get("status") == "RESOLVED"
            )

            closed_count = sum(
                1 for t in tickets
                if t.get("status") == "CLOSED"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Total", total)
            c2.metric("Open", open_count)
            c3.metric("In Progress", progress_count)
            c4.metric("Resolved", resolved_count + closed_count)

        except Exception:
            st.caption("Summary unavailable.")