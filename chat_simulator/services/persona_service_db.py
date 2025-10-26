"""Database-backed service for managing personas."""
from typing import List, Optional
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import async_session_maker
from database.models import Persona as PersonaDB, Memory as MemoryDB
from models.persona import Persona, PersonaCreate, PersonaUpdate, PersonaMemory, Memory
from core.config import settings


class PersonaServiceDB:
    """Database-backed service for persona management."""
    
    async def _db_to_model(self, db_persona: PersonaDB) -> Persona:
        """Convert database persona to Pydantic model."""
        # Load memories
        memory = PersonaMemory()
        async with async_session_maker() as session:
            stmt = select(MemoryDB).where(MemoryDB.persona_id == db_persona.id)
            result = await session.execute(stmt)
            memories = result.scalars().all()
            
            for mem in memories:
                mem_obj = Memory(
                    content=mem.content,
                    timestamp=mem.timestamp,
                    importance=mem.importance
                )
                if mem.memory_type == 'short_term':
                    memory.short_term.append(mem_obj)
                else:
                    memory.long_term.append(mem_obj)
        
        return Persona(
            id=db_persona.id,
            name=db_persona.name,
            persona_type=db_persona.persona_type,
            system_prompt=db_persona.system_prompt,
            description=db_persona.description,
            created_at=db_persona.created_at,
            updated_at=db_persona.updated_at,
            is_active=db_persona.is_active,
            memory=memory
        )
    
    async def persona_name_exists(self, name: str) -> bool:
        """Check if a persona with the given name already exists (case-insensitive)."""
        async with async_session_maker() as session:
            stmt = select(PersonaDB).where(PersonaDB.name.ilike(name))
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None
    
    async def get_persona_by_name(self, name: str) -> Optional[Persona]:
        """Get persona by name (case-insensitive)."""
        async with async_session_maker() as session:
            stmt = select(PersonaDB).where(PersonaDB.name.ilike(name))
            result = await session.execute(stmt)
            db_persona = result.scalar_one_or_none()
            
            if db_persona:
                return await self._db_to_model(db_persona)
            return None
    
    async def create_persona(self, persona_data: PersonaCreate, skip_if_exists: bool = False) -> Persona:
        """Create a new persona.
        
        Args:
            persona_data: The persona data to create
            skip_if_exists: If True, return existing persona instead of raising error
            
        Raises:
            ValueError: If persona name already exists (and skip_if_exists is False)
        """
        async with async_session_maker() as session:
            # Check persona count
            count_stmt = select(PersonaDB)
            count_result = await session.execute(count_stmt)
            if len(count_result.scalars().all()) >= settings.MAX_PERSONAS:
                raise ValueError(f"Maximum number of personas ({settings.MAX_PERSONAS}) reached")
            
            # Check for duplicate names
            if await self.persona_name_exists(persona_data.name):
                if skip_if_exists:
                    return await self.get_persona_by_name(persona_data.name)
                else:
                    raise ValueError(f"Persona with name '{persona_data.name}' already exists")
            
            # Create new persona
            persona_id = f"persona_{uuid.uuid4().hex[:8]}"
            db_persona = PersonaDB(
                id=persona_id,
                name=persona_data.name,
                persona_type=persona_data.persona_type,
                system_prompt=persona_data.system_prompt,
                description=persona_data.description,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            
            session.add(db_persona)
            await session.commit()
            await session.refresh(db_persona)
            
            return await self._db_to_model(db_persona)
    
    async def get_persona(self, persona_id: str) -> Optional[Persona]:
        """Get persona by ID."""
        async with async_session_maker() as session:
            stmt = select(PersonaDB).where(PersonaDB.id == persona_id)
            result = await session.execute(stmt)
            db_persona = result.scalar_one_or_none()
            
            if db_persona:
                return await self._db_to_model(db_persona)
            return None
    
    async def list_personas(self, active_only: bool = True) -> List[Persona]:
        """List all personas."""
        async with async_session_maker() as session:
            if active_only:
                stmt = select(PersonaDB).where(PersonaDB.is_active == True)
            else:
                stmt = select(PersonaDB)
            
            result = await session.execute(stmt)
            db_personas = result.scalars().all()
            
            personas = []
            for db_persona in db_personas:
                personas.append(await self._db_to_model(db_persona))
            
            return personas
    
    async def update_persona(self, persona_id: str, persona_data: PersonaUpdate) -> Optional[Persona]:
        """Update a persona."""
        async with async_session_maker() as session:
            stmt = select(PersonaDB).where(PersonaDB.id == persona_id)
            result = await session.execute(stmt)
            db_persona = result.scalar_one_or_none()
            
            if not db_persona:
                return None
            
            update_data = persona_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_persona, field, value)
            
            db_persona.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(db_persona)
            
            return await self._db_to_model(db_persona)
    
    async def delete_persona(self, persona_id: str) -> bool:
        """Delete a persona."""
        async with async_session_maker() as session:
            stmt = select(PersonaDB).where(PersonaDB.id == persona_id)
            result = await session.execute(stmt)
            db_persona = result.scalar_one_or_none()
            
            if not db_persona:
                return False
            
            await session.delete(db_persona)
            await session.commit()
            return True
    
    async def add_memory(self, persona_id: str, content: str, memory_type: str = "short_term", importance: float = 0.5):
        """Add a memory to a persona."""
        async with async_session_maker() as session:
            memory = MemoryDB(
                persona_id=persona_id,
                content=content,
                memory_type=memory_type,
                importance=importance,
                timestamp=datetime.utcnow()
            )
            session.add(memory)
            await session.commit()
    
    async def clear_all_personas(self) -> int:
        """Delete all personas and their memories. Returns count of deleted personas."""
        async with async_session_maker() as session:
            # Count before deleting
            count_stmt = select(PersonaDB)
            count_result = await session.execute(count_stmt)
            count = len(count_result.scalars().all())
            
            # Delete all memories first (cascade should handle this, but be explicit)
            mem_stmt = select(MemoryDB)
            mem_result = await session.execute(mem_stmt)
            for mem in mem_result.scalars().all():
                await session.delete(mem)
            
            # Delete all personas
            persona_stmt = select(PersonaDB)
            persona_result = await session.execute(persona_stmt)
            for persona in persona_result.scalars().all():
                await session.delete(persona)
            
            await session.commit()
            return count


# Global instance
persona_service_db = PersonaServiceDB()

