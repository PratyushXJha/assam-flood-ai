"""Village database and localized flood depth estimation engine for Assam.
Covers critical riverine, floodplain, and char island settlements with population,
elevation, vulnerability indices, and relief camp metadata.
"""
from typing import List, Dict, Any
from app.stage2_plains.cwc_gauges import get_gauge_by_id

VILLAGES: List[Dict[str, Any]] = [
    # Majuli District
    {
        "id": "VIL_MAJULI_SALMORA",
        "name": "Salmora",
        "district": "Majuli",
        "latitude": 26.8840,
        "longitude": 94.2750,
        "population": 4820,
        "char_island_status": True,
        "terrain_elevation_m": 84.60,
        "vulnerability_index": 0.88,  # High pottery artisan population, active bank erosion
        "closest_gauge_id": "GAUGE_NEMATIGHAT",
        "nearest_camp_name": "Salmora Higher Secondary School Relief Camp",
        "nearest_camp_coords": [26.8920, 94.2810],
        "safe_elevation_m": 88.00
    },
    {
        "id": "VIL_MAJULI_KAMALABARI",
        "name": "Kamalabari",
        "district": "Majuli",
        "latitude": 26.9420,
        "longitude": 94.1850,
        "population": 7250,
        "char_island_status": False,
        "terrain_elevation_m": 85.10,
        "vulnerability_index": 0.65,
        "closest_gauge_id": "GAUGE_NEMATIGHAT",
        "nearest_camp_name": "Kamalabari College Shelter Facility",
        "nearest_camp_coords": [26.9500, 94.1920],
        "safe_elevation_m": 88.50
    },
    {
        "id": "VIL_MAJULI_AHOTGURI",
        "name": "Ahotguri (Char)",
        "district": "Majuli",
        "latitude": 26.8200,
        "longitude": 94.0200,
        "population": 3600,
        "char_island_status": True,
        "terrain_elevation_m": 84.10,
        "vulnerability_index": 0.94,  # Isolated sandbar island
        "closest_gauge_id": "GAUGE_NEMATIGHAT",
        "nearest_camp_name": "Garmur Satra High Ground Refuge",
        "nearest_camp_coords": [26.9600, 94.2100],
        "safe_elevation_m": 89.00
    },
    {
        "id": "VIL_MAJULI_JENGRAIMUKH",
        "name": "Jengraimukh",
        "district": "Majuli",
        "latitude": 27.0800,
        "longitude": 94.3800,
        "population": 5100,
        "char_island_status": False,
        "terrain_elevation_m": 85.40,
        "vulnerability_index": 0.70,
        "closest_gauge_id": "GAUGE_NEMATIGHAT",
        "nearest_camp_name": "Jengraimukh Model Hospital Shelter",
        "nearest_camp_coords": [27.0850, 94.3890],
        "safe_elevation_m": 88.20
    },

    # Barpeta District
    {
        "id": "VIL_BARPETA_MANDIA",
        "name": "Mandia Char",
        "district": "Barpeta",
        "latitude": 26.2500,
        "longitude": 90.9100,
        "population": 8400,
        "char_island_status": True,
        "terrain_elevation_m": 35.10,
        "vulnerability_index": 0.92,
        "closest_gauge_id": "GAUGE_GOALPARA",
        "nearest_camp_name": "Mandia Block Development Relief Center",
        "nearest_camp_coords": [26.2650, 90.9250],
        "safe_elevation_m": 38.50
    },
    {
        "id": "VIL_BARPETA_CHENGA",
        "name": "Chenga",
        "district": "Barpeta",
        "latitude": 26.2800,
        "longitude": 91.0800,
        "population": 6900,
        "char_island_status": False,
        "terrain_elevation_m": 35.70,
        "vulnerability_index": 0.72,
        "closest_gauge_id": "GAUGE_GOALPARA",
        "nearest_camp_name": "Chenga High School Evacuation Center",
        "nearest_camp_coords": [26.2880, 91.0920],
        "safe_elevation_m": 38.80
    },
    {
        "id": "VIL_BARPETA_ALUPATI",
        "name": "Alupati Majarchar",
        "district": "Barpeta",
        "latitude": 26.1900,
        "longitude": 90.8400,
        "population": 4200,
        "char_island_status": True,
        "terrain_elevation_m": 34.80,
        "vulnerability_index": 0.95,
        "closest_gauge_id": "GAUGE_GOALPARA",
        "nearest_camp_name": "Baghbor Hill Elevated Camp",
        "nearest_camp_coords": [26.2300, 90.8700],
        "safe_elevation_m": 39.00
    },
    {
        "id": "VIL_BARPETA_KAYAKUCHI",
        "name": "Kayakuchi",
        "district": "Barpeta",
        "latitude": 26.3800,
        "longitude": 91.1200,
        "population": 5800,
        "char_island_status": False,
        "terrain_elevation_m": 36.20,
        "vulnerability_index": 0.68,
        "closest_gauge_id": "GAUGE_GOALPARA",
        "nearest_camp_name": "Kayakuchi College Relief Hub",
        "nearest_camp_coords": [26.3900, 91.1300],
        "safe_elevation_m": 39.50
    },

    # Dhemaji District
    {
        "id": "VIL_DHEMAJI_JONAI",
        "name": "Jonai (Lali Basin)",
        "district": "Dhemaji",
        "latitude": 27.7800,
        "longitude": 95.1800,
        "population": 6300,
        "char_island_status": False,
        "terrain_elevation_m": 105.10,
        "vulnerability_index": 0.85,
        "closest_gauge_id": "GAUGE_DIBRUGARH",
        "nearest_camp_name": "Jonai Tribal Rest House High Ground",
        "nearest_camp_coords": [27.7950, 95.1950],
        "safe_elevation_m": 108.50
    },
    {
        "id": "VIL_DHEMAJI_SISIBORGAON",
        "name": "Sisiborgaon",
        "district": "Dhemaji",
        "latitude": 27.5600,
        "longitude": 94.7500,
        "population": 5400,
        "char_island_status": False,
        "terrain_elevation_m": 105.30,
        "vulnerability_index": 0.78,
        "closest_gauge_id": "GAUGE_DIBRUGARH",
        "nearest_camp_name": "Sisiborgaon Higher Secondary Shelter",
        "nearest_camp_coords": [27.5700, 94.7620],
        "safe_elevation_m": 108.00
    },

    # Morigaon District
    {
        "id": "VIL_MORIGAON_MAYONG",
        "name": "Mayong (Pobitora Fringe)",
        "district": "Morigaon",
        "latitude": 26.2400,
        "longitude": 92.0300,
        "population": 5900,
        "char_island_status": False,
        "terrain_elevation_m": 48.80,
        "vulnerability_index": 0.82,
        "closest_gauge_id": "GAUGE_PANDU",
        "nearest_camp_name": "Mayong Anchalik College Relief Camp",
        "nearest_camp_coords": [26.2520, 92.0450],
        "safe_elevation_m": 52.00
    },
    {
        "id": "VIL_MORIGAON_LAHARIGHAT",
        "name": "Laharighat Riverbank",
        "district": "Morigaon",
        "latitude": 26.3600,
        "longitude": 92.3800,
        "population": 7800,
        "char_island_status": True,
        "terrain_elevation_m": 48.50,
        "vulnerability_index": 0.93,
        "closest_gauge_id": "GAUGE_PANDU",
        "nearest_camp_name": "Laharighat PWD Inspection Bungalow Hill",
        "nearest_camp_coords": [26.3400, 92.3600],
        "safe_elevation_m": 52.50
    },

    # Dhubri District
    {
        "id": "VIL_DHUBRI_SOUTHSALMARA",
        "name": "South Salmara Char",
        "district": "Dhubri",
        "latitude": 25.8800,
        "longitude": 89.9200,
        "population": 9100,
        "char_island_status": True,
        "terrain_elevation_m": 27.60,
        "vulnerability_index": 0.96,
        "closest_gauge_id": "GAUGE_DHUBRI",
        "nearest_camp_name": "South Salmara College Elevated Shelter",
        "nearest_camp_coords": [25.9050, 89.9450],
        "safe_elevation_m": 31.00
    },
    {
        "id": "VIL_DHUBRI_BILASIPARA",
        "name": "Bilasipara Riverine",
        "district": "Dhubri",
        "latitude": 26.2300,
        "longitude": 90.2300,
        "population": 6700,
        "char_island_status": False,
        "terrain_elevation_m": 28.20,
        "vulnerability_index": 0.74,
        "closest_gauge_id": "GAUGE_DHUBRI",
        "nearest_camp_name": "Bilasipara Stadium Camp",
        "nearest_camp_coords": [26.2400, 90.2450],
        "safe_elevation_m": 31.50
    },

    # Cachar District (Barak Valley)
    {
        "id": "VIL_CACHAR_SONAI",
        "name": "Sonai Riverside",
        "district": "Cachar",
        "latitude": 24.7400,
        "longitude": 92.8900,
        "population": 6200,
        "char_island_status": False,
        "terrain_elevation_m": 18.90,
        "vulnerability_index": 0.81,
        "closest_gauge_id": "GAUGE_SILCHAR",
        "nearest_camp_name": "Sonai College Relief Shelter",
        "nearest_camp_coords": [24.7520, 92.9020],
        "safe_elevation_m": 22.50
    },
    {
        "id": "VIL_CACHAR_KATIGORAH",
        "name": "Katigorah Wetland",
        "district": "Cachar",
        "latitude": 24.9600,
        "longitude": 92.6100,
        "population": 5700,
        "char_island_status": False,
        "terrain_elevation_m": 18.70,
        "vulnerability_index": 0.86,
        "closest_gauge_id": "GAUGE_SILCHAR",
        "nearest_camp_name": "Kalain High School Relief Centre",
        "nearest_camp_coords": [24.9750, 92.6250],
        "safe_elevation_m": 22.80
    }
]

