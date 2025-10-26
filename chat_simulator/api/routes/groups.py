"""API routes for group management."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from models.group import Group, GroupCreate, GroupUpdate
from services.group_service import GroupService
from database.connection import get_db


router = APIRouter()


@router.post("/", response_model=Group, status_code=201)
async def create_group(group_data: GroupCreate, db: AsyncSession = Depends(get_db)):
    """Create a new chat group."""
    service = GroupService(db)
    group = await service.create_group(group_data)
    return group


@router.get("/", response_model=List[Group])
async def list_groups(active_only: bool = True, db: AsyncSession = Depends(get_db)):
    """List all groups."""
    service = GroupService(db)
    groups = await service.list_groups(active_only)
    return groups


@router.get("/{group_id}", response_model=Group)
async def get_group(group_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific group."""
    service = GroupService(db)
    group = await service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.put("/{group_id}", response_model=Group)
async def update_group(
    group_id: str,
    group_data: GroupUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a group."""
    service = GroupService(db)
    group = await service.update_group(group_id, group_data)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.delete("/{group_id}")
async def delete_group(group_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a group."""
    service = GroupService(db)
    success = await service.delete_group(group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group deleted successfully"}


@router.post("/{group_id}/personas/{persona_id}")
async def add_persona_to_group(
    group_id: str,
    persona_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Add a persona to a group."""
    service = GroupService(db)
    success = await service.add_persona_to_group(group_id, persona_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group or persona not found")
    return {"message": "Persona added to group"}


@router.delete("/{group_id}/personas/{persona_id}")
async def remove_persona_from_group(
    group_id: str,
    persona_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a persona from a group."""
    service = GroupService(db)
    success = await service.remove_persona_from_group(group_id, persona_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Persona removed from group"}

