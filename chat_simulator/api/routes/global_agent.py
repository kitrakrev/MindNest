"""
Global Agent API Routes

This module provides REST API endpoints for the Global Meta-Advisor,
including advice generation, conversation analysis, and memory management.

Supports both traditional global agent and Letta-powered agent (when enabled).
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from typing import Optional

from services.global_agent_service import global_agent_service
from services.letta_global_agent_service import letta_global_agent_service
from services.message_service_db import message_service_db
from core.config import settings


router = APIRouter()


class GlobalAgentRequest(BaseModel):
    """Request model for global agent advice."""
    
    question: str = Field(..., description="User's question for the global agent", min_length=1)
    session_id: Optional[str] = Field(None, description="Optional session ID for context")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What patterns do you see in my conversations?",
                "session_id": "sim_123abc"
            }
        }


class GlobalAgentResponse(BaseModel):
    """Response model from global agent."""
    
    advice: str = Field(..., description="Generated advice from the global agent")
    context_size: int = Field(..., description="Number of messages analyzed")

    class Config:
        json_schema_extra = {
            "example": {
                "advice": "Based on your conversations, I notice...",
                "context_size": 15
            }
        }


@router.post("/advice", response_model=GlobalAgentResponse)
async def get_global_advice(
    request_data: GlobalAgentRequest,
    request: Request
) -> GlobalAgentResponse:
    """
    Get strategic advice from the global meta-agent.
    
    The global agent analyzes conversation patterns and provides high-level
    insights based on all available context and its accumulated memory.
    
    **NEW**: If LETTA_ENABLED=True, uses Letta's stateful memory system for
    persistent, evolving agent intelligence. Otherwise, uses traditional memory.
    
    Args:
        request_data: Request containing question and optional session ID
        request: FastAPI request object
        
    Returns:
        GlobalAgentResponse with advice and context size
    """
    # Collect messages from the database (persistent source of truth)
    if request_data.session_id:
        messages = await message_service_db.get_recent_messages(
            request_data.session_id,
            limit=100
        )
    else:
        messages = []
    
    # Choose service based on Letta configuration
    agent_service = letta_global_agent_service if settings.LETTA_ENABLED else global_agent_service
        
    # Generate advice from the global agent
    advice = await agent_service.get_advice(
        all_messages=messages,
        user_question=request_data.question,
        session_id=request_data.session_id
    )
    
    return GlobalAgentResponse(
        advice=advice,
        context_size=len(messages)
    )


@router.get("/analysis/{session_id}")
async def get_conversation_analysis(
    session_id: str,
    request: Request
):
    """
    Get detailed analysis of a specific conversation session.
    
    Provides statistics and AI-generated summary of the conversation,
    including participant counts and key themes.
    
    Uses Letta if enabled, otherwise uses traditional analysis.
    
    Args:
        session_id: The simulation session ID to analyze
        request: FastAPI request object
        
    Returns:
        Dictionary with analysis metrics and summary
    """
    # Get messages from database
    messages = await message_service_db.get_recent_messages(session_id, limit=100)
    
    # Choose service based on Letta configuration
    agent_service = letta_global_agent_service if settings.LETTA_ENABLED else global_agent_service
    
    analysis = await agent_service.get_conversation_analysis(
        messages=messages,
        session_id=session_id
    )
    
    return analysis


@router.get("/history")
async def get_global_agent_history():
    """
    Get the global agent's recent query history.
    
    Returns the last 10 interactions with the global agent,
    including questions asked and advice given.
    
    Returns:
        Dictionary with history list and total query count
    """
    agent_service = letta_global_agent_service if settings.LETTA_ENABLED else global_agent_service
    
    # For Letta, use fallback_history; for traditional, use conversation_history
    if settings.LETTA_ENABLED:
        history = agent_service.fallback_history[-10:]
        total = len(agent_service.fallback_history)
    else:
        history = agent_service.conversation_history[-10:]
        total = len(agent_service.conversation_history)
    
    return {
        "history": history,
        "total_queries": total,
        "using_letta": settings.LETTA_ENABLED
    }


@router.get("/memory/stats")
async def get_memory_stats():
    """
    Get statistics about the global agent's memory.
    
    Provides counts of short-term memories, long-term memories,
    total queries, and stored session summaries.
    
    When Letta is enabled, provides Letta-specific memory statistics.
    
    Returns:
        Dictionary with memory statistics
    """
    agent_service = letta_global_agent_service if settings.LETTA_ENABLED else global_agent_service
    return agent_service.get_memory_stats()


@router.get("/memory/content")
async def get_memory_content():
    """
    Get the actual content of the global agent's memory.
    
    Returns recent short-term and long-term memories with their
    timestamps and importance scores.
    
    When Letta is enabled, returns Letta memory blocks and state.
    
    Returns:
        Dictionary with memory content (format depends on Letta enabled/disabled)
    """
    agent_service = letta_global_agent_service if settings.LETTA_ENABLED else global_agent_service
    return agent_service.get_memory_content()


@router.get("/status")
async def get_global_agent_status():
    """
    Get the status of the global agent including Letta integration info.
    
    Returns:
        Dictionary with status information
    """
    return {
        "letta_enabled": settings.LETTA_ENABLED,
        "letta_configured": settings.LETTA_API_KEY != "letta_api_key_placeholder",
        "letta_agent_name": settings.LETTA_AGENT_NAME if settings.LETTA_ENABLED else None,
        "service_type": "letta" if settings.LETTA_ENABLED else "traditional",
        "docs": "https://docs.letta.com/overview"
    }

