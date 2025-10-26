"""Persona data models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class PersonaType(str, Enum):
    """Type of persona."""
    USER = "user"
    REAL_PEOPLE = "real_people"


class Memory(BaseModel):
    """Memory entry."""
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    importance: float = Field(ge=0.0, le=1.0, default=0.5)


class PersonaMemory(BaseModel):
    """Persona memory structure."""
    short_term: List[Memory] = Field(default_factory=list)
    long_term: List[Memory] = Field(default_factory=list)
    
    def add_short_term(self, content: str, importance: float = 0.5):
        """Add memory to short-term storage."""
        memory = Memory(content=content, importance=importance)
        self.short_term.append(memory)
        
    def add_long_term(self, content: str, importance: float = 0.7):
        """Add memory to long-term storage."""
        memory = Memory(content=content, importance=importance)
        self.long_term.append(memory)
        
    def consolidate(self, short_term_limit: int = 10):
        """Move important short-term memories to long-term."""
        if len(self.short_term) > short_term_limit:
            # Move high importance memories to long-term
            important = [m for m in self.short_term if m.importance >= 0.7]
            self.long_term.extend(important)
            # Keep only recent short-term memories
            self.short_term = self.short_term[-short_term_limit:]


class PersonaBase(BaseModel):
    """Base persona model."""
    name: str = Field(..., min_length=1, max_length=100)
    persona_type: PersonaType = PersonaType.USER
    system_prompt: str = Field(..., min_length=10)
    description: Optional[str] = None


class PersonaCreate(PersonaBase):
    """Persona creation model."""
    pass


class PersonaUpdate(BaseModel):
    """Persona update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    persona_type: Optional[PersonaType] = None
    system_prompt: Optional[str] = Field(None, min_length=10)
    description: Optional[str] = None


class Persona(PersonaBase):
    """Full persona model."""
    id: str
    memory: PersonaMemory = Field(default_factory=PersonaMemory)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "persona_123",
                "name": "Tech Enthusiast",
                "persona_type": "user",
                "system_prompt": "You are a tech enthusiast who loves discussing new technologies and innovations.",
                "description": "A persona interested in AI, robotics, and future tech",
                "is_active": True
            }
        }

