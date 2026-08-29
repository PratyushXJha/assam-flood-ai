"""Explainable Risk Scoring Engine for Stage 3.
Calculates multi-criteria vulnerability and flood impact scores per village
with 100% transparent mathematical factor attribution.
"""
from typing import Dict, Any, List
import numpy as np

class RiskScorer:
    def __init__(self):
        # Explicit weights for full explainability
        self.weights = {
            "flood_depth": 0.40,
            "vulnerability_index": 0.30,
            "isolation_penalty": 0.30
        }

    def compute_risk_score(
        self,
        village_info: Dict[str, Any],
        is_road_cut_off: bool = False
    ) -> Dict[str, Any]:
        """
        Compute normalized risk score (0-100) and explainable component breakdown.
        """
        flood_depth_m = village_info.get("estimated_flood_depth_m", 0.0)
        vulnerability_idx = village_info.get("vulnerability_index", 0.70)
        is_char = village_info.get("char_island_status", False)
        population = village_info.get("population", 5000)

        # 1. Depth score component (0 to 100): reaches 100 at 2.5m depth
        depth_subscore = min(100.0, (flood_depth_m / 2.5) * 100.0)

        # 2. Vulnerability component (0 to 100): based on demographic fragility
        vuln_subscore = min(100.0, vulnerability_idx * 100.0)

        # 3. Isolation component (0 to 100): char status + road cutoff status
        if is_char and is_road_cut_off:
            isolation_subscore = 100.0
            isolation_label = "CRITICAL_ISLAND_AND_ROAD_BREACH"
        elif is_char:
            isolation_subscore = 85.0
            isolation_label = "RIVERINE_CHAR_SANDBAR"
        elif is_road_cut_off:
            isolation_subscore = 75.0
            isolation_label = "ACCESS_ROAD_SUBMERGED"
        elif flood_depth_m > 0.3:
            isolation_subscore = 35.0
            isolation_label = "MARGINAL_WATERLOGGING"
        else:
            isolation_subscore = 10.0
            isolation_label = "CONNECTED_ROAD_OPEN"

        # 4. Population scaling factor: logarithmic multiplier
        # 1000 pop -> 1.0, 5000 pop -> 1.21, 10000 pop -> 1.30
        pop_multiplier = 0.85 + 0.30 * np.log10(max(100.0, population) / 1000.0)
        pop_multiplier = max(0.80, min(1.35, pop_multiplier))

        # Weighted combination
        weighted_base = (
            self.weights["flood_depth"] * depth_subscore +
            self.weights["vulnerability_index"] * vuln_subscore +
            self.weights["isolation_penalty"] * isolation_subscore
        )

        final_raw_score = weighted_base * pop_multiplier
        final_risk_score = round(float(min(100.0, max(0.0, final_raw_score))), 1)

        # Risk Classification
        if final_risk_score >= 75.0:
            risk_tier = "EXTREME_PRIORITY_P1"
            tier_color = "#ef4444"  # Red
            evacuation_urgency = "IMMEDIATE_MANDATORY_EVACUATION"
        elif final_risk_score >= 50.0:
            risk_tier = "HIGH_PRIORITY_P2"
            tier_color = "#f97316"  # Orange
            evacuation_urgency = "HIGH_PRIORITY_RELIEF_DISPATCH"
        elif final_risk_score >= 25.0:
            risk_tier = "MODERATE_PRIORITY_P3"
            tier_color = "#eab308"  # Yellow
            evacuation_urgency = "ALERT_MONITOR_WATER_RISE"
        else:
            risk_tier = "LOW_MONITORING_P4"
            tier_color = "#10b981"  # Green
            evacuation_urgency = "STANDBY_OBSERVATION"

        # Identify primary risk driver
        drivers = [
            ("Flood Depth Inundation", self.weights["flood_depth"] * depth_subscore),
            ("Demographic Fragility", self.weights["vulnerability_index"] * vuln_subscore),
            ("Physical Isolation / Char", self.weights["isolation_penalty"] * isolation_subscore)
        ]
        drivers.sort(key=lambda x: x[1], reverse=True)
        primary_driver = drivers[0][0]

        return {
            "village_id": village_info["village_id"],
            "village_name": village_info["village_name"],
            "district": village_info["district"],
            "latitude": village_info["latitude"],
            "longitude": village_info["longitude"],
            "population": population,
            "char_island_status": is_char,
            "estimated_flood_depth_m": round(flood_depth_m, 2),
            "final_risk_score": final_risk_score,
            "risk_tier": risk_tier,
            "tier_color": tier_color,
            "evacuation_urgency": evacuation_urgency,
            "primary_driver": primary_driver,
            "explainability": {
                "depth_subscore": round(depth_subscore, 1),
                "vulnerability_subscore": round(vuln_subscore, 1),
                "isolation_subscore": round(isolation_subscore, 1),
                "isolation_reason": isolation_label,
                "population_multiplier": round(pop_multiplier, 2),
                "weights_used": self.weights
            },
            "nearest_camp_name": village_info.get("nearest_camp_name", "District High Ground Shelter"),
            "nearest_camp_coords": village_info.get("nearest_camp_coords", [village_info["latitude"], village_info["longitude"]])
        }

    def rank_all_villages(
        self,
        villages_depth_data: List[Dict[str, Any]],
        submerged_road_districts: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Compute risk scores for all villages and sort descending by priority.
        """
        if submerged_road_districts is None:
            submerged_road_districts = []

        scored_villages = []
        for v in villages_depth_data:
            # Check if road to village is submerged
            is_cutoff = v["district"] in submerged_road_districts or v.get("estimated_flood_depth_m", 0) > 0.8
            scored = self.compute_risk_score(v, is_road_cut_off=is_cutoff)
            scored_villages.append(scored)

        # Sort descending by final risk score
        scored_villages.sort(key=lambda x: x["final_risk_score"], reverse=True)

        # Assign ordinal rank
        for idx, item in enumerate(scored_villages):
            item["rank"] = idx + 1

        return scored_villages
