"""Simulation & Scenario Playback API Endpoints.
"""
from fastapi import APIRouter
from app.scenarios.scenario_manager import scenario_manager

router = APIRouter(prefix="/simulation", tags=["Simulation & Scenario Playback"])

@router.get("/steps")
async def get_simulation_steps():
    """Retrieve all chronological steps of the historical scenario."""
    return {"steps": scenario_manager.get_timeline_steps()}

@router.get("/state")
async def get_current_pipeline_state():
    """Retrieve the unified, full pipeline state across all stages for the active timestep."""
    return scenario_manager.get_full_pipeline_state()

@router.post("/set-step/{step_index}")
async def set_simulation_step(step_index: int):
    """Jump directly to a specific timestep."""
    return scenario_manager.set_step(step_index)

@router.post("/forward")
async def advance_simulation():
    """Step forward one increment in time."""
    return scenario_manager.step_forward()

@router.post("/backward")
async def step_backward_simulation():
    """Step backward one increment in time."""
    return scenario_manager.step_backward()

@router.post("/reset")
async def reset_simulation():
    """Reset simulation back to T=0."""
    return scenario_manager.reset()
