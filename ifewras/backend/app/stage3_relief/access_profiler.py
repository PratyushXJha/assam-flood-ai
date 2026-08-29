"""Access Profiling Engine for Stage 3.
Evaluates physical terrain connectivity, char island isolation, and submerged road links
to determine transit modality (Road / Boat / Helicopter) and vehicle recommendations.
"""
from typing import Dict, Any, List

class AccessProfiler:
    def evaluate_village_access(
        self,
        village_scored: Dict[str, Any],
        road_status_list: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Determine operational transit profile for a village.
        """
        is_char = village_scored.get("char_island_status", False)
        depth_m = village_scored.get("estimated_flood_depth_m", 0.0)
        district = village_scored.get("district", "")

        # Check if relevant district roads are impassable
        has_submerged_road = False
        if road_status_list:
            for r in road_status_list:
                if r["district"] == district and r["status"] == "SUBMERGED_IMPASSABLE":
                    has_submerged_road = True
                    break

        # Categorization logic
        if depth_m >= 2.8:
            access_mode = "HELI_ONLY"
            recommended_craft = "IAF / NDRF ALH-Dhruv or Mi-17 Airdrop"
            transit_notes = "Ghats inundated, high channel debris; direct airdrop of dry rations & liferafts."
            estimated_transit_mins = 25
            is_boat_accessible = False
            is_road_accessible = False
        elif is_char or has_submerged_road or depth_m >= 0.5:
            access_mode = "BOAT_ONLY"
            if is_char or depth_m >= 1.5:
                recommended_craft = "NDRF 40HP Motorized Fiberglass Rescue Boat"
                estimated_transit_mins = 45
            else:
                recommended_craft = "SDRF Inflatable Rubber Boat (IRB) / Country Boat"
                estimated_transit_mins = 35
            transit_notes = "Approach via Baghbar/Nematighat staging ghat with lifejackets and outboard motors."
            is_boat_accessible = True
            is_road_accessible = False
        elif depth_m > 0.15:
            access_mode = "RESTRICTED_ROAD_TRUCK"
            recommended_craft = "High-Clearance 4x4 Rescue Truck / Emergency Tractor"
            transit_notes = "Road waterlogged up to 20cm; accessible via heavy vehicles only."
            estimated_transit_mins = 20
            is_boat_accessible = False
            is_road_accessible = True
        else:
            access_mode = "ROAD_CONNECTED"
            recommended_craft = "Standard ASDMA Relief Vans & Ambulances"
            transit_notes = "Road corridor clear and fully operational."
            estimated_transit_mins = 15
            is_boat_accessible = False
            is_road_accessible = True

        return {
            "village_id": village_scored["village_id"],
            "village_name": village_scored["village_name"],
            "district": district,
            "access_mode": access_mode,
            "recommended_craft": recommended_craft,
            "transit_notes": transit_notes,
            "estimated_transit_mins": estimated_transit_mins,
            "is_boat_accessible": is_boat_accessible,
            "is_road_accessible": is_road_accessible
        }

    def profile_all_villages(
        self,
        ranked_villages: List[Dict[str, Any]],
        road_status_list: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluate access profile for all ranked villages.
        """
        results = []
        for v in ranked_villages:
            prof = self.evaluate_village_access(v, road_status_list)
            # Merge profile with village record
            merged = {**v, "access_profile": prof}
            results.append(merged)
        return results
