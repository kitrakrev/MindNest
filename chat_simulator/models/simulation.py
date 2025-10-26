"""Simulation data models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SimulationType(str, Enum):
    """Type of simulation."""
    CHAT = "chat"
    VIEWS = "views"


class SimulationStatus(str, Enum):
    """Simulation status."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class SimulationConfig(BaseModel):
    """Configuration for a simulation."""
    simulation_type: SimulationType = SimulationType.CHAT
    max_turns: Optional[int] = Field(None, ge=1, le=1000)
    turn_delay: float = Field(1.0, ge=0.0, le=10.0)
    allow_user_interruption: bool = True
    auto_generate: bool = False


class SimulationCreate(BaseModel):
    """Simulation creation model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    persona_ids: List[str] = Field(..., min_items=1)
    config: SimulationConfig = Field(default_factory=SimulationConfig)


class SimulationUpdate(BaseModel):
    """Simulation update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[SimulationStatus] = None
    config: Optional[SimulationConfig] = None


class Simulation(BaseModel):
    """Full simulation model."""
    id: str
    name: str
    description: Optional[str] = None
    persona_ids: List[str]
    config: SimulationConfig
    status: SimulationStatus = SimulationStatus.CREATED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    message_count: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "sim_123",
                "name": "Tech Discussion",
                "description": "A discussion about AI and robotics",
                "persona_ids": ["persona_1", "persona_2", "persona_3"],
                "status": "running",
                "message_count": 42
            }
        }


class TLDRRequest(BaseModel):
    """Request for TLDR summary."""
    session_id: str
    last_n_messages: int = Field(10, ge=1, le=100)
    format: str = Field('text', pattern='^(text|video)$')  # 'text' or 'video'


class TLDRResponse(BaseModel):
    """TLDR summary response."""
    summary: str
    message_count: int
    time_range: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

