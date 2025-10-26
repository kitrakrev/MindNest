"""Group data models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class GroupBase(BaseModel):
    """Base group model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class GroupCreate(GroupBase):
    """Group creation model."""
    persona_ids: List[str] = Field(default_factory=list)


class GroupUpdate(BaseModel):
    """Group update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Group(GroupBase):
    """Full group model."""
    id: str
    persona_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "group_123",
                "name": "Tech Discussion Group",
                "description": "A group for discussing technology",
                "persona_ids": ["persona_1", "persona_2"],
                "is_active": True
            }
        }

