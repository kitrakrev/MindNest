"""Message data models."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role types."""
    USER = "user"
    PERSONA = "persona"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Message processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageBase(BaseModel):
    """Base message model."""
    content: str = Field(..., min_length=1)
    role: MessageRole
    persona_id: Optional[str] = None


class MessageCreate(MessageBase):
    """Message creation model."""
    pass


class Message(MessageBase):
    """Full message model."""
    id: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: MessageStatus = MessageStatus.PENDING
    response_to: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg_123",
                "session_id": "session_456",
                "content": "Hello, how are you?",
                "role": "user",
                "persona_id": "persona_123",
                "status": "completed"
            }
        }


class MessageResponse(BaseModel):
    """Response model for message endpoints."""
    message: Message
    success: bool
    error: Optional[str] = None

