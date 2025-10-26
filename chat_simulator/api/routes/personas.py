"""API routes for persona management (async DB version)."""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
import json

from models.persona import Persona, PersonaCreate, PersonaUpdate
from models.persona_generation import (
    ConversationUpload,
    PersonaGenerationRequest,
    PersonaGenerationResponse
)
from services.persona_service_db import persona_service_db as persona_service
from services.persona_generator import persona_generator


router = APIRouter()


@router.post("/", response_model=Persona, status_code=201)
async def create_persona(persona_data: PersonaCreate):
    """Create a new persona. Prevents duplicate persona names."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Creating persona: {persona_data.dict()}")
    try:
        # Check for duplicate names
        if await persona_service.persona_name_exists(persona_data.name):
            raise HTTPException(
                status_code=400,
                detail=f"Persona with name '{persona_data.name}' already exists"
            )
        
        persona = await persona_service.create_persona(persona_data)
        logger.info(f"Persona created successfully: {persona.id}")
        return persona
    except ValueError as e:
        logger.error(f"ValueError creating persona: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating persona: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/", response_model=List[Persona])
async def list_personas(active_only: bool = True):
    """List all personas."""
    personas = await persona_service.list_personas(active_only)
    return personas


@router.get("/{persona_id}", response_model=Persona)
async def get_persona(persona_id: str):
    """Get a specific persona."""
    persona = await persona_service.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona


@router.put("/{persona_id}", response_model=Persona)
async def update_persona(persona_id: str, persona_data: PersonaUpdate):
    """Update a persona."""
    persona = await persona_service.update_persona(persona_id, persona_data)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona


@router.delete("/{persona_id}")
async def delete_persona(persona_id: str):
    """Delete a persona."""
    success = await persona_service.delete_persona(persona_id)
    if not success:
        raise HTTPException(status_code=404, detail="Persona not found")
    return {"message": "Persona deleted successfully"}


@router.post("/{persona_id}/memory")
async def add_memory(
    persona_id: str,
    content: str,
    memory_type: str = "short_term",
    importance: float = 0.5
):
    """Add memory to persona."""
    try:
        await persona_service.add_memory(persona_id, content, memory_type, importance)
        return {"message": "Memory added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add memory: {str(e)}")


@router.post("/generate/from-conversation", response_model=PersonaGenerationResponse)
async def generate_from_conversation(request: ConversationUpload):
    """
    Generate personas from a conversation transcript.
    
    Accepts conversations in formats like:
    - "Name: message"
    - "Name - message"  
    - "[Name] message"
    - "<Name> message"
    
    Duplicate names are automatically skipped to prevent persona duplication.
    """
    try:
        # Generate personas
        personas_data = await persona_generator.generate_from_conversation(
            request.conversation_text,
            request.persona_type
        )
        
        created_ids = []
        preview = []
        skipped = []
        
        # Create personas if requested
        if request.auto_create:
            for persona_data in personas_data:
                # Check if persona with this name already exists
                if await persona_service.persona_name_exists(persona_data.name):
                    skipped.append(persona_data.name)
                    # Add existing persona to preview
                    existing = await persona_service.get_persona_by_name(persona_data.name)
                    if existing:
                        preview.append({
                            "id": existing.id,
                            "name": existing.name,
                            "system_prompt": existing.system_prompt,
                            "description": existing.description,
                            "already_exists": True
                        })
                    continue
                
                try:
                    persona = await persona_service.create_persona(persona_data)
                    created_ids.append(persona.id)
                    preview.append({
                        "id": persona.id,
                        "name": persona.name,
                        "system_prompt": persona.system_prompt,
                        "description": persona.description,
                        "already_exists": False
                    })
                except ValueError as e:
                    # Skip if duplicate somehow slipped through
                    skipped.append(persona_data.name)
        else:
            # Just preview
            for persona_data in personas_data:
                preview.append({
                    "name": persona_data.name,
                    "system_prompt": persona_data.system_prompt,
                    "description": persona_data.description
                })
        
        # Build response message
        message = f"Generated {len(personas_data)} persona(s) from conversation"
        if skipped:
            message += f". Skipped {len(skipped)} duplicate(s): {', '.join(skipped)}"
        if request.auto_create:
            message = f"Created {len(created_ids)} new persona(s). " + message
        
        return PersonaGenerationResponse(
            personas_created=created_ids,
            personas_preview=preview,
            count=len(created_ids) if request.auto_create else len(personas_data),
            message=message
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate personas: {str(e)}")


@router.post("/generate/from-description", response_model=Persona)
async def generate_from_description(request: PersonaGenerationRequest):
    """
    Generate a persona from a description and traits.
    
    Uses AI to create an appropriate system prompt based on the provided information.
    If a persona with the same name already exists, returns an error.
    """
    try:
        # Check if persona name already exists
        if await persona_service.persona_name_exists(request.name):
            raise HTTPException(
                status_code=400, 
                detail=f"Persona with name '{request.name}' already exists"
            )
        
        # Generate persona
        persona_data = await persona_generator.generate_single_persona(
            name=request.name,
            description=request.description,
            traits=request.traits,
            persona_type=request.persona_type
        )
        
        # Create persona
        persona = await persona_service.create_persona(persona_data)
        return persona
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate persona: {str(e)}")


@router.post("/generate/from-file", response_model=PersonaGenerationResponse)
async def generate_from_file(
    file: UploadFile = File(...),
    persona_type: str = "user",
    auto_create: bool = True
):
    """
    Generate personas from an uploaded conversation file.
    
    Supports .txt files with conversation transcripts.
    """
    try:
        # Read file
        content = await file.read()
        conversation_text = content.decode('utf-8')
        
        # Generate personas
        request = ConversationUpload(
            conversation_text=conversation_text,
            persona_type=persona_type,
            auto_create=auto_create
        )
        
        return await generate_from_conversation(request)
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be a valid text file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

