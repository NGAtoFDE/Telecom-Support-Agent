"""Discord webhook integration (Interactions API)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, BackgroundTasks
from pydantic import BaseModel
import httpx

try:
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
    HAVE_NACL = True
except ImportError:
    HAVE_NACL = False

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.state import TriageState
from telecom_agent.api.deps import Container, get_container
from telecom_agent.config.settings import Settings, get_settings
from telecom_agent.core.types import Message

router = APIRouter(prefix="/v1/discord", tags=["discord"])
log = logging.getLogger(__name__)

class DiscordInteraction(BaseModel):
    type: int
    data: dict[str, Any] | None = None
    member: dict[str, Any] | None = None
    user: dict[str, Any] | None = None
    token: str | None = None

def verify_signature(request: Request, body: bytes, settings: Settings) -> None:
    if not HAVE_NACL:
        raise HTTPException(status_code=500, detail="PyNaCl not installed")
    
    public_key = settings.discord_public_key
    if not public_key:
        raise HTTPException(status_code=500, detail="Discord public key not configured")
        
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    
    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="Missing signature headers")
        
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
    except BadSignatureError:
        raise HTTPException(status_code=401, detail="Invalid request signature")

def run_agent_in_background(
    user_msg: str,
    session_id: str,
    trace_id: str,
    container: Container,
    interaction_token: str,
    app_id: str
):
    state = TriageState(
        session_id=session_id,
        trace_id=trace_id,
        user_input=user_msg,
        messages=[Message(role="user", content=user_msg)]
    )
    
    result_state = container.graph.invoke(state)
    answer = result_state.get("draft") or result_state.get("answer") or "I couldn't process that."
    
    citations = result_state.get("citations", [])
    if citations:
        answer += "\n\n**Sources:**\n"
        for c in citations:
            answer += f"- {c.doc_id} §{c.section}\n"
            
    if result_state.get("ticket"):
        answer += f"\n\n🎫 Ticket Created: {result_state['ticket'].ticket_id}"

    url = f"https://discord.com/api/v10/webhooks/{app_id}/{interaction_token}/messages/@original"
    try:
        httpx.patch(url, json={"content": answer})
    except Exception as e:
        log.error(f"Failed to update discord interaction: {e}")

@router.post("/webhook")
async def discord_webhook(
    interaction: DiscordInteraction,
    request: Request,
    background_tasks: BackgroundTasks,
    container: Container = Depends(get_container)
) -> dict:
    body = await request.body()
    verify_signature(request, body, container.settings)
    
    # 1: PING
    if interaction.type == 1:
        return {"type": 1}
        
    # 2: APPLICATION_COMMAND
    if interaction.type == 2 and interaction.data:
        command_name = interaction.data.get("name")
        if command_name == "support":
            # Extract user message from options
            options = interaction.data.get("options", [])
            user_msg = next((opt["value"] for opt in options if opt["name"] == "issue"), "")
            
            if not user_msg:
                return {
                    "type": 4, # CHANNEL_MESSAGE_WITH_SOURCE
                    "data": {"content": "Please describe your issue."}
                }
            
            # Setup session
            session_id = "discord_" + str(interaction.member.get("user", {}).get("id") if interaction.member else "unknown")
            trace_id = getattr(request.state, "trace_id", "")
            
            # Defer execution to background task
            background_tasks.add_task(
                run_agent_in_background,
                user_msg=user_msg,
                session_id=session_id,
                trace_id=trace_id,
                container=container,
                interaction_token=interaction.token or "",
                app_id=container.settings.discord_app_id
            )
            
            # 5: DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
            return {
                "type": 5
            }
            
    return {"type": 4, "data": {"content": "Command not recognized."}}