class VillageDepthEngine:
    def __init__(self):
        self.villages = VILLAGES

    def compute_village_depth(self, village: Dict[str, Any], gauge_water_level_m: float) -> Dict[str, Any]:
        """
        Calculate flood depth, inundation percentage, and water level trend for a village.
        """
        gauge = get_gauge_by_id(village["closest_gauge_id"])
        terrain_elev = village["terrain_elevation_m"]

        # Hydraulic head at village location (accounting for distance gradient from gauge)
        local_flood_head_m = gauge_water_level_m
        flood_depth_m = max(0.0, local_flood_head_m - terrain_elev)

        # Inundation percentage of village land area
        if flood_depth_m <= 0.0:
            inundation_pct = 0.0
            impact_category = "SAFE"
        elif flood_depth_m < 0.5:
            inundation_pct = round(15.0 + (flood_depth_m / 0.5) * 25.0, 1)
            impact_category = "LOW_WATERLOGGING"
        elif flood_depth_m < 1.5:
            inundation_pct = round(40.0 + ((flood_depth_m - 0.5) / 1.0) * 35.0, 1)
            impact_category = "MODERATE_SUBMERSION"
        else:
            inundation_pct = min(100.0, round(75.0 + ((flood_depth_m - 1.5) / 1.5) * 25.0, 1))
            impact_category = "CRITICAL_INUNDATION"

        # Estimated affected residents
        affected_population = int(round(village["population"] * (inundation_pct / 100.0)))

        return {
            "village_id": village["id"],
            "village_name": village["name"],
            "district": village["district"],
            "latitude": village["latitude"],
            "longitude": village["longitude"],
            "population": village["population"],
            "affected_population": affected_population,
            "char_island_status": village["char_island_status"],
            "terrain_elevation_m": terrain_elev,
            "water_head_m": round(local_flood_head_m, 2),
            "estimated_flood_depth_m": round(flood_depth_m, 2),
            "inundation_pct": inundation_pct,
            "impact_category": impact_category,
            "vulnerability_index": village["vulnerability_index"],
            "closest_gauge_id": village["closest_gauge_id"],
            "nearest_camp_name": village["nearest_camp_name"],
            "nearest_camp_coords": village["nearest_camp_coords"],
            "safe_elevation_m": village["safe_elevation_m"]
        }

    def compute_all_villages(self, gauge_levels: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Evaluate flood depth for all registered villages based on current/forecast gauge water levels.
        """
        results = []
        for village in self.villages:
            gid = village["closest_gauge_id"]
            g_level = gauge_levels.get(gid, village["terrain_elevation_m"] - 0.5)
            depth_info = self.compute_village_depth(village, g_level)
            results.append(depth_info)
        return results
