"""Trigger detection engine for Stage 1 (Watch the Hills).
Evaluates satellite rainfall intensity, accumulation, and terrain soil moisture
to flag upstream flash-flood triggers with 3-6 hour lead times before plains impact.
"""
from typing import Dict, Any, List
from app.config import STAGE1_THRESHOLDS
from app.stage1_hills.catchments import get_all_catchments, get_catchment_by_id
from app.stage1_hills.rainfall_engine import RainfallEngine

class TriggerDetector:
    def __init__(self):
        self.rainfall_engine = RainfallEngine()
        self.thresholds = STAGE1_THRESHOLDS

    def evaluate_catchment_trigger(
        self,
        catchment_id: str,
        rate_mm_hr: float,
        accum_6h_mm: float,
        accum_24h_mm: float,
        soil_moisture_pct: float
    ) -> Dict[str, Any]:
        """
        Evaluate flash-flood trigger severity for an individual upstream catchment.
        """
        catchment = get_catchment_by_id(catchment_id)
        runoff_data = self.rainfall_engine.calculate_effective_runoff(
            catchment_id=catchment_id,
            rainfall_rate_mm_hr=rate_mm_hr,
            accum_6h_mm=accum_6h_mm,
            soil_moisture_pct=soil_moisture_pct
        )

        # Trigger score components
        rate_ratio = rate_mm_hr / self.thresholds["flash_flood_rate_mm_hr"]
        accum6_ratio = accum_6h_mm / self.thresholds["accum_6h_trigger_mm"]
        accum24_ratio = accum_24h_mm / self.thresholds["accum_24h_trigger_mm"]
        moisture_ratio = soil_moisture_pct / self.thresholds["soil_saturation_critical_pct"]

        # Composite trigger score (0 to 100)
        raw_score = (rate_ratio * 35.0) + (accum6_ratio * 30.0) + (accum24_ratio * 20.0) + (moisture_ratio * 15.0)
        trigger_score = min(100.0, max(0.0, raw_score))

        # Severity categorization
        if trigger_score >= 80.0 or rate_mm_hr >= 45.0 or accum_6h_mm >= 100.0:
            severity = "FLASH_FLOOD_EMERGENCY"
            action_code = "RED_ALERT"
            lead_time_status = "CRITICAL_SURGE_IMMINENT"
        elif trigger_score >= 55.0 or accum_6h_mm >= 65.0:
            severity = "TRIGGER_WARNING"
            action_code = "ORANGE_ALERT"
            lead_time_status = "SURGE_PROPAGATING"
        elif trigger_score >= 35.0 or rate_mm_hr >= 15.0:
            severity = "ADVISORY"
            action_code = "YELLOW_ALERT"
            lead_time_status = "ELEVATED_WATCH"
        else:
            severity = "NORMAL"
            action_code = "GREEN"
            lead_time_status = "NO_IMMEDIATE_THREAT"

        # Confidence calculation based on telemetry consistency
        confidence = round(0.88 + min(0.10, (soil_moisture_pct / 100.0) * 0.08), 2)

        return {
            "catchment_id": catchment_id,
            "catchment_name": catchment["name"],
            "region": catchment["region"],
            "severity": severity,
            "action_code": action_code,
            "trigger_score": round(trigger_score, 1),
            "lead_time_hours": catchment["lag_time_hours"],
            "lead_time_status": lead_time_status,
            "confidence": confidence,
            "telemetry": {
                "rainfall_rate_mm_hr": rate_mm_hr,
                "accum_6h_mm": accum_6h_mm,
                "accum_24h_mm": accum_24h_mm,
                "soil_moisture_pct": soil_moisture_pct
            },
            "runoff": runoff_data,
            "affected_downstream_districts": catchment["downstream_districts"],
            "affected_downstream_gauges": catchment["downstream_gauges"],
            "drainage_summary": catchment["drainage_direction"],
            "timestamp": "Live Simulation Stream"
        }

    def evaluate_all_catchments(self, snapshot_data: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """
        Evaluate all catchments against a snapshot dataset.
        """
        results = []
        for catchment in get_all_catchments():
            cid = catchment["id"]
            telemetry = snapshot_data.get(cid, {
                "rate_mm_hr": 8.0,
                "accum_6h_mm": 22.0,
                "accum_24h_mm": 45.0,
                "soil_moisture_pct": 58.0
            })
            eval_result = self.evaluate_catchment_trigger(
                catchment_id=cid,
                rate_mm_hr=telemetry.get("rate_mm_hr", 5.0),
                accum_6h_mm=telemetry.get("accum_6h_mm", 20.0),
                accum_24h_mm=telemetry.get("accum_24h_mm", 45.0),
                soil_moisture_pct=telemetry.get("soil_moisture_pct", 55.0)
            )
            results.append(eval_result)
        return results
