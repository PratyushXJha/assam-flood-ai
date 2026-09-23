"""Simulation & Scenario Playback API Endpoints.
"""
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from app.scenarios.scenario_manager import scenario_manager
from app.scenarios.dataset_loader import DatasetError, DEFAULT_DATASET_PATH

router = APIRouter(prefix="/simulation", tags=["Simulation & Scenario Playback"])

MAX_UPLOAD_BYTES = 2_000_000

@router.get("/steps")
async def get_simulation_steps():
    """Retrieve the milestone steps of the historical scenario."""
    return {"steps": scenario_manager.get_timeline_steps(), "max_hour": scenario_manager.max_hour}

@router.get("/state")
async def get_current_pipeline_state():
    """Retrieve the unified, full pipeline state across all stages for the active hour."""
    return scenario_manager.get_full_pipeline_state()

@router.post("/compute/{hour}")
async def compute_hour(hour: int):
    """Run the full forecast pipeline on the dataset row for `hour` (0..72) and return the result."""
    return scenario_manager.compute_hour(hour)

@router.post("/set-step/{step_index}")
async def set_simulation_step(step_index: int):
    """Jump directly to a milestone step."""
    return scenario_manager.set_step(step_index)

@router.post("/forward")
async def advance_simulation():
    """Step forward to the next milestone."""
    return scenario_manager.step_forward()

@router.post("/backward")
async def step_backward_simulation():
    """Step backward to the previous milestone."""
    return scenario_manager.step_backward()

@router.post("/reset")
async def reset_simulation():
    """Reset simulation back to T=0."""
    return scenario_manager.reset()

@router.get("/dataset")
async def get_dataset_info():
    """Describe the active 72-hour telemetry dataset."""
    return scenario_manager.dataset_info()

@router.get("/dataset/template")
async def download_dataset_template():
    """Download the built-in 72-hour dataset CSV (also the upload template)."""
    return FileResponse(DEFAULT_DATASET_PATH, media_type="text/csv", filename=os.path.basename(DEFAULT_DATASET_PATH))

@router.post("/dataset")
async def upload_dataset(request: Request):
    """Replace the active dataset. Send the CSV as the raw request body (Content-Type: text/csv)."""
    body = await request.body()
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Dataset too large (max 2 MB).")
    try:
        text = body.decode("utf-8-sig")
        name = request.headers.get("x-filename", "uploaded.csv")[:80]
        return scenario_manager.load_dataset_csv(text, name=name)
    except (UnicodeDecodeError, DatasetError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/dataset/reset")
async def reset_dataset():
    """Restore the built-in 72-hour dataset."""
    return scenario_manager.reset_dataset()
