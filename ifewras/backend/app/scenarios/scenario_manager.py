"""Scenario playback and full-pipeline orchestration manager.
Runs Stage 1 -> Stage 2 -> Stage 3 for any hour of the fed 72-hour dataset.
"""
import time
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
from app.stage3_relief.zone_classifier import ZoneClassifier
from app.scenarios.historical_assam_2024 import SCENARIO_TIMELINE
from app.scenarios.dataset_loader import load_default_dataset, parse_dataset_csv

TREND_WINDOW_HOURS = 6
TREND_CLAMP_M_PER_HR = (-0.08, 0.12)


class ScenarioManager:
    def __init__(self):
        self.timeline = SCENARIO_TIMELINE
        self.dataset = load_default_dataset()
        self.dataset_name = "assam_72h_dataset.csv (built-in)"
        self.current_hour = 0

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
        self.zone_classifier = ZoneClassifier()

    # ---------- dataset ----------
    @property
    def max_hour(self) -> int:
        return len(self.dataset) - 1

    def load_dataset_csv(self, text: str, name: str = "uploaded.csv") -> Dict[str, Any]:
        """Replace the active dataset (raises DatasetError on invalid input) and rewind to hour 0."""
        self.dataset = parse_dataset_csv(text)
        self.dataset_name = name
        self.current_hour = 0
        return self.dataset_info()

    def reset_dataset(self) -> Dict[str, Any]:
        self.dataset = load_default_dataset()
        self.dataset_name = "assam_72h_dataset.csv (built-in)"
        self.current_hour = 0
        return self.dataset_info()

    def dataset_info(self) -> Dict[str, Any]:
        first = self.dataset[0]
        return {
            "name": self.dataset_name,
            "hours": self.max_hour,
            "rows": len(self.dataset),
            "catchments": sorted(first["stage1_telemetry"].keys()),
            "gauges": sorted(first["stage2_gauge_readings"].keys()),
        }

    # ---------- navigation ----------
    def get_timeline_steps(self) -> List[Dict[str, Any]]:
        """Return basic metadata of the milestone steps."""
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

    def _milestone_for_hour(self, hour: int) -> Dict[str, Any]:
        current = self.timeline[0]
        for step in self.timeline:
            if step["time_offset_hours"] <= hour:
                current = step
        return current

    def compute_hour(self, hour: int) -> Dict[str, Any]:
        """Run the full prediction pipeline on the dataset row for `hour`."""
        self.current_hour = max(0, min(self.max_hour, int(hour)))
        return self.get_full_pipeline_state()

    def set_step(self, step_idx: int) -> Dict[str, Any]:
        """Jump to a milestone step (0 -> T+0h, 1 -> T+24h, ...)."""
        if 0 <= step_idx < len(self.timeline):
            self.current_hour = min(self.max_hour, self.timeline[step_idx]["time_offset_hours"])
        return self.get_full_pipeline_state()

    def step_forward(self) -> Dict[str, Any]:
        """Advance to the next milestone."""
        later = [s["time_offset_hours"] for s in self.timeline if s["time_offset_hours"] > self.current_hour]
        self.current_hour = min(self.max_hour, later[0]) if later else self.max_hour
        return self.get_full_pipeline_state()

    def step_backward(self) -> Dict[str, Any]:
        """Go back to the previous milestone."""
        earlier = [s["time_offset_hours"] for s in self.timeline if s["time_offset_hours"] < self.current_hour]
        self.current_hour = earlier[-1] if earlier else 0
        return self.get_full_pipeline_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to T=0."""
        self.current_hour = 0
        return self.get_full_pipeline_state()

    # ---------- pipeline ----------
    def _gauge_trend_rates(self, hour: int) -> Dict[str, float]:
        """Observed rise rate (m/hr) per gauge over the trailing window of the dataset."""
        if hour == 0:
            return {}
        past = self.dataset[max(0, hour - TREND_WINDOW_HOURS)]["stage2_gauge_readings"]
        now = self.dataset[hour]["stage2_gauge_readings"]
        span = min(hour, TREND_WINDOW_HOURS)
        lo, hi = TREND_CLAMP_M_PER_HR
        return {gid: round(max(lo, min(hi, (now[gid] - past[gid]) / span)), 4) for gid in now if gid in past}

    def get_full_pipeline_state(self) -> Dict[str, Any]:
        """
        Execute the full Stage 1 -> Stage 2 -> Stage 3 pipeline for the current hour.
        """
        started = time.perf_counter()
        hour = self.current_hour
        frame = self.dataset[hour]
        milestone = self._milestone_for_hour(hour)

        # STAGE 1: Hill Catchments & Triggers
        s1_triggers = self.trigger_detector.evaluate_all_catchments(frame["stage1_telemetry"])

        # Compute upstream surge volumes to feed into Stage 2
        upstream_surges = {t["catchment_id"]: t["runoff"]["accum_6h_volume_mcm"] for t in s1_triggers}

        # STAGE 2: River Gauges, Forecasts, Inundation Extent, Villages & Roads
        trend_rates = self._gauge_trend_rates(hour)
        s2_forecasts = self.forecast_model.forecast_all_gauges(frame["stage2_gauge_readings"], upstream_surges, trend_rates)

        # Map current gauge levels for extent and depth models
        gauge_levels_map = {g["gauge_id"]: g["current_level_m"] for g in s2_forecasts}
        s2_extent_geojson = self.dem_model.generate_full_extent_geojson(gauge_levels_map)
        s2_villages_depth = self.village_engine.compute_all_villages(gauge_levels_map)
        s2_roads_status = self.road_engine.evaluate_all_roads(gauge_levels_map)

        # STAGE 3: Risk Scoring, Access Profiling, Allocation, Zones & Multilingual Alerts
        submerged_districts = [r["district"] for r in s2_roads_status if r["status"] == "SUBMERGED_IMPASSABLE"]
        s3_ranked_villages = self.risk_scorer.rank_all_villages(s2_villages_depth, submerged_districts)
        s3_profiled_villages = self.access_profiler.profile_all_villages(s3_ranked_villages, s2_roads_status)
        s3_allocation = self.allocation_engine.allocate_resources(s3_profiled_villages)
        s3_alerts = self.alert_generator.generate_all_alerts(s3_allocation["dispatch_plan"])
        s3_zones = self.zone_classifier.classify(gauge_levels_map, s2_villages_depth, s3_profiled_villages)

        # High-level Executive Summary Indicators
        red_triggers_count = len([t for t in s1_triggers if t["action_code"] == "RED_ALERT"])
        danger_gauges_count = len([g for g in s2_forecasts if g["current_level_m"] >= g["danger_level_m"]])
        critical_villages_count = len([v for v in s3_ranked_villages if v["risk_tier"] == "EXTREME_PRIORITY_P1"])
        boats_deployed_count = s3_allocation["aggregate_metrics"]["total_allocated"]["sdrf_inflatable_boats"] + \
                               s3_allocation["aggregate_metrics"]["total_allocated"]["ndrf_motor_boats"]

        return {
            "current_step": {
                "step_index": milestone["step_index"],
                "time_offset_hours": hour,
                "time_label": f"T+{hour:02d}h : {milestone['time_label'].split(' : ', 1)[-1]}",
                "phase_name": milestone["phase_name"],
                "description": milestone["description"]
            },
            "computation": {
                "hour": hour,
                "max_hour": self.max_hour,
                "dataset": self.dataset_name,
                "gauge_trend_m_per_hr": trend_rates,
                "compute_ms": round((time.perf_counter() - started) * 1000.0, 2),
            },
            "kpi_summary": {
                "lead_time_hours": self.max_hour - hour,
                "red_hill_triggers": red_triggers_count,
                "danger_gauges_active": danger_gauges_count,
                "flooded_area_sq_km": s2_extent_geojson["metadata"]["total_inundated_sq_km"],
                "critical_p1_villages": critical_villages_count,
                "rescue_boats_deployed": boats_deployed_count,
                "dispatches_en_route": s3_allocation["aggregate_metrics"]["total_villages_served"],
                "red_zones": len([z for z in s3_zones if z["level"] == "RED"])
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
                "alerts": s3_alerts,
                "zones": s3_zones
            }
        }

# Global Singleton Manager
scenario_manager = ScenarioManager()
