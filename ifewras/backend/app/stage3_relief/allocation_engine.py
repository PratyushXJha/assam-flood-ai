"""Resource-constrained relief allocation engine for Stage 3.
Optimizes deployment of finite district assets (SDRF/NDRF boats, medical teams,
food kits, water purification packs) calibrated against ASDMA operational norms.
"""
from typing import Dict, Any, List
import copy
from app.config import DEFAULT_DISTRICT_RESOURCES

class ReliefAllocationEngine:
    def __init__(self):
        self.default_resources = DEFAULT_DISTRICT_RESOURCES

    def calculate_village_demand(self, village: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate resource requirements based on village population, depth, and isolation.
        """
        depth_m = village.get("estimated_flood_depth_m", 0.0)
        pop = village.get("population", 4000)
        is_char = village.get("char_island_status", False)
        vuln = village.get("vulnerability_index", 0.70)
        access_mode = village.get("access_profile", {}).get("access_mode", "BOAT_ONLY" if is_char else "ROAD_CONNECTED")

        if depth_m <= 0.05:
            # Standby demand only
            return {
                "sdrf_inflatable_boats": 0,
                "ndrf_motor_boats": 0,
                "medical_teams": 0,
                "food_ration_kits": 0,
                "water_purification_kits": 0
            }

        # Estimate people needing immediate evacuation / boat shuttling
        evac_fraction = min(0.60, 0.15 + (depth_m / 2.5) * 0.40) if (is_char or depth_m > 0.6) else 0.08
        evac_people = int(pop * evac_fraction)

        # Boat requirements (each boat cycle ferries ~15-20 people/hour)
        if access_mode == "BOAT_ONLY" or is_char:
            if depth_m >= 1.5 or is_char:
                ndrf_boats_needed = max(1, min(4, int(np_ceil(evac_people / 600.0))))
                sdrf_boats_needed = max(1, min(6, int(np_ceil(evac_people / 300.0))))
            else:
                ndrf_boats_needed = max(0, min(2, int(np_ceil(evac_people / 800.0))))
                sdrf_boats_needed = max(1, min(5, int(np_ceil(evac_people / 350.0))))
        else:
            ndrf_boats_needed = 0
            sdrf_boats_needed = 1 if depth_m > 0.4 else 0

        # Medical teams needed: anti-venom, ORS, trauma kits
        if vuln > 0.85 or depth_m >= 1.2:
            medical_teams_needed = max(1, min(3, int(np_ceil(pop / 3000.0))))
        elif depth_m > 0.3:
            medical_teams_needed = 1
        else:
            medical_teams_needed = 0

        # Relief kits: 1 food ration kit per ~4 people; 1 water kit per ~3 people
        affected_pop = int(pop * min(1.0, 0.25 + (depth_m / 2.0) * 0.75))
        food_kits_needed = int(affected_pop / 4.0)
        water_kits_needed = int(affected_pop / 3.0)

        return {
            "sdrf_inflatable_boats": sdrf_boats_needed,
            "ndrf_motor_boats": ndrf_boats_needed,
            "medical_teams": medical_teams_needed,
            "food_ration_kits": food_kits_needed,
            "water_purification_kits": water_kits_needed
        }

    def allocate_resources(
        self,
        ranked_villages_with_profile: List[Dict[str, Any]],
        custom_district_inventory: Dict[str, Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Execute prioritized resource-constrained allocation across all villages.
        """
        if custom_district_inventory is None:
            inventory = copy.deepcopy(self.default_resources)
        else:
            inventory = copy.deepcopy(custom_district_inventory)

        allocation_plan = []
        total_demand_summary = {
            "sdrf_inflatable_boats": 0,
            "ndrf_motor_boats": 0,
            "medical_teams": 0,
            "food_ration_kits": 0,
            "water_purification_kits": 0
        }
        total_allocated_summary = {
            "sdrf_inflatable_boats": 0,
            "ndrf_motor_boats": 0,
            "medical_teams": 0,
            "food_ration_kits": 0,
            "water_purification_kits": 0
        }

        # Process villages down the priority rank
        for village in ranked_villages_with_profile:
            district = village.get("district", "Majuli")
            dist_inv = inventory.get(district, {
                "sdrf_inflatable_boats": 10,
                "ndrf_motor_boats": 5,
                "medical_teams": 6,
                "food_ration_kits": 2000,
                "water_purification_kits": 1600
            })

            demand = self.calculate_village_demand(village)
            allocated = {}
            unmet = {}

            for res_key, req_qty in demand.items():
                total_demand_summary[res_key] += req_qty
                available_qty = dist_inv.get(res_key, 0)
                granted = min(req_qty, available_qty)

                allocated[res_key] = granted
                unmet[res_key] = req_qty - granted
                dist_inv[res_key] = available_qty - granted
                total_allocated_summary[res_key] += granted

            # Determine fulfillment status
            is_full = all(unmet[k] == 0 for k in unmet)
            is_zero = all(allocated[k] == 0 for k in allocated)

            if village.get("estimated_flood_depth_m", 0) <= 0.05:
                dispatch_status = "MONITORING_STANDBY"
                status_color = "#10b981"
            elif is_full:
                dispatch_status = "DISPATCHED_EN_ROUTE"
                status_color = "#10b981"
            elif not is_zero:
                dispatch_status = "PARTIAL_DISPATCH_RESTOCK_QUEUED"
                status_color = "#f59e0b"
            else:
                dispatch_status = "PENDING_DISTRICT_RESERVE_DEPLETED"
                status_color = "#ef4444"

            # Recommended Kit Combination
            access_mode = village.get("access_profile", {}).get("access_mode", "ROAD_CONNECTED")
            if access_mode in ["BOAT_ONLY", "HELI_ONLY"]:
                kit_package_type = "TYPE_A_AFLOAT: Inflatable/Power Boat + Medical Trauma + Water Jerrycans + Dry Rations"
            else:
                kit_package_type = "TYPE_B_TERRESTRIAL: Road Relief Van + Mobile Health Unit + Bulk Rations"

            allocation_plan.append({
                "rank": village.get("rank", 1),
                "village_id": village["village_id"],
                "village_name": village["village_name"],
                "district": district,
                "risk_score": village.get("final_risk_score", 0.0),
                "risk_tier": village.get("risk_tier", "LOW_MONITORING_P4"),
                "estimated_flood_depth_m": village.get("estimated_flood_depth_m", 0.0),
                "access_mode": access_mode,
                "transit_vehicle": village.get("access_profile", {}).get("recommended_craft", "Relief Boat"),
                "kit_package_type": kit_package_type,
                "demand": demand,
                "allocated": allocated,
                "unmet_shortfall": unmet,
                "dispatch_status": dispatch_status,
                "status_color": status_color,
                "staging_hub": village.get("nearest_camp_name", "District Staging Ground"),
                "coordinates": [village.get("latitude", 26.2), village.get("longitude", 92.9)]
            })

        # Calculate fulfillment percentage
        fulfillment_pct = {}
        for k in total_demand_summary:
            dem = total_demand_summary[k]
            alloc = total_allocated_summary[k]
            fulfillment_pct[k] = round((alloc / dem * 100.0) if dem > 0 else 100.0, 1)

        return {
            "dispatch_plan": allocation_plan,
            "district_remaining_inventory": inventory,
            "aggregate_metrics": {
                "total_demand": total_demand_summary,
                "total_allocated": total_allocated_summary,
                "fulfillment_percentages": fulfillment_pct,
                "total_villages_served": len([p for p in allocation_plan if p["dispatch_status"] == "DISPATCHED_EN_ROUTE"]),
                "total_villages_partial": len([p for p in allocation_plan if p["dispatch_status"] == "PARTIAL_DISPATCH_RESTOCK_QUEUED"]),
                "total_villages_depleted": len([p for p in allocation_plan if p["dispatch_status"] == "PENDING_DISTRICT_RESERVE_DEPLETED"])
            }
        }

def np_ceil(val: float) -> int:
    import math
    return int(math.ceil(val))
