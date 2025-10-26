"""Admin API routes for system management."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, delete
from database.connection import async_session_maker
from database.models import Persona, Memory, Group, Simulation, Message
from services.persona_service_db import persona_service_db

router = APIRouter()


@router.post("/clear-all")
async def clear_all_data():
    """
    Clear ALL data from the system.
    This will delete:
    - All personas and memories
    - All groups
    - All simulations
    - All messages
    
    WARNING: This action cannot be undone!
    """
    try:
        counts = {
            "personas": 0,
            "memories": 0,
            "groups": 0,
            "simulations": 0,
            "messages": 0
        }
        
        async with async_session_maker() as session:
            # Delete in correct order to respect foreign keys
            
            # 1. Messages (depends on simulations, groups, personas)
            msg_stmt = select(Message)
            msg_result = await session.execute(msg_stmt)
            messages = msg_result.scalars().all()
            counts["messages"] = len(messages)
            for msg in messages:
                await session.delete(msg)
            
            # 2. Simulations (depends on groups)
            sim_stmt = select(Simulation)
            sim_result = await session.execute(sim_stmt)
            simulations = sim_result.scalars().all()
            counts["simulations"] = len(simulations)
            for sim in simulations:
                await session.delete(sim)
            
            # 3. Memories (depends on personas)
            mem_stmt = select(Memory)
            mem_result = await session.execute(mem_stmt)
            memories = mem_result.scalars().all()
            counts["memories"] = len(memories)
            for mem in memories:
                await session.delete(mem)
            
            # 4. Groups (has many-to-many with personas, but we'll clear that)
            group_stmt = select(Group)
            group_result = await session.execute(group_stmt)
            groups = group_result.scalars().all()
            counts["groups"] = len(groups)
            for group in groups:
                await session.delete(group)
            
            # 5. Personas (no dependencies left)
            persona_stmt = select(Persona)
            persona_result = await session.execute(persona_stmt)
            personas = persona_result.scalars().all()
            counts["personas"] = len(personas)
            for persona in personas:
                await session.delete(persona)
            
            await session.commit()
        
        return {
            "message": "All data cleared successfully",
            "deleted": counts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")


@router.post("/clear-messages")
async def clear_messages_only():
    """Clear only messages and simulations, keeping personas and groups."""
    try:
        counts = {"messages": 0, "simulations": 0}
        
        async with async_session_maker() as session:
            # Delete messages
            msg_stmt = select(Message)
            msg_result = await session.execute(msg_stmt)
            messages = msg_result.scalars().all()
            counts["messages"] = len(messages)
            for msg in messages:
                await session.delete(msg)
            
            # Delete simulations
            sim_stmt = select(Simulation)
            sim_result = await session.execute(sim_stmt)
            simulations = sim_result.scalars().all()
            counts["simulations"] = len(simulations)
            for sim in simulations:
                await session.delete(sim)
            
            await session.commit()
        
        return {
            "message": "Messages and simulations cleared successfully",
            "deleted": counts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear messages: {str(e)}")


@router.get("/stats")
async def get_system_stats():
    """Get system statistics."""
    try:
        stats = {}
        
        async with async_session_maker() as session:
            # Count personas
            persona_stmt = select(Persona)
            persona_result = await session.execute(persona_stmt)
            stats["personas"] = len(persona_result.scalars().all())
            
            # Count groups
            group_stmt = select(Group)
            group_result = await session.execute(group_stmt)
            stats["groups"] = len(group_result.scalars().all())
            
            # Count simulations
            sim_stmt = select(Simulation)
            sim_result = await session.execute(sim_stmt)
            stats["simulations"] = len(sim_result.scalars().all())
            
            # Count messages
            msg_stmt = select(Message)
            msg_result = await session.execute(msg_stmt)
            stats["messages"] = len(msg_result.scalars().all())
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

