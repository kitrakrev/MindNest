"""
Global Agent Service Module

This module provides a meta-level AI advisor that analyzes conversations across
all sessions and provides strategic insights. The global agent maintains its own
memory (short-term and long-term) and learns from all interactions.

Features:
- Cross-session conversation analysis
- Memory consolidation (short-term and long-term)
- Pattern recognition across multiple conversations
- Strategic advice generation
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from models.message import Message
from models.persona import PersonaMemory
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


class GlobalAgentService:
    """
    Global Meta-Advisor Service
    
    Provides high-level analysis and strategic insights by analyzing all
    conversations and maintaining its own memory system.
    
    Attributes:
        conversation_history: List of all queries and responses
        memory: PersonaMemory instance for short-term and long-term storage
        session_summaries: Mapping of session IDs to their summaries
    """
    
    def __init__(self) -> None:
        """Initialize the global agent service."""
        self.conversation_history: List[Dict[str, Any]] = []
        self.memory = PersonaMemory()
        self.session_summaries: Dict[str, str] = {}
        self.persona_service = None  # Will be set when needed
        
    def _get_persona_name(self, persona_id: str) -> str:
        """Get actual persona name from ID."""
        if not self.persona_service:
            # Import here to avoid circular imports
            from services.persona_service import persona_service
            self.persona_service = persona_service
        
        persona = self.persona_service.get_persona(persona_id)
        if persona and persona.name:
            return persona.name
        return persona_id.replace("persona_", "Persona_")
    
    def _summarize_messages(self, messages: List[Message], max_messages: int = 50) -> str:
        """
        Summarize messages with actual speaker names for context.
        
        Args:
            messages: List of messages to summarize
            max_messages: Maximum number of recent messages to include
            
        Returns:
            Formatted string with "Speaker: message" format (e.g., "Alice: Hello!")
        """
        if not messages:
            return "No conversation history available."
            
        recent = messages[-max_messages:] if len(messages) > max_messages else messages
        
        summary_parts = []
        for msg in recent:
            # Format: "User: message" or "PersonaName: message" (actual name)
            if msg.role == "user":
                speaker = "User"
            elif msg.persona_id:
                # Look up actual persona name
                speaker = self._get_persona_name(msg.persona_id)
            else:
                speaker = "System"
            
            # Keep full message content for better context
            summary_parts.append(f"{speaker}: {msg.content}")
            
        return "\n".join(summary_parts)
        
    def _build_global_agent_prompt(self, context: str, user_question: str) -> List[Dict[str, str]]:
        """
        Build the prompt for the global agent including memory context.
        
        Args:
            context: Summarized conversation history
            user_question: The user's question or query
            
        Returns:
            List of message dictionaries for the LLM
        """
        system_prompt = (
            "You are a Global Meta-Advisor AI analyzing conversations.\n\n"
            "Conversation format: 'Speaker: message' (User, Persona_ID, or System)\n"
            "Track who said what. Analyze patterns, dynamics between speakers, themes.\n\n"
            "CRITICAL: Keep advice to 3-4 sentences max. Be direct and actionable."
        )

        # Add long-term memory context (reduced to 3)
        if self.memory.long_term:
            recent_lt = self.memory.long_term[-3:]
            memory_context = "\n".join(f"- {mem.content}" for mem in recent_lt)
            system_prompt += f"\n\nKey insights:\n{memory_context}"
            
        # Add short-term memory context (reduced to 2)
        if self.memory.short_term:
            recent_st = self.memory.short_term[-2:]
            memory_context = "\n".join(f"- {mem.content}" for mem in recent_st)
            system_prompt += f"\n\nRecent:\n{memory_context}"

        # Build detailed prompt with conversation history
        if context and context != "No conversation history available.":
            user_content = (
                f"Conversation History:\n"
                f"---\n"
                f"{context}\n"
                f"---\n\n"
                f"User Question: {user_question}\n\n"
                f"Analyze the conversation above and answer in 3-4 sentences."
            )
        else:
            user_content = (
                f"Question: {user_question}\n\n"
                f"(No conversation history available yet)\n\n"
                f"Answer in 3-4 sentences:"
            )
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
    async def get_advice(
        self,
        all_messages: List[Message],
        user_question: str,
        session_id: Optional[str] = None
    ) -> str:
        """
        Generate advice from the global agent based on conversation context.
        
        Args:
            all_messages: All messages from the session(s)
            user_question: The user's question
            session_id: Optional session ID for context
            
        Returns:
            Generated advice as a string
            
        Raises:
            Exception: If LLM generation fails
        """
        try:
            # Summarize conversation context
            context = self._summarize_messages(all_messages)
            
            # Build prompt with memory integration
            messages = self._build_global_agent_prompt(context, user_question)
            
            # Generate response with streaming
            stream = await llm_service.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                stream=True
            )
            
            # Collect streaming response
            content_parts = []
            async for chunk in stream:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content_parts.append(delta.content)
            
            advice = ''.join(content_parts).strip()
            
            if not advice:
                advice = "I'm unable to provide advice at this time."
            
            # Record in conversation history
            self.conversation_history.append({
                "question": user_question,
                "advice": advice,
                "context_size": len(all_messages),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update short-term memory with interaction summary
            question_preview = user_question[:100] + "..." if len(user_question) > 100 else user_question
            advice_preview = advice[:100] + "..." if len(advice) > 100 else advice
            self.memory.add_short_term(
                f"User asked: '{question_preview}' | Advised: '{advice_preview}'",
                importance=0.5
            )
            
            # Extract insights for substantial conversations
            if len(all_messages) > 10:
                await self._extract_insights(context, advice, session_id)
            
            # Consolidate memory to maintain manageable size
            self.memory.consolidate(short_term_limit=10)
            
            logger.info(f"Generated advice for session {session_id}, {len(all_messages)} messages analyzed")
            
            return advice
            
        except Exception as e:
            logger.error(f"Error generating advice: {str(e)}", exc_info=True)
            return f"I apologize, but I encountered an error while analyzing the conversation: {str(e)}"
    
    async def _extract_insights(
        self,
        context: str,
        advice: str,
        session_id: Optional[str]
    ) -> None:
        """
        Extract key insights from conversation and store in long-term memory.
        
        Args:
            context: Conversation context summary
            advice: The advice that was given
            session_id: Optional session identifier
        """
        try:
            # Truncate context for insight extraction
            truncated_context = context[:500] + "..." if len(context) > 500 else context
            
            insight_prompt = (
                f"Extract ONE key insight (max 50 chars):\n"
                f"Context: {truncated_context}\n"
                f"Advice: {advice}\n\n"
                f"Single insight only:"
            )

            stream = await llm_service.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": insight_prompt}],
                temperature=0.5,
                max_tokens=30,
                stream=True
            )
            
            # Collect streaming response
            content_parts = []
            async for chunk in stream:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content_parts.append(delta.content)
            
            insight = ''.join(content_parts).strip()
            
            # Store in long-term memory with high importance
            session_prefix = session_id or 'global'
            self.memory.add_long_term(
                f"[{session_prefix}] {insight}",
                importance=0.8
            )
            
            logger.debug(f"Extracted insight for session {session_id}: {insight[:50]}...")
            
        except Exception as e:
            # Log but don't fail the main operation
            logger.warning(f"Failed to extract insights: {str(e)}")
            
    async def get_conversation_analysis(
        self,
        messages: List[Message],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed analysis of a conversation.
        
        Args:
            messages: List of messages to analyze
            session_id: Optional session identifier
            
        Returns:
            Dictionary containing analysis metrics and summary
        """
        if not messages:
            return {
                "total_messages": 0,
                "user_messages": 0,
                "ai_messages": 0,
                "participants": [],
                "summary": "No messages to analyze."
            }
            
        # Calculate statistics
        total = len(messages)
        user_msgs = [m for m in messages if m.role == "user"]
        ai_msgs = [m for m in messages if m.role == "persona"]
        personas = list(set(m.persona_id for m in ai_msgs if m.persona_id))
        
        # Generate AI summary
        context = self._summarize_messages(messages, max_messages=20)
        summary_prompt = f"Summarize in 2 sentences:\n{context}"
        
        try:
            stream = await llm_service.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.5,
                max_tokens=100,
                stream=True
            )
            
            # Collect streaming response
            content_parts = []
            async for chunk in stream:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content_parts.append(delta.content)
            
            summary = ''.join(content_parts).strip()
            
            # Store summary for future reference
            if session_id:
                self.session_summaries[session_id] = summary
                self.memory.add_long_term(
                    f"Session {session_id}: {summary}",
                    importance=0.6
                )
                logger.info(f"Generated analysis for session {session_id}")
                
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            summary = "Unable to generate summary."
            
        return {
            "total_messages": total,
            "user_messages": len(user_msgs),
            "ai_messages": len(ai_msgs),
            "participants": personas,
            "summary": summary
        }
    
    def get_memory_stats(self) -> Dict[str, int]:
        """
        Get statistics about the global agent's memory.
        
        Returns:
            Dictionary with memory statistics
        """
        return {
            "short_term_memories": len(self.memory.short_term),
            "long_term_memories": len(self.memory.long_term),
            "total_queries": len(self.conversation_history),
            "session_summaries": len(self.session_summaries)
        }
    
    def get_memory_content(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the actual memory content for inspection.
        
        Returns:
            Dictionary containing short-term and long-term memories
        """
        return {
            "short_term": [
                {
                    "content": mem.content,
                    "timestamp": mem.timestamp.isoformat(),
                    "importance": mem.importance
                }
                for mem in self.memory.short_term[-10:]
            ],
            "long_term": [
                {
                    "content": mem.content,
                    "timestamp": mem.timestamp.isoformat(),
                    "importance": mem.importance
                }
                for mem in self.memory.long_term[-20:]
            ]
        }


# Singleton instance
global_agent_service = GlobalAgentService()

