"""Models for persona generation requests."""
from pydantic import BaseModel, Field
from typing import List, Optional

from models.persona import PersonaType


class ConversationUpload(BaseModel):
    """Request to generate personas from conversation."""
    conversation_text: str = Field(
        ...,
        min_length=10,
        description="Conversation transcript with speaker labels"
    )
    persona_type: PersonaType = PersonaType.USER
    auto_create: bool = Field(
        True,
        description="Automatically create personas after generation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_text": """Alice: Hey, how are you doing today?
Bob: I'm great! Just finished a coding project.
Alice: That sounds exciting! What was it about?
Bob: It's an AI chatbot using GPT. Really fun to build.""",
                "persona_type": "user",
                "auto_create": True
            }
        }


class PersonaGenerationRequest(BaseModel):
    """Request to generate a single persona."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    traits: List[str] = Field(
        default_factory=list,
        description="Key personality traits or characteristics"
    )
    persona_type: PersonaType = PersonaType.USER
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Dr. Science",
                "description": "A knowledgeable scientist who loves explaining complex topics simply",
                "traits": ["curious", "patient", "enthusiastic"],
                "persona_type": "user"
            }
        }


class PersonaGenerationResponse(BaseModel):
    """Response from persona generation."""
    personas_created: List[str] = Field(
        default_factory=list,
        description="IDs of created personas"
    )
    personas_preview: List[dict] = Field(
        default_factory=list,
        description="Preview of generated personas"
    )
    count: int
    message: str

