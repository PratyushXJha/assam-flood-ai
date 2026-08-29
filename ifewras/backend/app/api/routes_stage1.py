"""Stage 1 API Endpoints (Watch the Hills).
"""
from fastapi import APIRouter
from app.stage1_hills.catchments import get_all_catchments
from app.scenarios.scenario_manager import scenario_manager

router = APIRouter(prefix="/stage1", tags=["Stage 1: Watch the Hills"])

@router.get("/catchments")
async def get_catchments_list():
    """Retrieve metadata and boundary coordinates for all upstream hill catchments."""
    return {"catchments": get_all_catchments()}

@router.get("/triggers")
async def get_current_triggers():
    """Retrieve live/current trigger assessments, rainfall telemetry, and runoff estimates."""
    state = scenario_manager.get_full_pipeline_state()
    return {
        "timestamp_offset": state["current_step"]["time_label"],
        "triggers": state["stage1"]["triggers"]
    }
