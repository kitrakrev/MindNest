"""LLM service for generating persona responses."""
from typing import List, Dict, Optional
from openai import AsyncOpenAI
import json
import logging

from models.message import Message
from models.persona import Persona
from core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM."""
    
    def __init__(self):
        logger.info(f"Initializing LLM client with base_url={settings.LLM_BASE_URL}")
        import httpx
        
        # Create custom HTTP client with increased timeouts and retries
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            follow_redirects=True
        )
        
        self.client = AsyncOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            timeout=60.0,
            max_retries=3,
            http_client=http_client
        )
        
    async def generate_response(
        self,
        persona: Persona,
        conversation_history: List[Message],
        context: Optional[str] = None
    ) -> str:
        """Generate response for a persona based on conversation history."""
        messages = self._build_messages(persona, conversation_history, context)
        
        try:
            logger.debug(f"Sending streaming request with {len(messages)} messages")
            stream = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                stream=True  # Enable streaming
            )
            
            # Collect streaming response
            content_parts = []
            async for chunk in stream:
                # Handle OpenAI streaming chunk format
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content_parts.append(delta.content)
            
            full_content = ''.join(content_parts)
            
            if full_content:
                logger.info(f"Successfully streamed {len(content_parts)} chunks, total {len(full_content)} chars")
                return full_content.strip()
            else:
                logger.warning("No content received from streaming response")
                return "..."
                
        except Exception as e:
            logger.error(f"LLM API Error: {e}", exc_info=True)
            raise RuntimeError(f"LLM API Error: {str(e)}")
            
    async def generate_tldr(
        self,
        messages: List[Message],
        custom_prompt: Optional[str] = None,
        format: str = 'text'
    ) -> str:
        """Generate TLDR summary of conversation.
        
        Args:
            messages: List of messages to summarize
            custom_prompt: Optional custom prompt override
            format: 'text' for narrative summary (2-3 paragraphs), 
                   'video' for bullet-point style summary
        """
        if not messages:
            return "No messages to summarize."
        
        # Build conversation text for AI processing
        conversation_text = "\n".join([
            f"{msg.role.value} ({msg.persona_id or 'system'}): {msg.content}"
            for msg in messages
        ])
        
        # Choose prompt based on format
        if custom_prompt:
            prompt = custom_prompt
        elif format == 'text':
            # Text format: Generate narrative summary
            prompt = (
                "Summarize the following conversation in 2-3 concise paragraphs.\n"
                "Focus on:\n"
                "• Main topics and themes discussed\n"
                "• Key points or decisions made\n"
                "• Overall tone and outcome\n\n"
                "Write a flowing narrative summary, not bullet points.\n"
                "Be professional and informative."
            )
        else:
            # Video format: Generate bullet-point summary
            prompt = (
                "Create a YouTube-style video summary with:\n"
                "• 3-5 bullet points of key moments\n"
                "• Each point: emoji + brief insight\n"
                "• Format: '▶️ [Topic]: brief description'\n"
                "Keep it punchy and engaging like video chapter markers."
            )
        
        messages_payload = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": conversation_text}
        ]
        
        try:
            logger.debug(f"Generating TLDR summary ({format} format) with streaming")
            
            # Adjust max_tokens based on format
            max_tokens = 300 if format == 'text' else 150
            
            stream = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages_payload,
                temperature=0.5,
                max_tokens=max_tokens,
                stream=True  # Enable streaming
            )
            
            # Collect streaming response
            content_parts = []
            async for chunk in stream:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content_parts.append(delta.content)
            
            full_content = ''.join(content_parts)
            
            if full_content:
                logger.info("TLDR generated successfully via streaming")
                return full_content.strip()
            else:
                logger.warning("No TLDR content received, using fallback")
                return f"Summary: {len(messages)} messages exchanged in the conversation"
                
        except Exception as e:
            logger.error(f"Failed to generate TLDR: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate TLDR: {str(e)}")
            
    def _build_messages(
        self,
        persona: Persona,
        conversation_history: List[Message],
        context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build message payload for LLM."""
        messages = [
            {"role": "system", "content": self._build_system_prompt(persona, context)}
        ]
        
        # Add conversation history
        for msg in conversation_history[-20:]:  # Last 20 messages
            role = "assistant" if msg.persona_id == persona.id else "user"
            messages.append({
                "role": role,
                "content": msg.content
            })
            
        return messages
        
    def _build_system_prompt(
        self,
        persona: Persona,
        context: Optional[str] = None
    ) -> str:
        """Build system prompt with persona information and memory."""
        prompt_parts = [
            persona.system_prompt,
            "\n\nIMPORTANT: Keep responses concise (2-3 sentences max). Be precise and direct."
        ]
        
        # Add long-term memory context (reduced to 3)
        if persona.memory.long_term:
            memory_context = "\n".join([
                f"- {mem.content}"
                for mem in persona.memory.long_term[-3:]
            ])
            prompt_parts.append(f"\n\nKey memories:\n{memory_context}")
            
        # Add short-term memory context (reduced to 2)
        if persona.memory.short_term:
            memory_context = "\n".join([
                f"- {mem.content}"
                for mem in persona.memory.short_term[-2:]
            ])
            prompt_parts.append(f"\n\nRecent:\n{memory_context}")
            
        # Add additional context
        if context:
            prompt_parts.append(f"\n\nContext:\n{context}")
            
        return "\n".join(prompt_parts)
    
    async def decide_engagement(
        self,
        persona: Persona,
        message_content: str
    ) -> Dict[str, any]:
        """
        Decide if a persona would engage with and share a message.
        
        Returns:
            dict with 'engage' (bool), 'reason' (str), 'priority' (float 0-1)
        """
        prompt = f"""You are {persona.name}, a {persona.persona_type}.

Your personality: {persona.description or persona.system_prompt}

You just heard this message/topic: "{message_content}"

Would you engage with this message and share it with others?

Consider:
- Does this topic interest you based on your personality?
- Is this relevant to your expertise or concerns?
- Would you want to discuss or spread this information?

Respond in JSON format:
{{
    "engage": true/false,
    "reason": "brief explanation (10-20 words)",
    "priority": 0.0-1.0 (how much you care)
}}

Be authentic to your character. Only engage if it truly matches your interests."""

        try:
            # Use streaming to collect response (more reliable across different providers)
            stream = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a decision-making assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150,
                stream=True  # Use streaming for compatibility
            )
            
            # Collect streaming response
            content_parts = []
            async for chunk in stream:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content_parts.append(delta.content)
            
            content = ''.join(content_parts).strip()
            
            if not content:
                logger.warning(f"Empty content received for {persona.name}")
                raise ValueError("Empty response from LLM")
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            result = json.loads(content)
            
            # Validate response
            return {
                "engage": bool(result.get("engage", False)),
                "reason": str(result.get("reason", "No reason given")),
                "priority": float(result.get("priority", 0.5))
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse engagement decision JSON for {persona.name}: {e}")
            # Fallback: random decision
            return {
                "engage": False,
                "reason": "Unable to decide",
                "priority": 0.3
            }
        except Exception as e:
            logger.error(f"Error in decide_engagement for {persona.name}: {e}", exc_info=True)
            return {
                "engage": False,
                "reason": "Error occurred",
                "priority": 0.0
            }


# Singleton instance
llm_service = LLMService()

