"""Road network and transport corridor submersion engine for Stage 2.
Tracks National Highways, State Highways, and village embankment links
to flag impassable cut-offs and emergency detour requirements.
"""
from typing import List, Dict, Any

ROAD_SEGMENTS: List[Dict[str, Any]] = [
    {
        "id": "ROAD_NH715_KAZIRANGA",
        "name": "NH-715 Kaziranga Arterial Corridor (Kohora - Jakhalabandha)",
        "type": "NATIONAL_HIGHWAY",
        "district": "Golaghat / Nagaon",
        "associated_gauge": "GAUGE_TEZPUR",
        "crown_elevation_m": 64.90,
        "criticality": "HIGH_STRATEGIC",
        "coordinates": [
            [93.15, 26.58], [93.35, 26.59], [93.55, 26.60], [93.75, 26.62]
        ],
        "detour_advice": "Reroute via North Bank NH-15 (Tezpur - Biswanath Chariali) when overtopped."
    },
    {
        "id": "ROAD_MAJULI_SPINE",
        "name": "Kamalabari - Garmur Main Island Spine Road",
        "type": "DISTRICT_ROAD",
        "district": "Majuli",
        "associated_gauge": "GAUGE_NEMATIGHAT",
        "crown_elevation_m": 85.30,
        "criticality": "HIGH_ISLAND_LIFELINE",
        "coordinates": [
            [94.18, 26.94], [94.21, 26.96], [94.24, 26.99], [94.28, 27.02]
        ],
        "detour_advice": "Deploy SDRF motorized country boats between Kamalabari and Garmur Satra high grounds."
    },
    {
        "id": "ROAD_BARPETA_MANDIA",
        "name": "SH-46 Barpeta Town to Mandia Char Access Link",
        "type": "STATE_HIGHWAY",
        "district": "Barpeta",
        "associated_gauge": "GAUGE_GOALPARA",
        "crown_elevation_m": 35.80,
        "criticality": "CRITICAL_CHAR_FEEDER",
        "coordinates": [
            [91.00, 26.32], [90.96, 26.29], [90.91, 26.25]
        ],
        "detour_advice": "Road breached at 4th km; access Mandia Char only via SDRF power boats from Baghbar Ghat."
    },
    {
        "id": "ROAD_DHEMAJI_NH15",
        "name": "NH-15 Dhemaji - Jonai Border Corridor",
        "type": "NATIONAL_HIGHWAY",
        "district": "Dhemaji",
        "associated_gauge": "GAUGE_DIBRUGARH",
        "crown_elevation_m": 105.40,
        "criticality": "HIGH_STRATEGIC",
        "coordinates": [
            [94.75, 27.56], [94.95, 27.67], [95.18, 27.78]
        ],
        "detour_advice": "Water overflowing culverts at Sisiborgaon; heavy vehicles only with NDRF escort."
    },
    {
        "id": "ROAD_MORIGAON_MAYONG",
        "name": "Morigaon - Mayong - Pobitora Riverbank Link",
        "type": "DISTRICT_ROAD",
        "district": "Morigaon",
        "associated_gauge": "GAUGE_PANDU",
        "crown_elevation_m": 49.10,
        "criticality": "MEDIUM_LOCAL",
        "coordinates": [
            [92.34, 26.25], [92.18, 26.24], [92.03, 26.24]
        ],
        "detour_advice": "Submerged near Pobitora eco-gate; use Jagiroad - Morigaon bypass."
    },
    {
        "id": "ROAD_DHUBRI_FAKIRGANJ",
        "name": "Dhubri - Fakirganj Embankment Bund Road",
        "type": "EMBANKMENT_ROAD",
        "district": "Dhubri",
        "associated_gauge": "GAUGE_DHUBRI",
        "crown_elevation_m": 28.10,
        "criticality": "HIGH_EMBANKMENT",
        "coordinates": [
            [89.98, 26.02], [90.05, 25.96], [90.15, 25.90]
        ],
        "detour_advice": "Bund washed away at South Salmara junction; zero vehicle transit permitted."
    },
    {
        "id": "ROAD_SILCHAR_KATIGORAH",
        "name": "NH-37 Silchar - Katigorah (Kalain Bridge Link)",
        "type": "NATIONAL_HIGHWAY",
        "district": "Cachar",
        "associated_gauge": "GAUGE_SILCHAR",
        "crown_elevation_m": 19.30,
        "criticality": "HIGH_STRATEGIC",
        "coordinates": [
            [92.80, 24.83], [92.70, 24.90], [92.61, 24.96]
        ],
        "detour_advice": "Bethukandi embankment overflow has flooded Kalain approach; restricted to army heavy vehicles."
    }
]

class RoadSubmersionEngine:
    def __init__(self):
        self.roads = ROAD_SEGMENTS

    def evaluate_road_status(self, road: Dict[str, Any], gauge_water_level_m: float) -> Dict[str, Any]:
        """
        Evaluate road overtopping depth and vehicle transit capability.
        """
        crown_elev = road["crown_elevation_m"]
        overtop_m = max(0.0, gauge_water_level_m - crown_elev)
        water_depth_cm = round(overtop_m * 100.0, 1)

        if water_depth_cm <= 0.0:
            status = "OPERATIONAL"
            passable_light_vehicles = True
            passable_heavy_trucks = True
            color = "#10b981"  # Green
        elif water_depth_cm < 20.0:
            status = "WATERLOGGED_SLOW"
            passable_light_vehicles = True
            passable_heavy_trucks = True
            color = "#f59e0b"  # Amber
        elif water_depth_cm < 50.0:
            status = "RESTRICTED_HEAVY_ONLY"
            passable_light_vehicles = False
            passable_heavy_trucks = True
            color = "#ea580c"  # Orange
        else:
            status = "SUBMERGED_IMPASSABLE"
            passable_light_vehicles = False
            passable_heavy_trucks = False
            color = "#ef4444"  # Red

        return {
            "road_id": road["id"],
            "name": road["name"],
            "type": road["type"],
            "district": road["district"],
            "criticality": road["criticality"],
            "crown_elevation_m": crown_elev,
            "water_level_m": round(gauge_water_level_m, 2),
            "water_depth_cm": water_depth_cm,
            "status": status,
            "status_color": color,
            "passable_light_vehicles": passable_light_vehicles,
            "passable_heavy_trucks": passable_heavy_trucks,
            "coordinates": road["coordinates"],
            "detour_advice": road["detour_advice"]
        }

    def evaluate_all_roads(self, gauge_levels: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Evaluate all monitored road segments against gauge levels.
        """
        results = []
        for road in self.roads:
            gid = road["associated_gauge"]
            g_level = gauge_levels.get(gid, road["crown_elevation_m"] - 0.5)
            status_info = self.evaluate_road_status(road, g_level)
            results.append(status_info)
        return results
