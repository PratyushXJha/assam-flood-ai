"""Stage 2 API Endpoints (Predict the Plains).
"""
from fastapi import APIRouter
from app.stage2_plains.cwc_gauges import get_all_gauges
from app.scenarios.scenario_manager import scenario_manager

router = APIRouter(prefix="/stage2", tags=["Stage 2: Predict the Plains"])

@router.get("/gauges")
async def get_gauges_and_forecasts():
    """Retrieve CWC gauge levels, 24/48/72h forecasts, and hydrographs."""
    state = scenario_manager.get_full_pipeline_state()
    return {
        "timestamp_offset": state["current_step"]["time_label"],
        "gauges": state["stage2"]["gauges"]
    }

@router.get("/extent")
async def get_flood_extent_geojson():
    """Retrieve GeoJSON FeatureCollection of inundation polygons across Assam."""
    state = scenario_manager.get_full_pipeline_state()
    return state["stage2"]["extent_geojson"]

@router.get("/villages")
async def get_villages_flood_depth():
    """Retrieve village-level estimated flood depths and affected populations."""
    state = scenario_manager.get_full_pipeline_state()
    return {
        "timestamp_offset": state["current_step"]["time_label"],
        "villages": state["stage2"]["villages_depth"]
    }

@router.get("/roads")
async def get_roads_submersion_status():
    """Retrieve road network statuses, flood depths, and detour recommendations."""
    state = scenario_manager.get_full_pipeline_state()
    return {
        "timestamp_offset": state["current_step"]["time_label"],
        "roads": state["stage2"]["roads_status"]
    }
