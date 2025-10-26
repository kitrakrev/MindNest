"""API routes for simulation management."""
from fastapi import APIRouter, HTTPException, Request
from typing import List

from models.simulation import Simulation, SimulationCreate, SimulationUpdate
from services.simulation_service import SimulationService


router = APIRouter()


def get_simulation_service(request: Request) -> SimulationService:
    """Get or create simulation service."""
    if not hasattr(request.app.state, 'simulation_service'):
        request.app.state.simulation_service = SimulationService(
            request.app.state.queue_manager
        )
    return request.app.state.simulation_service


@router.post("/", response_model=Simulation, status_code=201)
async def create_simulation(simulation_data: SimulationCreate, request: Request):
    """Create a new simulation."""
    service = get_simulation_service(request)
    try:
        simulation = await service.create_simulation(simulation_data)
        return simulation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[Simulation])
async def list_simulations(request: Request):
    """List all simulations."""
    service = get_simulation_service(request)
    simulations = await service.list_simulations()
    return simulations


@router.get("/{simulation_id}", response_model=Simulation)
async def get_simulation(simulation_id: str, request: Request):
    """Get a specific simulation."""
    service = get_simulation_service(request)
    simulation = await service.get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulation


@router.put("/{simulation_id}", response_model=Simulation)
async def update_simulation(
    simulation_id: str,
    simulation_data: SimulationUpdate,
    request: Request
):
    """Update a simulation."""
    service = get_simulation_service(request)
    simulation = await service.update_simulation(simulation_id, simulation_data)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulation


@router.delete("/{simulation_id}")
async def delete_simulation(simulation_id: str, request: Request):
    """Delete a simulation."""
    service = get_simulation_service(request)
    success = await service.delete_simulation(simulation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return {"message": "Simulation deleted successfully"}


@router.post("/{simulation_id}/start")
async def start_simulation(simulation_id: str, request: Request):
    """Start a simulation."""
    service = get_simulation_service(request)
    success = await service.start_simulation(simulation_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot start simulation (not found or already running)"
        )
    return {"message": "Simulation started successfully"}


@router.post("/{simulation_id}/pause")
async def pause_simulation(simulation_id: str, request: Request):
    """Pause a simulation."""
    service = get_simulation_service(request)
    success = await service.pause_simulation(simulation_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause simulation")
    return {"message": "Simulation paused successfully"}


@router.post("/{simulation_id}/stop")
async def stop_simulation(simulation_id: str, request: Request):
    """Stop a simulation."""
    service = get_simulation_service(request)
    success = await service.stop_simulation(simulation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return {"message": "Simulation stopped successfully"}

