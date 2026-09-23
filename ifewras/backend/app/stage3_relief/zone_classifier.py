"""Red / Yellow / Green hazard zone classification.

Each DEM flood zone is graded from its computed overtopping depth and the risk tiers
of the villages it contains. Only RED zones raise operator popups and resident alerts.
"""
from typing import Any, Dict, List

from app.stage2_plains.dem_floodfill import DEMFloodFillModel

ZONE_COLORS = {"RED": "#ef4444", "YELLOW": "#eab308", "GREEN": "#10b981"}
RED_OVERTOP_M = 1.5  # Bank overtopping depth that makes a zone RED on its own


class ZoneClassifier:
    def __init__(self):
        self.dem_model = DEMFloodFillModel()

    def classify(
        self,
        gauge_levels: Dict[str, float],
        villages_depth: List[Dict[str, Any]],
        ranked_villages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        gauge_by_village = {v["village_id"]: v["closest_gauge_id"] for v in villages_depth}
        affected_by_village = {v["village_id"]: v["affected_population"] for v in villages_depth}

        zones = []
        for zone in self.dem_model.zones:
            gid = zone["associated_gauge"]
            extent = self.dem_model.compute_zone_extent(zone, gauge_levels.get(gid, zone["base_bank_level_m"]))
            members = [v for v in ranked_villages if gauge_by_village.get(v["village_id"]) == gid]
            red_villages = [v for v in members if v["risk_tier"] == "EXTREME_PRIORITY_P1"]
            watch_villages = [
                v for v in members
                if v["risk_tier"] in ("HIGH_PRIORITY_P2", "MODERATE_PRIORITY_P3") and v["estimated_flood_depth_m"] > 0
            ]

            overtop = extent["overtop_depth_m"]
            if red_villages or overtop >= RED_OVERTOP_M:
                level = "RED"
                reason = (
                    f"{len(red_villages)} P1 village(s) at extreme risk" if red_villages
                    else f"Bank overtopped by {overtop} m"
                )
            elif watch_villages or overtop > 0:
                level = "YELLOW"
                reason = "Water above bank level; monitor" if overtop > 0 else "Elevated village risk; monitor"
            else:
                level = "GREEN"
                reason = "Below bank level"

            zones.append({
                "zone_id": zone["zone_id"],
                "name": zone["name"],
                "district": zone["district"],
                "level": level,
                "color": ZONE_COLORS[level],
                "reason": reason,
                "center": zone["center"],  # [lat, lon]
                "overtop_depth_m": overtop,
                "flooded_area_sq_km": extent["flooded_area_sq_km"],
                "geometry": extent["geojson_geometry"],
                "population_at_risk": sum(affected_by_village.get(v["village_id"], 0) for v in red_villages),
                "villages": [
                    {
                        "village_id": v["village_id"],
                        "village_name": v["village_name"],
                        "risk_tier": v["risk_tier"],
                        "risk_score": v["final_risk_score"],
                        "depth_m": v["estimated_flood_depth_m"],
                        "latitude": v["latitude"],
                        "longitude": v["longitude"],
                    }
                    for v in members
                ],
                "red_village_ids": [v["village_id"] for v in red_villages],
            })
        return zones
