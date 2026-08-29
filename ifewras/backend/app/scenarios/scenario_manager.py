"""Scenario playback and full-pipeline orchestration manager.
Executes Stage 1 -> Stage 2 -> Stage 3 synchronically for any simulation step.
"""
from typing import Dict, Any, List
from app.stage1_hills.trigger_detector import TriggerDetector
from app.stage2_plains.forecast_model import RiverForecastModel
from app.stage2_plains.dem_floodfill import DEMFloodFillModel
from app.stage2_plains.village_depth import VillageDepthEngine
from app.stage2_plains.road_submersion import RoadSubmersionEngine
from app.stage3_relief.risk_scorer import RiskScorer
from app.stage3_relief.access_profiler import AccessProfiler
from app.stage3_relief.allocation_engine import ReliefAllocationEngine
from app.stage3_relief.alert_generator import AlertGenerator
from app.scenarios.historical_assam_2024 import SCENARIO_TIMELINE

class ScenarioManager:
    def __init__(self):
        self.timeline = SCENARIO_TIMELINE
        self.current_step_idx = 0

        # Instantiate pipeline engines
        self.trigger_detector = TriggerDetector()
        self.forecast_model = RiverForecastModel()
        self.dem_model = DEMFloodFillModel()
        self.village_engine = VillageDepthEngine()
        self.road_engine = RoadSubmersionEngine()
        self.risk_scorer = RiskScorer()
        self.access_profiler = AccessProfiler()
        self.allocation_engine = ReliefAllocationEngine()
        self.alert_generator = AlertGenerator()

    def get_timeline_steps(self) -> List[Dict[str, Any]]:
        """Return basic metadata of all available simulation steps."""
        return [
            {
                "step_index": s["step_index"],
                "time_offset_hours": s["time_offset_hours"],
                "time_label": s["time_label"],
                "phase_name": s["phase_name"],
                "description": s["description"]
            }
            for s in self.timeline
        ]

    def set_step(self, step_idx: int) -> Dict[str, Any]:
        """Jump to a specific simulation step."""
        if 0 <= step_idx < len(self.timeline):
            self.current_step_idx = step_idx
        return self.get_full_pipeline_state()

    def step_forward(self) -> Dict[str, Any]:
        """Advance one step forward in time."""
        if self.current_step_idx < len(self.timeline) - 1:
            self.current_step_idx += 1
        return self.get_full_pipeline_state()

    def step_backward(self) -> Dict[str, Any]:
        """Step one step backward in time."""
        if self.current_step_idx > 0:
            self.current_step_idx -= 1
        return self.get_full_pipeline_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to T=0."""
        self.current_step_idx = 0
        return self.get_full_pipeline_state()

    def get_full_pipeline_state(self) -> Dict[str, Any]:
        """
        Execute the full Stage 1 -> Stage 2 -> Stage 3 pipeline for the current timestep.
        """
        step_data = self.timeline[self.current_step_idx]

        # STAGE 1: Hill Catchments & Triggers
        s1_telemetry = step_data["stage1_telemetry"]
        s1_triggers = self.trigger_detector.evaluate_all_catchments(s1_telemetry)

        # Compute upstream surge volumes to feed into Stage 2
        upstream_surges = {}
        for t in s1_triggers:
            upstream_surges[t["catchment_id"]] = t["runoff"]["accum_6h_volume_mcm"]

        # STAGE 2: River Gauges, Forecasts, Inundation Extent, Villages & Roads
        s2_levels = step_data["stage2_gauge_readings"]
        s2_forecasts = self.forecast_model.forecast_all_gauges(s2_levels, upstream_surges)

        # Map current gauge levels for extent and depth models
        gauge_levels_map = {g["gauge_id"]: g["current_level_m"] for g in s2_forecasts}
        s2_extent_geojson = self.dem_model.generate_full_extent_geojson(gauge_levels_map)
        s2_villages_depth = self.village_engine.compute_all_villages(gauge_levels_map)
        s2_roads_status = self.road_engine.evaluate_all_roads(gauge_levels_map)

        # STAGE 3: Risk Scoring, Access Profiling, Allocation & Multilingual Alerts
        submerged_districts = [r["district"] for r in s2_roads_status if r["status"] == "SUBMERGED_IMPASSABLE"]
        s3_ranked_villages = self.risk_scorer.rank_all_villages(s2_villages_depth, submerged_districts)
        s3_profiled_villages = self.access_profiler.profile_all_villages(s3_ranked_villages, s2_roads_status)
        s3_allocation = self.allocation_engine.allocate_resources(s3_profiled_villages)
        s3_alerts = self.alert_generator.generate_all_alerts(s3_allocation["dispatch_plan"])

        # High-level Executive Summary Indicators
        red_triggers_count = len([t for t in s1_triggers if t["action_code"] == "RED_ALERT"])
        danger_gauges_count = len([g for g in s2_forecasts if g["current_level_m"] >= g["danger_level_m"]])
        critical_villages_count = len([v for v in s3_ranked_villages if v["risk_tier"] == "EXTREME_PRIORITY_P1"])
        boats_deployed_count = s3_allocation["aggregate_metrics"]["total_allocated"]["sdrf_inflatable_boats"] + \
                               s3_allocation["aggregate_metrics"]["total_allocated"]["ndrf_motor_boats"]

        return {
            "current_step": {
                "step_index": step_data["step_index"],
                "time_offset_hours": step_data["time_offset_hours"],
                "time_label": step_data["time_label"],
                "phase_name": step_data["phase_name"],
                "description": step_data["description"]
            },
            "kpi_summary": {
                "lead_time_hours": 72 - step_data["time_offset_hours"],
                "red_hill_triggers": red_triggers_count,
                "danger_gauges_active": danger_gauges_count,
                "flooded_area_sq_km": s2_extent_geojson["metadata"]["total_inundated_sq_km"],
                "critical_p1_villages": critical_villages_count,
                "rescue_boats_deployed": boats_deployed_count,
                "dispatches_en_route": s3_allocation["aggregate_metrics"]["total_villages_served"]
            },
            "stage1": {
                "triggers": s1_triggers
            },
            "stage2": {
                "gauges": s2_forecasts,
                "extent_geojson": s2_extent_geojson,
                "villages_depth": s2_villages_depth,
                "roads_status": s2_roads_status
            },
            "stage3": {
                "ranked_villages": s3_profiled_villages,
                "allocation": s3_allocation,
                "alerts": s3_alerts
            }
        }

# Global Singleton Manager
scenario_manager = ScenarioManager()
