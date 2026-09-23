"""Read-only situation tools for the FloodCast AI assistant.

Each tool reads the live pipeline state (the hour currently computed by the simulation)
and returns a compact dict. The same functions back both the Claude tool-use loop and
the offline NLP engine, so every number the assistant quotes comes from here.
"""
import difflib
from typing import Any, Dict, List, Optional

from app.alerts.dispatcher import dispatcher
from app.config import EMERGENCY_CONTACTS
from app.scenarios.scenario_manager import scenario_manager


def _state() -> Dict[str, Any]:
    return scenario_manager.get_full_pipeline_state()


def _pretty(code: str) -> str:
    return code.replace("_", " ").title()


def _village_names(state: Dict[str, Any]) -> List[str]:
    return [v["village_name"] for v in state["stage3"]["ranked_villages"]]


def _match(query: str, choices: List[str]) -> Optional[str]:
    """Case-insensitive fuzzy match (substring first, then close spelling)."""
    q = query.strip().lower()
    if not q:
        return None
    for c in choices:
        if q in c.lower() or c.lower().split(" (")[0] in q:
            return c
    close = difflib.get_close_matches(q, [c.lower() for c in choices], n=1, cutoff=0.6)
    if close:
        return next(c for c in choices if c.lower() == close[0])
    return None


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def get_situation_overview() -> Dict[str, Any]:
    """Headline numbers, current phase, red zones, top-risk villages and alert delivery."""
    s = _state()
    kpi = s["kpi_summary"]
    red = [z for z in s["stage3"]["zones"] if z["level"] == "RED"]
    disp = dispatcher.status()["channels"]
    return {
        "time": s["current_step"]["time_label"],
        "hour": s["computation"]["hour"],
        "hours_of_data_left": kpi["lead_time_hours"],
        "phase": _pretty(s["current_step"]["phase_name"]),
        "phase_description": s["current_step"]["description"],
        "red_zones": [{"district": z["district"], "reason": z["reason"], "people_at_risk": z["population_at_risk"]} for z in red],
        "gauges_above_danger": kpi["danger_gauges_active"],
        "flooded_area_sq_km": kpi["flooded_area_sq_km"],
        "p1_extreme_risk_villages": kpi["critical_p1_villages"],
        "rescue_boats_deployed": kpi["rescue_boats_deployed"],
        "red_hill_triggers": kpi["red_hill_triggers"],
        "top_risk_villages": [
            {"village": v["village_name"], "district": v["district"], "risk_score": v["final_risk_score"],
             "tier": v["risk_tier"], "depth_m": v["estimated_flood_depth_m"]}
            for v in s["stage3"]["ranked_villages"][:5]
        ],
        "alerts": {
            "sms_sent": disp["sms"]["sent"], "sms_waiting": disp["sms"]["pending"],
            "calls_placed": disp["voice"]["sent"], "calls_waiting": disp["voice"]["pending"],
            "failed": disp["sms"]["failed"] + disp["voice"]["failed"],
        },
    }


def get_zones(level: Optional[str] = None) -> Dict[str, Any]:
    """Hazard zones graded RED / YELLOW / GREEN, optionally filtered by level."""
    zones = _state()["stage3"]["zones"]
    if level:
        zones = [z for z in zones if z["level"] == level.upper()]
    return {"zones": [
        {"name": z["name"], "district": z["district"], "level": z["level"], "reason": z["reason"],
         "bank_overtop_m": z["overtop_depth_m"], "flooded_sq_km": z["flooded_area_sq_km"],
         "people_at_risk": z["population_at_risk"],
         "villages": [f"{v['village_name']} ({_pretty(v['risk_tier'])}, {v['depth_m']} m)" for v in z["villages"]]}
        for z in zones
    ]}


def get_village(name: str) -> Dict[str, Any]:
    """Risk, depth, shelter, access route, relief sent and alert text for one village."""
    s = _state()
    match = _match(name, _village_names(s))
    if not match:
        return {"error": f"No village matching '{name}'.", "known_villages": _village_names(s)}
    v = next(x for x in s["stage3"]["ranked_villages"] if x["village_name"] == match)
    plan = next((p for p in s["stage3"]["allocation"]["dispatch_plan"] if p["village_id"] == v["village_id"]), None)
    alert = next((a for a in s["stage3"]["alerts"] if a["village_id"] == v["village_id"]), None)
    zone = next((z for z in s["stage3"]["zones"] if any(m["village_id"] == v["village_id"] for m in z["villages"])), None)
    access = v.get("access_profile", {})
    return {
        "village": v["village_name"], "district": v["district"], "population": v["population"],
        "river_char_island": v["char_island_status"], "rank": v["rank"],
        "risk_score": v["final_risk_score"], "risk_tier": v["risk_tier"], "main_risk_driver": v["primary_driver"],
        "flood_depth_m": v["estimated_flood_depth_m"], "evacuation": _pretty(v["evacuation_urgency"]),
        "zone": f"{zone['level']} - {zone['name']}" if zone else None,
        "shelter": v["nearest_camp_name"],
        "access_mode": access.get("access_mode"), "recommended_craft": access.get("recommended_craft"),
        "relief_sent": plan["allocated"] if plan else None,
        "relief_status": _pretty(plan["dispatch_status"]) if plan else None,
        "resident_sms_english": alert["languages"]["english"]["sms_body"] if alert else None,
    }


