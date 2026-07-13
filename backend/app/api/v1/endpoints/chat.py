from fastapi import APIRouter, HTTPException
from typing import Optional
import uuid

from app.models.schemas import ChatRequest, ChatResponse, UserRole
from app.agents.master_agent import get_master_agent

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for all stakeholder interactions.
    Routes to the appropriate agent based on query intent and user role.
    Handles graceful degradation: any agent failure returns a clear fallback response,
    never a raw stack trace.
    """
    session_id = request.session_id or str(uuid.uuid4())

    try:
        master_agent = get_master_agent()
        result = await master_agent.process_chat(
            message=request.message,
            session_id=session_id,
            role=request.role.value,
            language=request.language.value if hasattr(request.language, "value") else str(request.language),
            context=request.context or {},
        )

        # If the agent returned nothing usable, degrade gracefully
        response_text = result.get("response") or "I'm sorry, I couldn't process that request right now. Please try rephrasing, or contact the nearest volunteer for assistance."

        return ChatResponse(
            success=True,
            response=response_text,
            session_id=session_id,
            language=request.language,
            sources=result.get("sources", []),
            suggested_actions=result.get("suggested_actions", []),
            agent_used=result.get("agent_used"),
        )
    except Exception as e:
        # Never expose raw errors to fans — return a safe fallback
        return ChatResponse(
            success=False,
            response="I'm having trouble connecting to my systems right now. For urgent help, please find the nearest volunteer or use the emergency button.",
            session_id=session_id,
            language=request.language,
            sources=[],
            suggested_actions=["Contact nearest volunteer", "Use emergency button if urgent"],
            agent_used=None,
        )