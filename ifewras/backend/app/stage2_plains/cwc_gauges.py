"""Central Water Commission (CWC) River Gauges along Brahmaputra and Barak basins.
Accurately configured with real datum levels, Warning Levels, Danger Levels, and Highest Flood Levels (HFL).
"""
from typing import List, Dict, Any

CWC_GAUGES: List[Dict[str, Any]] = [
    {
        "id": "GAUGE_DIBRUGARH",
        "name": "Brahmaputra at Dibrugarh",
        "river": "Brahmaputra",
        "district": "Dibrugarh",
        "latitude": 27.4850,
        "longitude": 94.9120,
        "zero_datum_m": 0.0,
        "warning_level_m": 104.24,
        "danger_level_m": 105.70,
        "highest_flood_level_m": 106.48,
        "upstream_catchments": ["CATCH_SIANG", "CATCH_LOHIT_DIBANG"],
        "normal_monsoon_level_m": 103.50,
        "description": "Upper reach entry gauge, first to record surges from Arunachal Siang & Lohit basins."
    },
    {
        "id": "GAUGE_NEMATIGHAT",
        "name": "Brahmaputra at Nematighat (Jorhat/Majuli)",
        "river": "Brahmaputra",
        "district": "Jorhat / Majuli",
        "latitude": 26.8580,
        "longitude": 94.2250,
        "zero_datum_m": 0.0,
        "warning_level_m": 84.04,
        "danger_level_m": 85.04,
        "highest_flood_level_m": 87.37,
        "upstream_catchments": ["CATCH_SIANG", "CATCH_SUBANSIRI"],
        "normal_monsoon_level_m": 83.20,
        "description": "Critical monitoring station for Majuli river island and Jorhat ferry connectivity."
    },
    {
        "id": "GAUGE_TEZPUR",
        "name": "Brahmaputra at Tezpur",
        "river": "Brahmaputra",
        "district": "Sonitpur",
        "latitude": 26.6200,
        "longitude": 92.7900,
        "zero_datum_m": 0.0,
        "warning_level_m": 64.23,
        "danger_level_m": 65.23,
        "highest_flood_level_m": 66.19,
        "upstream_catchments": ["CATCH_JIABHARALI", "CATCH_SUBANSIRI"],
        "normal_monsoon_level_m": 63.40,
        "description": "Central Assam trunk gauge downstream of Jia Bharali confluence."
    },
    {
        "id": "GAUGE_PANDU",
        "name": "Brahmaputra at Pandu (Guwahati)",
        "river": "Brahmaputra",
        "district": "Kamrup Metropolitan",
        "latitude": 26.1780,
        "longitude": 91.6890,
        "zero_datum_m": 0.0,
        "warning_level_m": 48.68,
        "danger_level_m": 49.68,
        "highest_flood_level_m": 51.46,
        "upstream_catchments": ["CATCH_KOPILI_MEGHALAYA", "CATCH_JIABHARALI"],
        "normal_monsoon_level_m": 47.80,
        "description": "Strategic bottleneck gauge monitoring Guwahati metropolitan area and Saraighat channel."
    },
    {
        "id": "GAUGE_GOALPARA",
        "name": "Brahmaputra at Goalpara",
        "river": "Brahmaputra",
        "district": "Goalpara",
        "latitude": 26.1800,
        "longitude": 90.6200,
        "zero_datum_m": 0.0,
        "warning_level_m": 35.27,
        "danger_level_m": 36.27,
        "highest_flood_level_m": 37.43,
        "upstream_catchments": ["CATCH_MANAS_BEKI", "CATCH_KOPILI_MEGHALAYA"],
        "normal_monsoon_level_m": 34.40,
        "description": "Lower Assam gauge monitoring confluence with Manas river."
    },
    {
        "id": "GAUGE_DHUBRI",
        "name": "Brahmaputra at Dhubri",
        "river": "Brahmaputra",
        "district": "Dhubri",
        "latitude": 26.0200,
        "longitude": 89.9800,
        "zero_datum_m": 0.0,
        "warning_level_m": 27.62,
        "danger_level_m": 28.62,
        "highest_flood_level_m": 30.52,
        "upstream_catchments": ["CATCH_MANAS_BEKI"],
        "normal_monsoon_level_m": 26.80,
        "description": "Exit terminal gauge near India-Bangladesh border, subject to prolonged backwater pooling."
    },
    {
        "id": "GAUGE_SILCHAR",
        "name": "Barak at Silchar (Annapurna Ghat)",
        "river": "Barak",
        "district": "Cachar",
        "latitude": 24.8300,
        "longitude": 92.8000,
        "zero_datum_m": 0.0,
        "warning_level_m": 18.83,
        "danger_level_m": 19.83,
        "highest_flood_level_m": 21.98,
        "upstream_catchments": ["CATCH_BARAK_HEADWATERS"],
        "normal_monsoon_level_m": 17.50,
        "description": "Barak Valley key gauge, vulnerable to catastrophic urban and embankment breaches."
    }
]

def get_gauge_by_id(gauge_id: str) -> Dict[str, Any]:
    """Retrieve CWC gauge metadata by ID."""
    for g in CWC_GAUGES:
        if g["id"] == gauge_id:
            return g
    raise ValueError(f"Gauge ID not found: {gauge_id}")

def get_all_gauges() -> List[Dict[str, Any]]:
    """Return all CWC gauge stations."""
    return CWC_GAUGES
