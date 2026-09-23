"""Alert Dispatch API: throttled SMS, AI voice calls and the resident alert feed.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.alerts.dispatcher import dispatcher
from app.scenarios.scenario_manager import scenario_manager

router = APIRouter(prefix="/alerts", tags=["Alert Dispatch (SMS + AI Voice)"])


class DispatchRequest(BaseModel):
    zone_id: Optional[str] = None
    village_ids: Optional[List[str]] = None
    channels: List[str] = ["sms", "voice"]


class DispatchSettings(BaseModel):
    sms_per_minute: Optional[float] = None
    calls_per_minute: Optional[float] = None
    max_retries: Optional[int] = None
    retry_backoff_seconds: Optional[float] = None


@router.post("/dispatch")
async def dispatch_alerts(req: DispatchRequest):
    """Queue SMS + AI voice-call alerts for a red zone or a list of villages (sent at a throttled rate)."""
    state = scenario_manager.get_full_pipeline_state()
    alerts = {a["village_id"]: a for a in state["stage3"]["alerts"]}
    zone = None
    if req.zone_id:
        zone = next((z for z in state["stage3"]["zones"] if z["zone_id"] == req.zone_id), None)
        if zone is None:
            raise HTTPException(status_code=404, detail="Unknown zone_id")
        village_ids = zone["red_village_ids"] or [v["village_id"] for v in zone["villages"]]
    elif req.village_ids:
        village_ids = req.village_ids
    else:
        raise HTTPException(status_code=400, detail="Provide zone_id or village_ids")

    packages = [alerts[v] for v in village_ids if v in alerts]
    if not packages:
        raise HTTPException(status_code=404, detail="No matching villages")
    return dispatcher.enqueue_alerts(packages, req.channels, zone)


@router.get("/dispatch/status")
async def dispatch_status():
    """Queue depth, sent/failed counts, send rate and recent delivery log."""
    return dispatcher.status()


@router.post("/dispatch/clear")
async def clear_dispatch_queue():
    """Clear the dispatch queue and log."""
    dispatcher.reset()
    return dispatcher.status()


@router.get("/settings")
async def get_dispatch_settings():
    return dispatcher.public_settings()


@router.put("/settings")
async def update_dispatch_settings(body: DispatchSettings):
    """Change SMS / call send rates and retry policy."""
    return dispatcher.update_settings(body.model_dump())


@router.get("/feed")
async def resident_alert_feed(since: int = 0, village_id: Optional[str] = None):
    """Alerts broadcast to resident devices after event id `since` (polled by the receiver page)."""
    events = dispatcher.feed_since(since, village_id)
    latest = dispatcher.feed[-1]["event_id"] if dispatcher.feed else 0
    return {"latest_event_id": latest, "events": events}
