"""Service for managing groups."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import uuid

from database.models import Group as DBGroup, Persona as DBPersona
from models.group import GroupCreate, GroupUpdate, Group


class GroupService:
    """Service for group management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_group(self, group_data: GroupCreate) -> Group:
        """Create a new group."""
        group_id = f"group_{uuid.uuid4().hex[:8]}"
        
        db_group = DBGroup(
            id=group_id,
            name=group_data.name,
            description=group_data.description
        )
        
        # Add personas to group
        if group_data.persona_ids:
            result = await self.db.execute(
                select(DBPersona).where(DBPersona.id.in_(group_data.persona_ids))
            )
            personas = result.scalars().all()
            db_group.personas.extend(personas)
        
        self.db.add(db_group)
        await self.db.commit()
        
        # Reload with personas relationship eagerly loaded
        result = await self.db.execute(
            select(DBGroup)
            .options(selectinload(DBGroup.personas))
            .where(DBGroup.id == db_group.id)
        )
        db_group = result.scalar_one()
        
        return await self._to_pydantic(db_group)
    
    async def get_group(self, group_id: str) -> Optional[Group]:
        """Get group by ID."""
        result = await self.db.execute(
            select(DBGroup)
            .options(selectinload(DBGroup.personas))
            .where(DBGroup.id == group_id)
        )
        db_group = result.scalar_one_or_none()
        
        if db_group:
            return await self._to_pydantic(db_group)
        return None
    
    async def list_groups(self, active_only: bool = True) -> List[Group]:
        """List all groups."""
        query = select(DBGroup).options(selectinload(DBGroup.personas))
        
        if active_only:
            query = query.where(DBGroup.is_active == True)
        
        result = await self.db.execute(query)
        db_groups = result.scalars().all()
        
        return [await self._to_pydantic(g) for g in db_groups]
    
    async def update_group(self, group_id: str, group_data: GroupUpdate) -> Optional[Group]:
        """Update a group."""
        result = await self.db.execute(
            select(DBGroup).where(DBGroup.id == group_id)
        )
        db_group = result.scalar_one_or_none()
        
        if not db_group:
            return None
        
        update_data = group_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_group, field, value)
        
        await self.db.commit()
        
        # Reload with personas relationship eagerly loaded
        result = await self.db.execute(
            select(DBGroup)
            .options(selectinload(DBGroup.personas))
            .where(DBGroup.id == db_group.id)
        )
        db_group = result.scalar_one()
        
        return await self._to_pydantic(db_group)
    
    async def delete_group(self, group_id: str) -> bool:
        """Delete a group."""
        result = await self.db.execute(
            select(DBGroup).where(DBGroup.id == group_id)
        )
        db_group = result.scalar_one_or_none()
        
        if db_group:
            await self.db.delete(db_group)
            await self.db.commit()
            return True
        return False
    
    async def add_persona_to_group(self, group_id: str, persona_id: str) -> bool:
        """Add a persona to a group."""
        result = await self.db.execute(
            select(DBGroup)
            .options(selectinload(DBGroup.personas))
            .where(DBGroup.id == group_id)
        )
        db_group = result.scalar_one_or_none()
        
        if not db_group:
            return False
        
        persona_result = await self.db.execute(
            select(DBPersona).where(DBPersona.id == persona_id)
        )
        db_persona = persona_result.scalar_one_or_none()
        
        if not db_persona:
            return False
        
        if db_persona not in db_group.personas:
            db_group.personas.append(db_persona)
            await self.db.commit()
        
        return True
    
    async def remove_persona_from_group(self, group_id: str, persona_id: str) -> bool:
        """Remove a persona from a group."""
        result = await self.db.execute(
            select(DBGroup)
            .options(selectinload(DBGroup.personas))
            .where(DBGroup.id == group_id)
        )
        db_group = result.scalar_one_or_none()
        
        if not db_group:
            return False
        
        db_group.personas = [p for p in db_group.personas if p.id != persona_id]
        await self.db.commit()
        
        return True
    
    async def _to_pydantic(self, db_group: DBGroup) -> Group:
        """Convert database model to Pydantic model.
        
        Note: Expects db_group to have personas relationship already loaded.
        """
        # Access personas directly - should already be loaded by selectinload
        persona_ids = [p.id for p in (db_group.personas or [])]
        
        return Group(
            id=db_group.id,
            name=db_group.name,
            description=db_group.description,
            persona_ids=persona_ids,
            created_at=db_group.created_at,
            updated_at=db_group.updated_at,
            is_active=db_group.is_active
        )

