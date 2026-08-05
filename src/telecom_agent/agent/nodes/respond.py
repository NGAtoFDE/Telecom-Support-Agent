"""respond — formats the final reply, narrows citations to those actually referenced in
the answer, and stamps the degraded flag. Runs only on the grounded path.
"""

from __future__ import annotations

import re

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.state import TriageState
from telecom_agent.core.enums import Resolution
from telecom_agent.core.types import Message
from telecom_agent.observability.logging import bind

_CITE = re.compile(r"\b(KB-\d+|[A-Z]+-\d+)\b")


def respond(state: TriageState, deps: AgentDeps) -> dict:
    session_id = state["session_id"]
    log = bind(__name__, trace_id=state.get("trace_id", ""), session_id=session_id, node="respond")
    draft = state.get("draft", "")
    all_citations = state.get("citations", [])

    referenced_ids = set(_CITE.findall(draft))
    cited = [c for c in all_citations if c.doc_id in referenced_ids]
    if not cited:  # answer didn't emit ids we recognise → fall back to top evidence
        cited = all_citations[:3]

    deps.session_store.append(session_id, Message(role="assistant", content=draft))
    log.info("responded", extra={"citations": [c.doc_id for c in cited]})
    return {
        "answer": draft,
        "citations": cited,
        "resolution": Resolution.RESOLVED,
        "ticket": None,
    }
