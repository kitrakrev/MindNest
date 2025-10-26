"""API routes for chat functionality."""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Request
from typing import List, Optional
import uuid
import json

from models.message import Message, MessageCreate, MessageRole, MessageStatus
from models.simulation import TLDRRequest, TLDRResponse
from services.llm_service import llm_service
from services.persona_service_db import persona_service_db as persona_service
from services.message_service_db import message_service_db


router = APIRouter()


@router.post("/message", response_model=Message)
async def send_message(message_data: MessageCreate, session_id: str, request: Request):
    """Send a message in a chat session."""
    queue_manager = request.app.state.queue_manager
    
    # Validate persona if specified
    if message_data.persona_id:
        persona = await persona_service.get_persona(message_data.persona_id)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
    
    # Generate message ID
    message_id = f"msg_{uuid.uuid4().hex[:8]}"
    
    # Save message to database (source of truth)
    message = await message_service_db.create_message(
        message_data=message_data,
        session_id=session_id,
        message_id=message_id
    )
    
    # Also add to queue for real-time processing/notifications
    if message.role == MessageRole.USER:
        await queue_manager.add_completed_message(session_id, message)
    else:
        await queue_manager.enqueue_message(session_id, message)
    
    return message


@router.get("/messages/{session_id}", response_model=List[Message])
async def get_messages(
    session_id: str,
    limit: int = 50,
    request: Request = None
):
    """Get messages from a chat session (from database)."""
    # Read from database (source of truth)
    messages = await message_service_db.get_recent_messages(session_id, limit)
    return messages


@router.post("/tldr", response_model=TLDRResponse)
async def generate_tldr(tldr_request: TLDRRequest, request: Request):
    """Generate TLDR summary of recent conversation."""
    # Get recent messages from database
    messages = await message_service_db.get_recent_messages(
        tldr_request.session_id,
        tldr_request.last_n_messages
    )
    
    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")
    
    # Generate TLDR with format specification
    try:
        summary = await llm_service.generate_tldr(messages, format=tldr_request.format)
        
        time_range = f"{messages[0].timestamp.strftime('%H:%M')} - {messages[-1].timestamp.strftime('%H:%M')}"
        
        return TLDRResponse(
            summary=summary,
            message_count=len(messages),
            time_range=time_range
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate TLDR: {str(e)}")


@router.get("/queue/stats/{session_id}")
async def get_queue_stats(session_id: str, request: Request):
    """Get queue statistics for a session."""
    queue_manager = request.app.state.queue_manager
    stats = await queue_manager.get_queue_stats(session_id)
    return stats


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat updates."""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Create and process message
            message = Message(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                content=message_data.get("content"),
                role=MessageRole(message_data.get("role", "user")),
                persona_id=message_data.get("persona_id")
            )
            
            # Send confirmation
            await websocket.send_json({
                "type": "message_received",
                "message": message.model_dump(mode='json')
            })
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })

