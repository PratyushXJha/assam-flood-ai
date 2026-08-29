"""Stage 3 API Endpoints (Help the People).
"""
from fastapi import APIRouter
from app.scenarios.scenario_manager import scenario_manager

router = APIRouter(prefix="/stage3", tags=["Stage 3: Help the People"])

@router.get("/risk-rankings")
async def get_village_risk_rankings():
    """Retrieve prioritized risk scores, rankings, and explainability breakdowns."""
    state = scenario_manager.get_full_pipeline_state()
    return {
        "timestamp_offset": state["current_step"]["time_label"],
        "ranked_villages": state["stage3"]["ranked_villages"]
    }

@router.get("/allocation")
async def get_relief_allocation_plan():
    """Retrieve resource-constrained dispatch plan and remaining inventory."""
    state = scenario_manager.get_full_pipeline_state()
    return {
        "timestamp_offset": state["current_step"]["time_label"],
        "allocation_plan": state["stage3"]["allocation"]["dispatch_plan"],
        "district_remaining_inventory": state["stage3"]["allocation"]["district_remaining_inventory"],
        "aggregate_metrics": state["stage3"]["allocation"]["aggregate_metrics"]
    }

@router.get("/alerts")
async def get_multilingual_resident_alerts():
    """Retrieve multilingual resident emergency alerts (Assamese, Bodo, English)."""
    state = scenario_manager.get_full_pipeline_state()
    return {
        "timestamp_offset": state["current_step"]["time_label"],
        "alerts": state["stage3"]["alerts"]
    }