def get_river_gauges() -> Dict[str, Any]:
    """Current level vs warning/danger for each CWC gauge, with 24/48/72 h forecasts."""
    s = _state()
    trends = s["computation"]["gauge_trend_m_per_hr"]
    return {"gauges": [
        {"gauge": g["gauge_name"], "district": g["district"], "now_m": g["current_level_m"],
         "warning_m": g["warning_level_m"], "danger_m": g["danger_level_m"],
         "above_danger_by_m": round(g["current_level_m"] - g["danger_level_m"], 2),
         "status": _pretty(g["alert_status"]), "trend_cm_per_hr": round(trends.get(g["gauge_id"], 0.0) * 100, 1),
         "forecast_24h_m": g["forecast_24h_m"], "forecast_48h_m": g["forecast_48h_m"],
         "forecast_72h_m": g["forecast_72h_m"], "peak_predicted_m": g["peak_predicted_level_m"]}
        for g in s["stage2"]["gauges"]
    ]}


def get_hill_rainfall() -> Dict[str, Any]:
    """Upstream hill catchment rainfall triggers (Stage 1)."""
    return {"catchments": [
        {"catchment": t["catchment_name"], "region": t["region"], "alert": t["action_code"],
         "rain_mm_hr": t["telemetry"]["rainfall_rate_mm_hr"], "rain_6h_mm": t["telemetry"]["accum_6h_mm"],
         "soil_saturation_pct": t["telemetry"]["soil_moisture_pct"], "hours_until_plains": t["lead_time_hours"],
         "affects": t["affected_downstream_districts"]}
        for t in _state()["stage1"]["triggers"]
    ]}


def get_relief_status(district: Optional[str] = None) -> Dict[str, Any]:
    """Boats, medical teams and relief kits sent per village, and reserves left per district."""
    s = _state()
    alloc = s["stage3"]["allocation"]
    plan = alloc["dispatch_plan"]
    inventory = alloc["district_remaining_inventory"]
    if district:
        d = _match(district, list(inventory.keys()))
        if d:
            plan = [p for p in plan if p["district"] == d]
            inventory = {d: inventory[d]}
    return {
        "dispatches": [
            {"village": p["village_name"], "district": p["district"], "status": _pretty(p["dispatch_status"]),
             "boats": p["allocated"]["sdrf_inflatable_boats"] + p["allocated"]["ndrf_motor_boats"],
             "medical_teams": p["allocated"]["medical_teams"], "ration_kits": p["allocated"]["food_ration_kits"],
             "unmet_boats": p["unmet_shortfall"]["sdrf_inflatable_boats"] + p["unmet_shortfall"]["ndrf_motor_boats"]}
            for p in plan if p["estimated_flood_depth_m"] > 0.05
        ],
        "reserves_left": {
            d: {"boats": i["sdrf_inflatable_boats"] + i["ndrf_motor_boats"], "medical_teams": i["medical_teams"],
                "ration_kits": i["food_ration_kits"], "water_kits": i["water_purification_kits"]}
            for d, i in inventory.items()
        },
        "fulfilment_pct": alloc["aggregate_metrics"]["fulfillment_percentages"],
    }


def get_alert_dispatch_status() -> Dict[str, Any]:
    """SMS and AI voice-call delivery: sent, waiting, failed, send rate and ETA."""
    st = dispatcher.status()
    return {
        "provider": st["settings"]["provider"],
        "sms_per_minute": st["settings"]["sms_per_minute"], "calls_per_minute": st["settings"]["calls_per_minute"],
        "sms": {k: st["channels"]["sms"][k] for k in ("sent", "pending", "retrying", "failed", "eta_seconds")},
        "voice_calls": {k: st["channels"]["voice"][k] for k in ("sent", "pending", "retrying", "failed", "eta_seconds")},
    }


