# Streamlit Support Console

A **pure API client** for the Telecom Support Agent. It talks to the FastAPI service over
HTTP only and never imports from the `telecom_agent` package (README §8 boundary rule).

## Run

Start the API first (from the repo root):

```bash
LLM_PROVIDER=fake make dev        # or: uvicorn telecom_agent.api.main:app --port 8000
```

Then launch the console:

```bash
export API_BASE_URL=http://localhost:8000    # default
export API_KEY=dev-key-change-me             # must match the API's API_KEY
streamlit run ui/app.py
```

On Windows PowerShell:

```powershell
$env:API_BASE_URL = "http://localhost:8000"
$env:API_KEY = "dev-key-change-me"
streamlit run ui/app.py
```

## Environment

| Var | Default | Purpose |
|---|---|---|
| `API_BASE_URL` | `http://localhost:8000` | Base URL of the FastAPI service |
| `API_KEY` | `dev-key-change-me` | Sent as `X-API-Key`; must match the API |

## Layout

- **Chat** (centre): the triage conversation, with category/priority/resolution badges and
  an expandable **citation card** under each assistant turn.
- **Degraded banner** (top): appears when a turn was served from the Groq backup.
- **Sidebar**: session controls, live `/readyz` indicator, **ticket panel**, **feedback widget**.
- **Debug drawer** (right): provider, tokens, cost, latency, and on-demand classification —
  the "demo gold" view.

## Files

| File | Role |
|---|---|
| `app.py` | Entrypoint, layout, session bootstrap, the one place the chat call is issued |
| `api_client.py` | Typed HTTP wrapper — the only place URLs appear |
| `state.py` | All `st.session_state` keys + bootstrap/reset |
| `components/chat_panel.py` | Message thread + input box |
| `components/citation_card.py` | Expandable source view |
| `components/ticket_panel.py` | Last-turn ticket + recent tickets |
| `components/feedback_widget.py` | Thumbs + comment, keyed to `trace_id` |
| `components/degraded_banner.py` | Backup-provider warning |
| `components/debug_drawer.py` | Category/provider/tokens/cost/latency |
| `theme/styles.css` | Minimal console styling |
