"""Calibrated historical data timeline for Assam Brahmaputra Monsoon Flood Scenario.
Captures the 72-hour cascade from upstream hill cloudbursts to plain inundation.
"""
from typing import List, Dict, Any

SCENARIO_TIMELINE: List[Dict[str, Any]] = [
    {
        "step_index": 0,
        "time_offset_hours": 0,
        "time_label": "T+00h : Upstream Cloudburst & Hill Trigger",
        "phase_name": "UPSTREAM_DETECTION",
        "description": "Intense torrential rainfall detected across Arunachal Pradesh Siang & Subansiri gorges and Meghalaya Escarpment. Rivers in plains currently at normal monsoon baseline.",
        "stage1_telemetry": {
            "CATCH_SIANG": {"rate_mm_hr": 48.5, "accum_6h_mm": 115.0, "accum_24h_mm": 195.0, "soil_moisture_pct": 86.0},
            "CATCH_SUBANSIRI": {"rate_mm_hr": 42.0, "accum_6h_mm": 98.0, "accum_24h_mm": 170.0, "soil_moisture_pct": 82.0},
            "CATCH_LOHIT_DIBANG": {"rate_mm_hr": 34.0, "accum_6h_mm": 80.0, "accum_24h_mm": 140.0, "soil_moisture_pct": 79.0},
            "CATCH_JIABHARALI": {"rate_mm_hr": 22.0, "accum_6h_mm": 52.0, "accum_24h_mm": 95.0, "soil_moisture_pct": 70.0},
            "CATCH_KOPILI_MEGHALAYA": {"rate_mm_hr": 55.0, "accum_6h_mm": 130.0, "accum_24h_mm": 220.0, "soil_moisture_pct": 92.0},
            "CATCH_MANAS_BEKI": {"rate_mm_hr": 16.0, "accum_6h_mm": 38.0, "accum_24h_mm": 70.0, "soil_moisture_pct": 65.0},
            "CATCH_BARAK_HEADWATERS": {"rate_mm_hr": 18.0, "accum_6h_mm": 42.0, "accum_24h_mm": 80.0, "soil_moisture_pct": 68.0}
        },
        "stage2_gauge_readings": {
            "GAUGE_DIBRUGARH": 103.80,    # Normal baseline (Warning: 104.24m)
            "GAUGE_NEMATIGHAT": 83.40,   # Normal baseline (Warning: 84.04m)
            "GAUGE_TEZPUR": 63.60,       # Normal baseline (Warning: 64.23m)
            "GAUGE_PANDU": 48.00,        # Normal baseline (Warning: 48.68m)
            "GAUGE_GOALPARA": 34.50,     # Normal baseline (Warning: 35.27m)
            "GAUGE_DHUBRI": 26.90,       # Normal baseline (Warning: 27.62m)
            "GAUGE_SILCHAR": 17.60       # Normal baseline (Warning: 18.83m)
        }
    },
    {
        "step_index": 1,
        "time_offset_hours": 24,
        "time_label": "T+24h : Upper Reach Surge & Early Warning",
        "phase_name": "UPPER_ASSAM_WARNING",
        "description": "Hill runoff reaches Upper Assam plains. Brahmaputra at Dibrugarh and Nematighat (Majuli) crosses Warning Mark. First wave of waterlogging begins in Majuli chars and Dhemaji.",
        "stage1_telemetry": {
            "CATCH_SIANG": {"rate_mm_hr": 28.0, "accum_6h_mm": 75.0, "accum_24h_mm": 210.0, "soil_moisture_pct": 91.0},
            "CATCH_SUBANSIRI": {"rate_mm_hr": 30.0, "accum_6h_mm": 82.0, "accum_24h_mm": 190.0, "soil_moisture_pct": 88.0},
            "CATCH_LOHIT_DIBANG": {"rate_mm_hr": 25.0, "accum_6h_mm": 60.0, "accum_24h_mm": 150.0, "soil_moisture_pct": 83.0},
            "CATCH_JIABHARALI": {"rate_mm_hr": 36.0, "accum_6h_mm": 88.0, "accum_24h_mm": 140.0, "soil_moisture_pct": 78.0},
            "CATCH_KOPILI_MEGHALAYA": {"rate_mm_hr": 38.0, "accum_6h_mm": 95.0, "accum_24h_mm": 235.0, "soil_moisture_pct": 95.0},
            "CATCH_MANAS_BEKI": {"rate_mm_hr": 28.0, "accum_6h_mm": 65.0, "accum_24h_mm": 110.0, "soil_moisture_pct": 75.0},
            "CATCH_BARAK_HEADWATERS": {"rate_mm_hr": 22.0, "accum_6h_mm": 54.0, "accum_24h_mm": 105.0, "soil_moisture_pct": 72.0}
        },
        "stage2_gauge_readings": {
            "GAUGE_DIBRUGARH": 104.95,   # Above Warning (104.24m), approaching Danger (105.70m)
            "GAUGE_NEMATIGHAT": 84.70,  # Above Warning (84.04m), approaching Danger (85.04m)
            "GAUGE_TEZPUR": 64.40,      # Crossing Warning (64.23m)
            "GAUGE_PANDU": 48.80,       # Crossing Warning (48.68m)
            "GAUGE_GOALPARA": 34.90,    # Rising towards Warning
            "GAUGE_DHUBRI": 27.20,      # Steady rise
            "GAUGE_SILCHAR": 18.20      # Moderate rise
        }
    },
    {
        "step_index": 2,
        "time_offset_hours": 48,
        "time_label": "T+48h : Peak Flood Stage & Middle Assam Overtopping",
        "phase_name": "PEAK_INUNDATION_CRISIS",
        "description": "Massive flood wave surges through Central Assam. Nematighat and Tezpur exceed Danger Marks. Majuli island chars and Morigaon wetlands experience severe submergence. P1 rescue boat dispatch initiated.",
        "stage1_telemetry": {
            "CATCH_SIANG": {"rate_mm_hr": 14.0, "accum_6h_mm": 40.0, "accum_24h_mm": 160.0, "soil_moisture_pct": 88.0},
            "CATCH_SUBANSIRI": {"rate_mm_hr": 16.0, "accum_6h_mm": 45.0, "accum_24h_mm": 150.0, "soil_moisture_pct": 85.0},
            "CATCH_LOHIT_DIBANG": {"rate_mm_hr": 12.0, "accum_6h_mm": 35.0, "accum_24h_mm": 120.0, "soil_moisture_pct": 80.0},
            "CATCH_JIABHARALI": {"rate_mm_hr": 20.0, "accum_6h_mm": 50.0, "accum_24h_mm": 130.0, "soil_moisture_pct": 82.0},
            "CATCH_KOPILI_MEGHALAYA": {"rate_mm_hr": 24.0, "accum_6h_mm": 60.0, "accum_24h_mm": 180.0, "soil_moisture_pct": 92.0},
            "CATCH_MANAS_BEKI": {"rate_mm_hr": 42.0, "accum_6h_mm": 105.0, "accum_24h_mm": 165.0, "soil_moisture_pct": 86.0},
            "CATCH_BARAK_HEADWATERS": {"rate_mm_hr": 35.0, "accum_6h_mm": 85.0, "accum_24h_mm": 145.0, "soil_moisture_pct": 84.0}
        },
        "stage2_gauge_readings": {
            "GAUGE_DIBRUGARH": 105.85,   # ABOVE DANGER LEVEL (105.70m)
            "GAUGE_NEMATIGHAT": 85.95,  # 0.91m ABOVE DANGER LEVEL (85.04m)
            "GAUGE_TEZPUR": 65.65,      # 0.42m ABOVE DANGER LEVEL (65.23m)
            "GAUGE_PANDU": 49.95,       # 0.27m ABOVE DANGER LEVEL (49.68m)
            "GAUGE_GOALPARA": 35.80,    # Above Warning (35.27m)
            "GAUGE_DHUBRI": 27.95,      # Above Warning (27.62m)
            "GAUGE_SILCHAR": 19.30      # Above Warning (18.83m)
        }
    },
    {
        "step_index": 3,
        "time_offset_hours": 72,
        "time_label": "T+72h : Downstream Backwater Peak & Full Relief Operations",
        "phase_name": "DOWNSTREAM_DISASTER_MANAGEMENT",
        "description": "Surge concentrates in Lower Assam (Barpeta & Dhubri border) while Upper Assam slowly stabilizes. Barpeta Mandia chars and Dhubri South Salmara require maximum SDRF/NDRF boat and airdrop allocations.",
        "stage1_telemetry": {
            "CATCH_SIANG": {"rate_mm_hr": 6.0, "accum_6h_mm": 18.0, "accum_24h_mm": 85.0, "soil_moisture_pct": 80.0},
            "CATCH_SUBANSIRI": {"rate_mm_hr": 8.0, "accum_6h_mm": 22.0, "accum_24h_mm": 90.0, "soil_moisture_pct": 78.0},
            "CATCH_LOHIT_DIBANG": {"rate_mm_hr": 5.0, "accum_6h_mm": 15.0, "accum_24h_mm": 70.0, "soil_moisture_pct": 74.0},
            "CATCH_JIABHARALI": {"rate_mm_hr": 10.0, "accum_6h_mm": 28.0, "accum_24h_mm": 80.0, "soil_moisture_pct": 75.0},
            "CATCH_KOPILI_MEGHALAYA": {"rate_mm_hr": 12.0, "accum_6h_mm": 32.0, "accum_24h_mm": 110.0, "soil_moisture_pct": 85.0},
            "CATCH_MANAS_BEKI": {"rate_mm_hr": 18.0, "accum_6h_mm": 48.0, "accum_24h_mm": 135.0, "soil_moisture_pct": 88.0},
            "CATCH_BARAK_HEADWATERS": {"rate_mm_hr": 40.0, "accum_6h_mm": 102.0, "accum_24h_mm": 185.0, "soil_moisture_pct": 91.0}
        },
        "stage2_gauge_readings": {
            "GAUGE_DIBRUGARH": 105.10,   # Receding slightly below danger
            "GAUGE_NEMATIGHAT": 85.20,  # Slowly receding
            "GAUGE_TEZPUR": 65.10,      # Receding near danger
            "GAUGE_PANDU": 49.80,       # Sustained high above danger
            "GAUGE_GOALPARA": 36.65,    # 0.38m ABOVE DANGER LEVEL (36.27m)
            "GAUGE_DHUBRI": 28.95,      # 0.33m ABOVE DANGER LEVEL (28.62m)
            "GAUGE_SILCHAR": 20.25      # 0.42m ABOVE DANGER LEVEL (19.83m)
        }
    }
]