def get_recommended_actions() -> Dict[str, Any]:
    """Rule-based operational next steps derived from the current state."""
    s = _state()
    actions: List[str] = []
    zones = s["stage3"]["zones"]
    red = [z for z in zones if z["level"] == "RED"]
    disp = dispatcher.status()["channels"]
    sent_villages = {e["village_id"] for e in dispatcher.feed}

    unalerted = [z for z in red if not set(z["red_village_ids"]) & sent_villages]
    for z in unalerted:
        actions.append(f"Send SMS + AI voice alerts for the red zone in {z['district']} (no alerts sent yet).")

    short = [p for p in s["stage3"]["allocation"]["dispatch_plan"]
             if p["unmet_shortfall"]["sdrf_inflatable_boats"] + p["unmet_shortfall"]["ndrf_motor_boats"] > 0]
    for p in short[:3]:
        n = p["unmet_shortfall"]["sdrf_inflatable_boats"] + p["unmet_shortfall"]["ndrf_motor_boats"]
        actions.append(f"{p['village_name']} ({p['district']}) is short of {n} boat(s): request NDRF/SDRF reinforcement from a neighbouring district.")

    heli = [v for v in s["stage3"]["ranked_villages"] if v.get("access_profile", {}).get("access_mode") == "HELI_ONLY"]
    for v in heli:
        actions.append(f"{v['village_name']} is reachable only by air: request an IAF/NDRF helicopter airdrop.")

    rising = [g for g in s["stage2"]["gauges"]
              if g["current_level_m"] < g["danger_level_m"] <= g["forecast_24h_m"]]
    for g in rising:
        actions.append(f"{g['gauge_name']} is forecast to cross danger level within 24 h: pre-position boats in {g['district']}.")

    cut = [r for r in s["stage2"]["roads_status"] if r["status"] == "SUBMERGED_IMPASSABLE"]
    for r in cut:
        actions.append(f"{r['name']} is submerged. {r['detour_advice']}")

    if disp["sms"]["failed"] + disp["voice"]["failed"]:
        actions.append("Some alerts failed after retries: check the Alerts page and resend by another channel.")
    if disp["sms"]["pending"] > 50:
        actions.append(f"{disp['sms']['pending']} SMS are still queued; consider a cell broadcast for faster reach.")
    if not actions:
        actions.append("No urgent action needed. Keep monitoring upstream rainfall and gauge trends.")
    return {"actions": actions}


def get_emergency_contacts() -> Dict[str, Any]:
    """Assam emergency helpline numbers."""
    return {"helplines": EMERGENCY_CONTACTS}


TOOL_FUNCTIONS = {
    "get_situation_overview": get_situation_overview,
    "get_zones": get_zones,
    "get_village": get_village,
    "get_river_gauges": get_river_gauges,
    "get_hill_rainfall": get_hill_rainfall,
    "get_relief_status": get_relief_status,
    "get_alert_dispatch_status": get_alert_dispatch_status,
    "get_recommended_actions": get_recommended_actions,
    "get_emergency_contacts": get_emergency_contacts,
}

TOOL_SCHEMAS = [
    {"name": "get_situation_overview",
     "description": "Overall flood situation right now: simulation hour and phase, red zones, gauges above danger, flooded area, extreme-risk villages, boats deployed and alert delivery totals. Call this first for any general status question.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "get_zones",
     "description": "Hazard zones graded RED, YELLOW or GREEN with the reason, bank overtopping depth, flooded area, people at risk and the villages inside each.",
     "input_schema": {"type": "object", "properties": {
         "level": {"type": "string", "enum": ["RED", "YELLOW", "GREEN"], "description": "Only return zones at this level."}},
         "additionalProperties": False}},
    {"name": "get_village",
     "description": "Details for one village: risk score and tier, flood depth, zone, shelter, access route (road/boat/helicopter), relief sent and the resident SMS. Accepts partial or misspelled names.",
     "input_schema": {"type": "object", "properties": {"name": {"type": "string", "description": "Village name, e.g. 'Majuli Salmora' or 'Mandia'."}},
                      "required": ["name"], "additionalProperties": False}},
    {"name": "get_river_gauges",
     "description": "Every CWC river gauge: current level, warning and danger marks, how far above danger, rise rate and 24/48/72-hour forecasts.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "get_hill_rainfall",
     "description": "Upstream hill catchment rainfall, soil saturation and trigger alerts, with hours until the surge reaches the plains.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "get_relief_status",
     "description": "Relief dispatched per village (boats, medical teams, ration kits, shortfalls) and reserves left per district.",
     "input_schema": {"type": "object", "properties": {"district": {"type": "string", "description": "Optional district, e.g. 'Barpeta'."}},
                      "additionalProperties": False}},
    {"name": "get_alert_dispatch_status",
     "description": "Resident alert delivery: SMS and AI voice calls sent, waiting, retrying and failed, the send rate and time to clear the queue.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "get_recommended_actions",
     "description": "Suggested next operational steps (unalerted red zones, boat shortfalls, air-only villages, gauges about to cross danger, submerged roads, failed alerts).",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "get_emergency_contacts",
     "description": "Emergency helpline numbers for Assam.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
]


def run_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        raise KeyError(f"Unknown tool {name}")
    return fn(**(args or {}))
