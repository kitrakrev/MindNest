"""API routes for Views simulation (message propagation)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.persona_service_db import persona_service_db
from services.llm_service import llm_service

router = APIRouter()


class EngagementRequest(BaseModel):
    """Request for engagement decision."""
    persona_id: str
    message: str


class EngagementResponse(BaseModel):
    """Response for engagement decision."""
    persona_id: str
    engage: bool
    reason: str
    priority: float


@router.post("/decide-engagement", response_model=EngagementResponse)
async def decide_engagement(
    request: EngagementRequest
) -> EngagementResponse:
    """
    Ask a persona's LLM if they would engage with and share a message.
    
    This is used in the Views simulation to determine message propagation
    based on persona personalities rather than random chance.
    """
    # Get persona from database
    persona = await persona_service_db.get_persona(request.persona_id)
    
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona {request.persona_id} not found")
    
    # Get LLM decision
    decision = await llm_service.decide_engagement(persona, request.message)
    
    return EngagementResponse(
        persona_id=request.persona_id,
        engage=decision["engage"],
        reason=decision["reason"],
        priority=decision["priority"]
    )

