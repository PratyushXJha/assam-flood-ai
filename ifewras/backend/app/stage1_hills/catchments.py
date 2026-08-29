"""Catchment definitions for upstream hill basins surrounding Assam.
Covers Arunachal Pradesh foothills, Meghalaya Plateau edge, Bhutan border, and Karbi Anglong.
"""
from typing import List, Dict, Any

CATCHMENTS: List[Dict[str, Any]] = [
    {
        "id": "CATCH_SIANG",
        "name": "Siang / Upper Brahmaputra Basin",
        "region": "Arunachal Pradesh (Upper & East Siang)",
        "area_sq_km": 14200,
        "elevation_range_m": [450, 4200],
        "drainage_direction": "South-West into Assam Plains (Pasighat to Dhemaji)",
        "downstream_districts": ["Dhemaji", "Dibrugarh", "Majuli", "Lakhimpur"],
        "downstream_gauges": ["GAUGE_DIBRUGARH", "GAUGE_NEMATIGHAT"],
        "lag_time_hours": 4.5,
        "base_flow_cumec": 5200,
        "runoff_coefficient": 0.82,  # Steep rocky topography
        "center_coords": [28.05, 95.30],
        "polygon_coords": [
            [94.80, 28.50], [95.80, 28.60], [96.00, 27.90],
            [95.40, 27.60], [94.70, 27.90], [94.80, 28.50]
        ]
    },
    {
        "id": "CATCH_SUBANSIRI",
        "name": "Subansiri Gorge & Foothills",
        "region": "Arunachal Pradesh (Lower Subansiri / Kamle)",
        "area_sq_km": 11800,
        "elevation_range_m": [300, 3600],
        "drainage_direction": "South into Lakhimpur & Northern Majuli",
        "downstream_districts": ["Lakhimpur", "Dhemaji", "Majuli"],
        "downstream_gauges": ["GAUGE_NEMATIGHAT"],
        "lag_time_hours": 3.8,
        "base_flow_cumec": 3800,
        "runoff_coefficient": 0.85,
        "center_coords": [27.75, 94.20],
        "polygon_coords": [
            [93.80, 28.10], [94.70, 28.10], [94.60, 27.35],
            [93.90, 27.25], [93.60, 27.70], [93.80, 28.10]
        ]
    },
    {
        "id": "CATCH_LOHIT_DIBANG",
        "name": "Lohit & Dibang Catchment",
        "region": "Eastern Arunachal / Mishmi Hills",
        "area_sq_km": 13400,
        "elevation_range_m": [350, 4800],
        "drainage_direction": "West into Sadiya and Upper Brahmaputra confluence",
        "downstream_districts": ["Tinsukia", "Dibrugarh"],
        "downstream_gauges": ["GAUGE_DIBRUGARH"],
        "lag_time_hours": 5.0,
        "base_flow_cumec": 4100,
        "runoff_coefficient": 0.80,
        "center_coords": [27.90, 96.15],
        "polygon_coords": [
            [95.60, 28.40], [96.60, 28.30], [96.70, 27.50],
            [95.80, 27.40], [95.60, 28.40]
        ]
    },
    {
        "id": "CATCH_JIABHARALI",
        "name": "Jia Bharali / Kameng Basin",
        "region": "West Kameng / Bhutan Border",
        "area_sq_km": 9600,
        "elevation_range_m": [250, 3900],
        "drainage_direction": "South into Tezpur & Sonitpur plain",
        "downstream_districts": ["Sonitpur", "Biswanath"],
        "downstream_gauges": ["GAUGE_TEZPUR"],
        "lag_time_hours": 3.5,
        "base_flow_cumec": 2400,
        "runoff_coefficient": 0.78,
        "center_coords": [27.30, 92.80],
        "polygon_coords": [
            [92.30, 27.80], [93.30, 27.80], [93.10, 26.80],
            [92.40, 26.75], [92.30, 27.80]
        ]
    },
    {
        "id": "CATCH_KOPILI_MEGHALAYA",
        "name": "Kopili & Meghalaya Escarpment",
        "region": "East Khasi Hills & Jaintia Hills / Karbi Anglong",
        "area_sq_km": 8900,
        "elevation_range_m": [150, 1950],
        "drainage_direction": "North-East into Morigaon & Nagaon wetlands",
        "downstream_districts": ["Morigaon", "Nagaon", "Kamrup Metro"],
        "downstream_gauges": ["GAUGE_PANDU"],
        "lag_time_hours": 3.0,
        "base_flow_cumec": 1950,
        "runoff_coefficient": 0.88,  # High intensity rainfall zone (Cherrapunji/Mawsynram fringe)
        "center_coords": [25.75, 92.40],
        "polygon_coords": [
            [91.80, 26.00], [92.90, 26.10], [93.00, 25.30],
            [92.00, 25.20], [91.80, 26.00]
        ]
    },
    {
        "id": "CATCH_MANAS_BEKI",
        "name": "Manas-Beki & Bhutan Foothills",
        "region": "Southern Bhutan / Baksa / Chirang Hills",
        "area_sq_km": 10500,
        "elevation_range_m": [120, 3100],
        "drainage_direction": "South into Barpeta & Lower Assam chars",
        "downstream_districts": ["Barpeta", "Baksa", "Bongaigaon"],
        "downstream_gauges": ["GAUGE_GOALPARA", "GAUGE_DHUBRI"],
        "lag_time_hours": 4.0,
        "base_flow_cumec": 2700,
        "runoff_coefficient": 0.84,
        "center_coords": [26.80, 91.00],
        "polygon_coords": [
            [90.40, 27.20], [91.50, 27.20], [91.40, 26.35],
            [90.50, 26.30], [90.40, 27.20]
        ]
    },
    {
        "id": "CATCH_BARAK_HEADWATERS",
        "name": "Barak Headwaters & Manipur Hills",
        "region": "Manipur / Dima Hasao / Cachar Hills",
        "area_sq_km": 9200,
        "elevation_range_m": [100, 2400],
        "drainage_direction": "West into Barak Valley (Silchar)",
        "downstream_districts": ["Cachar", "Hailakandi", "Karimganj"],
        "downstream_gauges": ["GAUGE_SILCHAR"],
        "lag_time_hours": 4.2,
        "base_flow_cumec": 1800,
        "runoff_coefficient": 0.81,
        "center_coords": [25.00, 93.30],
        "polygon_coords": [
            [92.80, 25.50], [93.80, 25.50], [93.70, 24.50],
            [92.70, 24.60], [92.80, 25.50]
        ]
    }
]

def get_catchment_by_id(catchment_id: str) -> Dict[str, Any]:
    """Retrieve catchment metadata by ID."""
    for c in CATCHMENTS:
        if c["id"] == catchment_id:
            return c
    raise ValueError(f"Catchment ID not found: {catchment_id}")

def get_all_catchments() -> List[Dict[str, Any]]:
    """Return all defined catchments."""
    return CATCHMENTS
