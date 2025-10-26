"""Service for generating personas from conversation transcripts."""
from typing import List, Dict, Optional
import re
from collections import defaultdict

from models.persona import PersonaCreate, PersonaType
from services.llm_service import llm_service
from core.config import settings


class PersonaGenerator:
    """Generate personas from conversation analysis."""
    
    def __init__(self):
        self.conversation_patterns = [
            r"^(.+?):\s*(.+)$",  # "Name: message"
            r"^(.+?)\s*-\s*(.+)$",  # "Name - message"
            r"^\[(.+?)\]\s*(.+)$",  # "[Name] message"
            r"^<(.+?)>\s*(.+)$",  # "<Name> message"
        ]
    
    async def generate_from_conversation(
        self,
        conversation_text: str,
        persona_type: PersonaType = PersonaType.USER
    ) -> List[PersonaCreate]:
        """Generate personas from a conversation transcript."""
        # Parse conversation
        participants = self._parse_conversation(conversation_text)
        
        if not participants:
            raise ValueError("No valid conversation format detected")
        
        # Generate personas for each participant
        personas = []
        for name, messages in participants.items():
            persona = await self._generate_persona(name, messages, persona_type)
            personas.append(persona)
        
        return personas
    
    def _parse_conversation(self, text: str) -> Dict[str, List[str]]:
        """Parse conversation text into participants and their messages."""
        participants = defaultdict(list)
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try each pattern
            for pattern in self.conversation_patterns:
                match = re.match(pattern, line)
                if match:
                    name = match.group(1).strip()
                    message = match.group(2).strip()
                    if message:  # Only add non-empty messages
                        participants[name].append(message)
                    break
        
        return dict(participants)
    
    async def _generate_persona(
        self,
        name: str,
        messages: List[str],
        persona_type: PersonaType
    ) -> PersonaCreate:
        """Generate a persona based on conversation analysis."""
        # Analyze speaking style and generate system prompt
        sample_messages = "\n".join(messages[:10])  # Use first 10 messages
        
        analysis_prompt = f"""Analyze "{name}" from these messages:
{sample_messages}

Create 2-sentence system prompt ("You are...") capturing their style/personality.

Format:
SYSTEM_PROMPT: [2 sentences max]
DESCRIPTION: [1 sentence]"""

        try:
            stream = await llm_service.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7,
                max_tokens=150,
                stream=True
            )
            
            # Collect streaming response
            content_parts = []
            async for chunk in stream:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content_parts.append(delta.content)
            
            content = ''.join(content_parts).strip()
            
            # Parse response
            system_prompt = self._extract_field(content, "SYSTEM_PROMPT")
            description = self._extract_field(content, "DESCRIPTION")
            
            # Fallback if parsing fails
            if not system_prompt:
                system_prompt = f"You are {name}, someone who communicates in a clear and engaging way."
            if not description:
                description = f"A participant in conversations"
            
        except Exception as e:
            # Fallback persona if LLM fails
            system_prompt = f"You are {name}, a thoughtful person who engages in meaningful conversations."
            description = f"A conversation participant"
        
        return PersonaCreate(
            name=name,
            persona_type=persona_type,
            system_prompt=system_prompt,
            description=description
        )
    
    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """Extract a field from the LLM response."""
        pattern = rf"{field_name}:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None
    
    async def generate_single_persona(
        self,
        name: str,
        description: str,
        traits: List[str],
        persona_type: PersonaType = PersonaType.USER
    ) -> PersonaCreate:
        """Generate a single persona from user-provided information."""
        traits_text = ", ".join(traits) if traits else "friendly and engaging"
        
        prompt = f"""Create 2-sentence system prompt:
Name: {name}
Description: {description}
Traits: {traits_text}

Format: "You are..." (2 sentences only)"""

        try:
            stream = await llm_service.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
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
            
            system_prompt = ''.join(content_parts).strip()
            
            if not system_prompt:
                system_prompt = f"You are {name}. {description}"
            
        except Exception:
            # Fallback
            system_prompt = f"You are {name}. {description} You are {traits_text} in your conversations."
        
        return PersonaCreate(
            name=name,
            persona_type=persona_type,
            system_prompt=system_prompt,
            description=description
        )


# Singleton instance
persona_generator = PersonaGenerator()

