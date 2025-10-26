"""Message queue management system."""
import asyncio
from typing import Dict, Optional, List
from collections import deque
from datetime import datetime

from models.message import Message, MessageStatus


class MessageQueue:
    """Queue for managing messages in a session."""
    
    def __init__(self, max_size: int = 1000):
        self.queue: deque = deque(maxlen=max_size)
        self.processing: Dict[str, Message] = {}
        self.completed: List[Message] = []
        self._lock = asyncio.Lock()
        
    async def enqueue(self, message: Message):
        """Add message to queue."""
        async with self._lock:
            self.queue.append(message)
            
    async def dequeue(self) -> Optional[Message]:
        """Get next message from queue."""
        async with self._lock:
            if self.queue:
                message = self.queue.popleft()
                message.status = MessageStatus.PROCESSING
                self.processing[message.id] = message
                return message
            return None
            
    async def mark_completed(self, message_id: str):
        """Mark message as completed."""
        async with self._lock:
            if message_id in self.processing:
                message = self.processing.pop(message_id)
                message.status = MessageStatus.COMPLETED
                self.completed.append(message)
                
    async def add_completed_message(self, message: Message):
        """Add a message directly to completed (for instant messages)."""
        async with self._lock:
            message.status = MessageStatus.COMPLETED
            self.completed.append(message)
                
    async def mark_failed(self, message_id: str):
        """Mark message as failed."""
        async with self._lock:
            if message_id in self.processing:
                message = self.processing.pop(message_id)
                message.status = MessageStatus.FAILED
                
    async def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent completed messages."""
        async with self._lock:
            messages = self.completed[-limit:] if limit > 0 else self.completed
            return messages
            
    async def get_queue_size(self) -> int:
        """Get current queue size."""
        async with self._lock:
            return len(self.queue)
            
    async def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self.queue) == 0 and len(self.processing) == 0


class MessageQueueManager:
    """Manages multiple message queues for different sessions."""
    
    def __init__(self, max_queue_size: int = 1000):
        self.queues: Dict[str, MessageQueue] = {}
        self.max_queue_size = max_queue_size
        self._lock = asyncio.Lock()
        self._processors: Dict[str, asyncio.Task] = {}
        
    async def get_queue(self, session_id: str) -> MessageQueue:
        """Get or create queue for session."""
        async with self._lock:
            if session_id not in self.queues:
                self.queues[session_id] = MessageQueue(self.max_queue_size)
            return self.queues[session_id]
            
    async def enqueue_message(self, session_id: str, message: Message):
        """Add message to session queue."""
        queue = await self.get_queue(session_id)
        await queue.enqueue(message)
        
    async def dequeue_message(self, session_id: str) -> Optional[Message]:
        """Get next message from session queue."""
        queue = await self.get_queue(session_id)
        return await queue.dequeue()
        
    async def mark_completed(self, session_id: str, message_id: str):
        """Mark message as completed."""
        queue = await self.get_queue(session_id)
        await queue.mark_completed(message_id)
        
    async def add_completed_message(self, session_id: str, message: Message):
        """Add a message directly to completed."""
        queue = await self.get_queue(session_id)
        await queue.add_completed_message(message)
        
    async def mark_failed(self, session_id: str, message_id: str):
        """Mark message as failed."""
        queue = await self.get_queue(session_id)
        await queue.mark_failed(message_id)
        
    async def get_recent_messages(self, session_id: str, limit: int = 10) -> List[Message]:
        """Get recent messages from session."""
        queue = await self.get_queue(session_id)
        return await queue.get_recent_messages(limit)
        
    async def get_queue_stats(self, session_id: str) -> Dict:
        """Get queue statistics."""
        queue = await self.get_queue(session_id)
        return {
            "queue_size": await queue.get_queue_size(),
            "processing_count": len(queue.processing),
            "completed_count": len(queue.completed)
        }
        
    async def shutdown(self):
        """Shutdown all processors and cleanup."""
        for task in self._processors.values():
            task.cancel()
        await asyncio.gather(*self._processors.values(), return_exceptions=True)
        self._processors.clear()

