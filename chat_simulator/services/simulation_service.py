"""Service for managing simulations."""
from typing import Dict, Optional, List
import uuid
import asyncio
import random
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sql_update

from models.simulation import (
    Simulation as SimulationModel, SimulationCreate, SimulationUpdate,
    SimulationStatus, SimulationType
)
from models.message import Message, MessageRole, MessageStatus, MessageCreate
from database.models import Simulation as DBSimulation
from database.connection import async_session_maker
from core.queue_manager import MessageQueueManager
from services.persona_service_db import persona_service_db as persona_service
from services.llm_service import llm_service
from services.message_service_db import message_service_db


class SimulationService:
    """Service for simulation management."""
    
    def __init__(self, queue_manager: MessageQueueManager):
        self.queue_manager = queue_manager
        self._simulation_tasks: Dict[str, asyncio.Task] = {}
        
    async def create_simulation(self, simulation_data: SimulationCreate) -> SimulationModel:
        """Create a new simulation and save to database."""
        # Validate personas exist
        for persona_id in simulation_data.persona_ids:
            if not await persona_service.get_persona(persona_id):
                raise ValueError(f"Persona {persona_id} not found")
                
        simulation_id = f"sim_{uuid.uuid4().hex[:8]}"
        
        # Create database simulation
        async with async_session_maker() as db:
            db_simulation = DBSimulation(
                id=simulation_id,
                name=simulation_data.name,
                description=simulation_data.description,
                persona_ids=json.dumps(simulation_data.persona_ids),  # Store as JSON
                status='created',
                simulation_type=simulation_data.config.simulation_type.value,
                max_turns=simulation_data.config.max_turns,
                turn_delay=simulation_data.config.turn_delay,
                allow_user_interruption=simulation_data.config.allow_user_interruption,
                message_count=0,
                created_at=datetime.utcnow()
            )
            db.add(db_simulation)
            await db.commit()
            await db.refresh(db_simulation)
            
            # Convert to pydantic model
            return self._db_to_model(db_simulation)
        
    async def get_simulation(self, simulation_id: str) -> Optional[SimulationModel]:
        """Get simulation by ID from database."""
        async with async_session_maker() as db:
            result = await db.execute(
                select(DBSimulation).where(DBSimulation.id == simulation_id)
            )
            db_simulation = result.scalar_one_or_none()
            
            if not db_simulation:
                return None
                
            return self._db_to_model(db_simulation)
        
    async def list_simulations(self) -> List[SimulationModel]:
        """List all simulations from database."""
        async with async_session_maker() as db:
            result = await db.execute(select(DBSimulation))
            db_simulations = result.scalars().all()
            
            return [self._db_to_model(sim) for sim in db_simulations]
        
    async def update_simulation(
        self,
        simulation_id: str,
        simulation_data: SimulationUpdate
    ) -> Optional[SimulationModel]:
        """Update a simulation in database."""
        async with async_session_maker() as db:
            result = await db.execute(
                select(DBSimulation).where(DBSimulation.id == simulation_id)
            )
            db_simulation = result.scalar_one_or_none()
            
            if not db_simulation:
                return None
                
            update_data = simulation_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(db_simulation, field):
                    setattr(db_simulation, field, value)
                    
            await db.commit()
            await db.refresh(db_simulation)
            
            return self._db_to_model(db_simulation)
        
    async def delete_simulation(self, simulation_id: str) -> bool:
        """Delete a simulation from database."""
        # Cancel running task if exists
        if simulation_id in self._simulation_tasks:
            self._simulation_tasks[simulation_id].cancel()
            del self._simulation_tasks[simulation_id]
            
        async with async_session_maker() as db:
            result = await db.execute(
                select(DBSimulation).where(DBSimulation.id == simulation_id)
            )
            db_simulation = result.scalar_one_or_none()
            
            if not db_simulation:
                return False
                
            await db.delete(db_simulation)
            await db.commit()
            return True
    
    def _db_to_model(self, db_sim: DBSimulation) -> SimulationModel:
        """Convert database simulation to pydantic model."""
        from models.simulation import SimulationConfig
        
        # Parse persona_ids from JSON
        persona_ids = []
        if db_sim.persona_ids:
            try:
                persona_ids = json.loads(db_sim.persona_ids)
            except json.JSONDecodeError:
                persona_ids = []
        
        # Create config from database fields
        config = SimulationConfig(
            simulation_type=SimulationType(db_sim.simulation_type) if db_sim.simulation_type else SimulationType.CHAT,
            max_turns=db_sim.max_turns or 20,
            turn_delay=db_sim.turn_delay or 1.0,
            allow_user_interruption=db_sim.allow_user_interruption if db_sim.allow_user_interruption is not None else True
        )
        
        return SimulationModel(
            id=db_sim.id,
            name=db_sim.name,
            description=db_sim.description or "",
            persona_ids=persona_ids,
            config=config,
            status=SimulationStatus(db_sim.status) if db_sim.status else SimulationStatus.CREATED,
            message_count=db_sim.message_count or 0,
            created_at=db_sim.created_at,
            started_at=db_sim.started_at,
            completed_at=db_sim.completed_at
        )
        
    async def start_simulation(self, simulation_id: str) -> bool:
        """Start a simulation."""
        async with async_session_maker() as db:
            result = await db.execute(
                select(DBSimulation).where(DBSimulation.id == simulation_id)
            )
            db_simulation = result.scalar_one_or_none()
            
            if not db_simulation:
                return False
                
            if db_simulation.status == 'running':
                return False
                
            db_simulation.status = 'running'
            db_simulation.started_at = datetime.utcnow()
            await db.commit()
        
        # Start simulation task
        task = asyncio.create_task(self._run_simulation(simulation_id))
        self._simulation_tasks[simulation_id] = task
        return True
        
    async def pause_simulation(self, simulation_id: str) -> bool:
        """Pause a simulation."""
        async with async_session_maker() as db:
            result = await db.execute(
                select(DBSimulation).where(DBSimulation.id == simulation_id)
            )
            db_simulation = result.scalar_one_or_none()
            
            if not db_simulation:
                return False
                
            if db_simulation.status == 'running':
                db_simulation.status = 'paused'
                await db.commit()
                return True
            return False
        
    async def stop_simulation(self, simulation_id: str) -> bool:
        """Stop a simulation."""
        async with async_session_maker() as db:
            result = await db.execute(
                select(DBSimulation).where(DBSimulation.id == simulation_id)
            )
            db_simulation = result.scalar_one_or_none()
            
            if not db_simulation:
                return False
                
            db_simulation.status = 'completed'
            db_simulation.completed_at = datetime.utcnow()
            await db.commit()
        
        # Cancel task if running
        if simulation_id in self._simulation_tasks:
            self._simulation_tasks[simulation_id].cancel()
            del self._simulation_tasks[simulation_id]
            
        return True
        
    async def _run_simulation(self, simulation_id: str):
        """Run simulation loop."""
        simulation = await self.get_simulation(simulation_id)
        if not simulation:
            return
        
        # If only one persona, generate just one message then pause
        single_persona_mode = len(simulation.persona_ids) == 1
        
        # Use configured max turns or default to 20 for multi-persona conversations
        if simulation.config.max_turns:
            actual_max_turns = simulation.config.max_turns
        else:
            # Default: 20 turns for multi-persona, 1 for single persona
            actual_max_turns = 20 if len(simulation.persona_ids) > 1 else 1
        
        turn = 0
        max_turns = actual_max_turns
        
        try:
            while turn < max_turns:
                # Check simulation status from database
                async with async_session_maker() as db:
                    result = await db.execute(
                        select(DBSimulation).where(DBSimulation.id == simulation_id)
                    )
                    db_sim = result.scalar_one_or_none()
                    if not db_sim or db_sim.status != 'running':
                        break
                # Get next persona in round-robin fashion
                persona_index = turn % len(simulation.persona_ids)
                persona_id = simulation.persona_ids[persona_index]
                persona = await persona_service.get_persona(persona_id)
                
                if not persona or not persona.is_active:
                    turn += 1
                    continue
                    
                # Get conversation history from database
                history = await message_service_db.get_recent_messages(
                    simulation_id,
                    limit=20
                )
                
                # Generate response
                try:
                    response_content = await llm_service.generate_response(
                        persona,
                        history
                    )
                    
                    # Create message in database (source of truth)
                    message_id = f"msg_{uuid.uuid4().hex[:8]}"
                    message_data = MessageCreate(
                        content=response_content,
                        role=MessageRole.PERSONA,
                        persona_id=persona_id
                    )
                    
                    message = await message_service_db.create_message(
                        message_data=message_data,
                        session_id=simulation_id,
                        message_id=message_id
                    )
                    
                    # Also add to queue for real-time updates
                    await self.queue_manager.add_completed_message(simulation_id, message)
                    
                    # Update message count in database
                    async with async_session_maker() as db:
                        result = await db.execute(
                            select(DBSimulation).where(DBSimulation.id == simulation_id)
                        )
                        db_sim = result.scalar_one_or_none()
                        if db_sim:
                            db_sim.message_count = (db_sim.message_count or 0) + 1
                            await db.commit()
                    
                    simulation.message_count += 1
                    
                    # Add to persona's short-term memory
                    await persona_service.add_memory(
                        persona_id,
                        f"I said: {response_content}",
                        "short_term"
                    )
                    
                except Exception as e:
                    print(f"Error generating response for {persona_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    
                turn += 1
                
                # If single persona mode, pause after each message (wait for user input)
                if single_persona_mode:
                    simulation.status = SimulationStatus.PAUSED
                    # Update status in database
                    async with async_session_maker() as db:
                        result = await db.execute(
                            select(DBSimulation).where(DBSimulation.id == simulation_id)
                        )
                        db_sim = result.scalar_one_or_none()
                        if db_sim:
                            db_sim.status = 'paused'
                            await db.commit()
                    break
                
                # Wait for turn delay (skip delay for first turn to get immediate response)
                if turn > 1 or simulation.config.turn_delay > 0.5:
                    await asyncio.sleep(simulation.config.turn_delay)
                
        except asyncio.CancelledError:
            pass
        finally:
            if simulation.status == SimulationStatus.RUNNING:
                simulation.status = SimulationStatus.COMPLETED
                simulation.completed_at = datetime.utcnow()
                # Update status in database
                async with async_session_maker() as db:
                    result = await db.execute(
                        select(DBSimulation).where(DBSimulation.id == simulation_id)
                    )
                    db_sim = result.scalar_one_or_none()
                    if db_sim:
                        db_sim.status = 'completed'
                        db_sim.completed_at = datetime.utcnow()
                        await db.commit()

