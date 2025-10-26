"""
Letta-powered Global Agent Service

This module provides an enhanced global agent using Letta's stateful memory system.
The agent maintains persistent memory, context, and learning across all sessions.

Letta Documentation: https://docs.letta.com/overview
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from models.message import Message
from core.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Enable debug logging for Letta service


class LettaGlobalAgentService:
    """
    Letta-powered Global Meta-Advisor Service
    
    Provides high-level analysis and strategic insights using Letta's advanced
    memory management system. Unlike the basic global agent, this agent:
    - Maintains persistent state across server restarts
    - Has intelligent memory consolidation
    - Can learn and evolve continuously
    - Supports "sleep-time" processing for insights
    
    Reference: https://docs.letta.com/overview
    """
    
    def __init__(self) -> None:
        """Initialize the Letta-powered global agent service."""
        self.client = None
        self.agent_id = None
        self.initialized = False
        self.fallback_history: List[Dict[str, Any]] = []
        self.persona_service = None  # Will be set when needed
        
        # Only initialize if Letta is enabled
        if settings.LETTA_ENABLED:
            self._initialize_letta_agent()
        else:
            logger.warning(
                "Letta is not enabled. Set LETTA_ENABLED=True and configure LETTA_API_KEY "
                "in your .env file to use Letta for the global agent."
            )
    
    def _initialize_letta_agent(self) -> None:
        """Initialize Letta client and agent."""
        try:
            from letta_client import Letta
            
            logger.info("Initializing Letta client...")
            self.client = Letta(token=settings.LETTA_API_KEY)
            
            # Try to find existing agent or create new one
            try:
                # List all agents
                agents_response = self.client.agents.list()
                existing_agent = None
                
                # Search for existing agent by name
                for agent in agents_response:
                    if hasattr(agent, 'name') and agent.name == settings.LETTA_AGENT_NAME:
                        existing_agent = agent
                        break
                
                if existing_agent:
                    self.agent_id = existing_agent.id
                    logger.info(f"Found existing Letta agent: {self.agent_id}")
                else:
                    logger.info("Creating new Letta agent...")
                    agent_state = self.client.agents.create(
                        model=settings.LETTA_MODEL,
                        embedding=settings.LETTA_EMBEDDING,
                        memory_blocks=[
                            {
                                "label": "human",
                                "value": (
                                    "System: Chat Simulator. "
                                    "Provides conversation transcripts in format 'Speaker: message'. "
                                    "Tracks all participants and their interactions."
                                )
                            },
                            {
                                "label": "persona",
                                "value": (
                                    "You are a Global Meta-Advisor AI analyzing conversations. "
                                    "You track who said what (User/Persona names in messages). "
                                    "Identify patterns, analyze dynamics between speakers, provide strategic insights. "
                                    "Remember key facts about each participant across sessions. "
                                    "CRITICAL: Responses must be 3-4 sentences max. Be direct and actionable."
                                )
                            }
                        ],
                        tools=["web_search"]  # Optional: web_search, run_code
                    )
                    self.agent_id = agent_state.id
                    logger.info(f"Created new Letta agent: {self.agent_id}")
                
                self.initialized = True
                logger.info("Letta global agent initialized successfully!")
                
            except Exception as e:
                logger.error(f"Error finding/creating Letta agent: {e}")
                raise
                
        except ImportError as e:
            logger.warning(
                f"Letta package not properly installed or incompatible: {e}. "
                "Try: pip install letta OR pip install letta-client. "
                "Falling back to traditional global agent."
            )
            self.initialized = False
        except Exception as e:
            logger.warning(f"Failed to initialize Letta agent: {e}. Using fallback mode.")
            self.initialized = False
    
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
    
    async def get_advice(
        self,
        all_messages: List[Message],
        user_question: str,
        session_id: Optional[str] = None
    ) -> str:
        """
        Generate advice from the global agent using Letta's stateful memory.
        
        Args:
            all_messages: All messages from the session(s)
            user_question: The user's question
            session_id: Optional session ID for context
            
        Returns:
            Generated advice as a string
        """
        # Fallback to basic response if Letta not initialized
        if not self.initialized:
            return self._get_fallback_advice(all_messages, user_question, session_id)
        
        try:
            # Prepare context for Letta
            context = self._summarize_messages(all_messages)
            
            # Build detailed message for Letta agent with conversation history
            session_prefix = f"[Session: {session_id}] " if session_id else ""
            
            if all_messages:
                prompt = (
                    f"{session_prefix}Conversation History ({len(all_messages)} messages):\n"
                    f"---\n"
                    f"{context}\n"
                    f"---\n\n"
                    f"User Question: {user_question}\n\n"
                    f"Analyze the conversation above and answer in 3-4 sentences."
                )
            else:
                prompt = (
                    f"{session_prefix}Question: {user_question}\n\n"
                    f"(No conversation history available yet)\n\n"
                    f"Answer in 3-4 sentences:"
                )
            
            # Send message to Letta agent and get response
            logger.info(f"Sending advice request to Letta agent: {self.agent_id}")
            response = self.client.agents.messages.create(
                agent_id=self.agent_id,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract the assistant's response from Letta
            # Debug: log the response structure
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response has messages: {hasattr(response, 'messages')}")
            
            advice_parts = []
            
            # Try to extract messages
            if hasattr(response, 'messages'):
                logger.debug(f"Number of messages: {len(response.messages)}")
                for idx, message in enumerate(response.messages):
                    logger.debug(f"Message {idx}: type={type(message)}, has role={hasattr(message, 'role')}")
                    
                    # Try different ways to access content
                    content = None
                    if hasattr(message, 'content'):
                        content = message.content
                    elif hasattr(message, 'text'):
                        content = message.text
                    elif isinstance(message, dict):
                        content = message.get('content') or message.get('text')
                    
                    if content:
                        # Check role if available
                        role = getattr(message, 'role', None) or (message.get('role') if isinstance(message, dict) else None)
                        logger.debug(f"Message {idx}: role={role}, content_preview={str(content)[:50]}")
                        
                        # Accept assistant messages or messages without role info
                        if not role or role == 'assistant':
                            advice_parts.append(str(content))
            
            advice = "\n".join(advice_parts).strip()
            
            if not advice:
                logger.warning(f"No advice content received from Letta. Response object: {response}")
                advice = "I'm processing your request. Please try again."
            
            # Record in fallback history for debugging
            self.fallback_history.append({
                "question": user_question,
                "advice": advice,
                "context_size": len(all_messages),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "provider": "letta"
            })
            
            logger.info(
                f"Generated Letta advice for session {session_id}, "
                f"{len(all_messages)} messages analyzed"
            )
            
            return advice
            
        except Exception as e:
            logger.error(f"Error getting advice from Letta: {str(e)}", exc_info=True)
            # Fallback to basic response
            return self._get_fallback_advice(all_messages, user_question, session_id)
    
    def _get_fallback_advice(
        self,
        all_messages: List[Message],
        user_question: str,
        session_id: Optional[str]
    ) -> str:
        """Provide fallback advice when Letta is unavailable."""
        logger.warning("Using fallback advice generation (Letta unavailable)")
        
        self.fallback_history.append({
            "question": user_question,
            "advice": "Letta unavailable - using fallback",
            "context_size": len(all_messages),
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "provider": "fallback"
        })
        
        return (
            f"I'm currently operating in fallback mode. To enable Letta's advanced "
            f"stateful memory for the global agent:\n\n"
            f"1. Set LETTA_ENABLED=True in your .env file\n"
            f"2. Configure your LETTA_API_KEY\n"
            f"3. Restart the server\n\n"
            f"Your question was: {user_question}\n\n"
            f"Context: {len(all_messages)} messages in conversation"
        )
    
    async def get_conversation_analysis(
        self,
        messages: List[Message],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed analysis of a conversation using Letta.
        
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
        
        # Generate summary using Letta if available
        if self.initialized:
            try:
                context = self._summarize_messages(messages, max_messages=20)
                prompt = f"Summarize in 2 sentences:\n{context}"
                
                response = self.client.agents.messages.create(
                    agent_id=self.agent_id,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Extract summary from response messages
                summary_parts = []
                for message in response.messages:
                    if hasattr(message, 'role') and message.role == 'assistant':
                        if hasattr(message, 'content') and message.content:
                            summary_parts.append(str(message.content))
                
                summary = "\n".join(summary_parts).strip()
                
                if not summary:
                    summary = f"Conversation with {len(personas)} participants over {total} messages."
                
                logger.info(f"Generated Letta analysis for session {session_id}")
                
            except Exception as e:
                logger.error(f"Failed to generate Letta summary: {str(e)}")
                summary = f"Conversation with {len(personas)} participants over {total} messages."
        else:
            summary = f"Conversation with {len(personas)} participants over {total} messages."
        
        return {
            "total_messages": total,
            "user_messages": len(user_msgs),
            "ai_messages": len(ai_msgs),
            "participants": personas,
            "summary": summary,
            "letta_enabled": self.initialized
        }
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the global agent's memory.
        
        Returns:
            Dictionary with memory statistics
        """
        stats = {
            "letta_enabled": self.initialized,
            "total_queries": len(self.fallback_history),
            "agent_id": self.agent_id if self.initialized else None
        }
        
        if self.initialized and self.client:
            try:
                # Get agent state from Letta using retrieve method
                agent_state = self.client.agents.retrieve(self.agent_id)
                stats["agent_name"] = getattr(agent_state, 'name', "unknown")
                stats["letta_status"] = "active"
            except Exception as e:
                logger.warning(f"Could not retrieve Letta agent details: {e}")
                stats["letta_status"] = "active"  # Still active even if details fail
        else:
            stats["letta_status"] = "disabled"
        
        return stats
    
    def get_memory_content(self) -> Dict[str, Any]:
        """
        Get the actual memory content for inspection.
        
        Returns:
            Dictionary containing Letta agent's memory state
        """
        if not self.initialized or not self.client:
            return {
                "letta_enabled": False,
                "message": "Letta is not enabled. Configure LETTA_API_KEY to use Letta memory."
            }
        
        try:
            # Get agent state with memory blocks using retrieve method
            agent_state = self.client.agents.retrieve(self.agent_id)
            
            memory_data = {
                "letta_enabled": True,
                "agent_id": self.agent_id,
                "agent_name": getattr(agent_state, 'name', 'unknown'),
                "memory_blocks": []
            }
            
            # Extract memory blocks if available
            if hasattr(agent_state, 'memory'):
                memory = agent_state.memory
                if hasattr(memory, 'blocks'):
                    for block in memory.blocks:
                        memory_data["memory_blocks"].append({
                            "label": getattr(block, 'label', 'unknown'),
                            "value": getattr(block, 'value', ''),
                            "limit": getattr(block, 'limit', None)
                        })
            
            # Add recent interactions
            memory_data["recent_interactions"] = self.fallback_history[-10:]
            
            return memory_data
            
        except Exception as e:
            logger.error(f"Error getting Letta memory content: {e}", exc_info=True)
            return {
                "letta_enabled": True,
                "error": str(e),
                "recent_interactions": self.fallback_history[-10:]
            }


# Singleton instance
letta_global_agent_service = LettaGlobalAgentService()

