"""POST /v1/chat — the main triage workflow. Invokes the compiled graph and serialises the
final state into the contract response shape (README §7)."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from telecom_agent.api.deps import Container, get_container
from telecom_agent.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    CitationOut,
    LlmInfoOut,
    TicketBrief,
)
from telecom_agent.api.schemas.common import UsageOut
from telecom_agent.core.enums import Alias, Provider, Resolution
from telecom_agent.core.types import CustomerCtx, TokenUsage
from telecom_agent.core.utils import new_session_id
from telecom_agent.observability import metrics
from telecom_agent.observability.cost import estimate_cost

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest, request: Request, container: Container = Depends(get_container)
) -> ChatResponse:
    trace_id = getattr(request.state, "trace_id", "")
    session_id = req.session_id or new_session_id()

    if req.customer_ctx:
        container.agent_deps.session_store.set_customer_ctx(
            session_id, CustomerCtx(**req.customer_ctx)
        )

    initial = {
        "session_id": session_id,
        "trace_id": trace_id,
        "user_input": req.message,
        "token_usage": TokenUsage(),
    }

    start = time.monotonic()
    final = container.graph.invoke(initial)
    latency_ms = int((time.monotonic() - start) * 1000)

    provider: Provider = final.get("provider", container.settings.default_provider)
    metrics.turn_latency_seconds.labels(provider=provider.value).observe(latency_ms / 1000)

    usage: TokenUsage = final.get("token_usage") or TokenUsage()
    ticket = final.get("ticket")
    return ChatResponse(
        trace_id=trace_id,
        session_id=session_id,
        category=final.get("category"),
        priority=final.get("priority"),
        resolution=final.get("resolution", Resolution.ESCALATED),
        answer=final.get("answer", ""),
        citations=[CitationOut(**c.model_dump()) for c in final.get("citations", [])],
        ticket=TicketBrief(
            ticket_id=ticket.ticket_id,
            queue=str(ticket.queue),
            priority=str(ticket.priority),
            status=str(ticket.status),
        )
        if ticket
        else None,
        llm=LlmInfoOut(
            provider=provider,
            alias=Alias.CHAT_MAIN.value,
            degraded=bool(final.get("degraded") or container.router.is_degraded(session_id)),
        ),
        usage=UsageOut(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            est_cost_usd=estimate_cost(provider, Alias.CHAT_MAIN, usage),
        ),
        latency_ms=latency_ms,
    )
