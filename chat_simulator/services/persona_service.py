"""Service for managing personas."""
from typing import Dict, List, Optional
import uuid
from datetime import datetime

from models.persona import Persona, PersonaCreate, PersonaUpdate, PersonaMemory
from core.config import settings


class PersonaService:
    """Service for persona management."""
    
    def __init__(self):
        self.personas: Dict[str, Persona] = {}
    
    def persona_name_exists(self, name: str) -> bool:
        """Check if a persona with the given name already exists (case-insensitive)."""
        return any(p.name.lower() == name.lower() for p in self.personas.values())
    
    def get_persona_by_name(self, name: str) -> Optional[Persona]:
        """Get persona by name (case-insensitive)."""
        for persona in self.personas.values():
            if persona.name.lower() == name.lower():
                return persona
        return None
        
    def create_persona(self, persona_data: PersonaCreate, skip_if_exists: bool = False) -> Persona:
        """Create a new persona.
        
        Args:
            persona_data: The persona data to create
            skip_if_exists: If True, return existing persona instead of raising error
            
        Raises:
            ValueError: If persona name already exists (and skip_if_exists is False)
        """
        if len(self.personas) >= settings.MAX_PERSONAS:
            raise ValueError(f"Maximum number of personas ({settings.MAX_PERSONAS}) reached")
        
        # Check for duplicate names
        if self.persona_name_exists(persona_data.name):
            if skip_if_exists:
                return self.get_persona_by_name(persona_data.name)
            else:
                raise ValueError(f"Persona with name '{persona_data.name}' already exists")
            
        persona_id = f"persona_{uuid.uuid4().hex[:8]}"
        persona = Persona(
            id=persona_id,
            **persona_data.model_dump(),
            memory=PersonaMemory()
        )
        self.personas[persona_id] = persona
        return persona
        
    def get_persona(self, persona_id: str) -> Optional[Persona]:
        """Get persona by ID."""
        return self.personas.get(persona_id)
        
    def list_personas(self, active_only: bool = True) -> List[Persona]:
        """List all personas."""
        personas = list(self.personas.values())
        if active_only:
            personas = [p for p in personas if p.is_active]
        return personas
        
    def update_persona(
        self,
        persona_id: str,
        persona_data: PersonaUpdate
    ) -> Optional[Persona]:
        """Update a persona."""
        persona = self.personas.get(persona_id)
        if not persona:
            return None
            
        update_data = persona_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(persona, field, value)
            
        persona.updated_at = datetime.utcnow()
        return persona
        
    def delete_persona(self, persona_id: str) -> bool:
        """Delete a persona."""
        if persona_id in self.personas:
            del self.personas[persona_id]
            return True
        return False
        
    def deactivate_persona(self, persona_id: str) -> bool:
        """Deactivate a persona."""
        persona = self.personas.get(persona_id)
        if persona:
            persona.is_active = False
            return True
        return False
        
    def add_memory(
        self,
        persona_id: str,
        content: str,
        memory_type: str = "short_term",
        importance: float = 0.5
    ) -> bool:
        """Add memory to persona."""
        persona = self.personas.get(persona_id)
        if not persona:
            return False
            
        if memory_type == "short_term":
            persona.memory.add_short_term(content, importance)
        else:
            persona.memory.add_long_term(content, importance)
            
        # Consolidate memories if needed
        persona.memory.consolidate(settings.SHORT_TERM_MEMORY_SIZE)
        return True
        
    def import_personas(self, personas_data: List[PersonaCreate]) -> List[Persona]:
        """Import multiple personas."""
        imported = []
        for persona_data in personas_data:
            try:
                persona = self.create_persona(persona_data)
                imported.append(persona)
            except ValueError:
                # Skip if max personas reached
                break
        return imported


# Singleton instance
persona_service = PersonaService()

