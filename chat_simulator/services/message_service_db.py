"""Message service for database operations."""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import async_session_maker
from database.models import Message as DBMessage
from models.message import Message, MessageCreate, MessageRole, MessageStatus

logger = logging.getLogger(__name__)


class MessageServiceDB:
    """Service for managing messages in the database."""
    
    async def create_message(self, message_data: MessageCreate, session_id: str, message_id: str) -> Message:
        """
        Create a new message and save to database.
        
        Args:
            message_data: Message creation data
            session_id: Simulation/session ID
            message_id: Unique message ID
            
        Returns:
            Created Message model
        """
        async with async_session_maker() as db:
            db_message = DBMessage(
                id=message_id,
                simulation_id=session_id,
                persona_id=message_data.persona_id,
                content=message_data.content,
                role=message_data.role.value,
                status='completed',
                timestamp=datetime.utcnow(),
                response_to=None  # Optional field, not in MessageCreate
            )
            
            db.add(db_message)
            await db.commit()
            await db.refresh(db_message)
            
            return self._db_to_model(db_message)
    
    async def get_message(self, message_id: str) -> Optional[Message]:
        """Get a message by ID."""
        async with async_session_maker() as db:
            result = await db.execute(
                select(DBMessage).where(DBMessage.id == message_id)
            )
            db_message = result.scalar_one_or_none()
            
            if not db_message:
                return None
            
            return self._db_to_model(db_message)
    
    async def get_messages_by_simulation(
        self, 
        simulation_id: str, 
        limit: int = 100,
        skip: int = 0
    ) -> List[Message]:
        """
        Get messages for a simulation/session.
        
        Args:
            simulation_id: The simulation ID
            limit: Maximum number of messages to return
            skip: Number of messages to skip (for pagination)
            
        Returns:
            List of Message models, ordered by timestamp
        """
        async with async_session_maker() as db:
            result = await db.execute(
                select(DBMessage)
                .where(DBMessage.simulation_id == simulation_id)
                .order_by(DBMessage.timestamp)
                .offset(skip)
                .limit(limit)
            )
            db_messages = result.scalars().all()
            
            return [self._db_to_model(msg) for msg in db_messages]
    
    async def get_recent_messages(
        self, 
        simulation_id: str, 
        limit: int = 50
    ) -> List[Message]:
        """
        Get the most recent messages for a simulation.
        
        Args:
            simulation_id: The simulation ID
            limit: Maximum number of recent messages
            
        Returns:
            List of Message models, ordered by timestamp (oldest to newest)
        """
        async with async_session_maker() as db:
            result = await db.execute(
                select(DBMessage)
                .where(DBMessage.simulation_id == simulation_id)
                .order_by(desc(DBMessage.timestamp))
                .limit(limit)
            )
            db_messages = result.scalars().all()
            
            # Reverse to get chronological order (oldest to newest)
            return [self._db_to_model(msg) for msg in reversed(list(db_messages))]
    
    async def count_messages(self, simulation_id: str) -> int:
        """Count total messages in a simulation."""
        async with async_session_maker() as db:
            from sqlalchemy import func
            result = await db.execute(
                select(func.count(DBMessage.id))
                .where(DBMessage.simulation_id == simulation_id)
            )
            return result.scalar() or 0
    
    async def delete_messages_by_simulation(self, simulation_id: str) -> int:
        """Delete all messages for a simulation. Returns count of deleted messages."""
        async with async_session_maker() as db:
            result = await db.execute(
                select(DBMessage).where(DBMessage.simulation_id == simulation_id)
            )
            messages = result.scalars().all()
            count = len(messages)
            
            for msg in messages:
                await db.delete(msg)
            
            await db.commit()
            return count
    
    async def delete_all_messages(self) -> int:
        """Delete all messages. Returns count of deleted messages."""
        async with async_session_maker() as db:
            result = await db.execute(select(DBMessage))
            messages = result.scalars().all()
            count = len(messages)
            
            for msg in messages:
                await db.delete(msg)
            
            await db.commit()
            return count
    
    def _db_to_model(self, db_message: DBMessage) -> Message:
        """Convert database message to pydantic model."""
        return Message(
            id=db_message.id,
            session_id=db_message.simulation_id,
            persona_id=db_message.persona_id,
            content=db_message.content,
            role=MessageRole(db_message.role),
            status=MessageStatus(db_message.status),
            timestamp=db_message.timestamp,
            response_to=db_message.response_to
        )


# Singleton instance
message_service_db = MessageServiceDB()

