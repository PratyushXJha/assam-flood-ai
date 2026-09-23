"""Configuration and constants for FloodCast AI.
AI flood early warning, forecasting and rescue allocation for Assam.
"""
import os
from typing import Dict, Any

APP_NAME = "FloodCast AI"
APP_VERSION = "2.0.0"

# Geographic bounding box for Assam & Upstream Hill Catchments
GEO_BOUNDS = {
    "min_lat": 24.0,
    "max_lat": 28.5,
    "min_lon": 89.5,
    "max_lon": 96.5,
    "center_lat": 26.2006,
    "center_lon": 92.9376,
}

# Stage 1 Rainfall Intensity Thresholds (mm/hr & accumulated mm)
STAGE1_THRESHOLDS = {
    "flash_flood_rate_mm_hr": 25.0,        # > 25 mm/hr in steep terrain triggers immediate runoff
    "accum_6h_trigger_mm": 65.0,           # 6-hr accumulated rainfall threshold
    "accum_24h_trigger_mm": 130.0,         # 24-hr accumulated rainfall threshold
    "soil_saturation_critical_pct": 75.0,  # Saturation > 75% magnifies runoff by up to 1.6x
}

# Stage 2 Forecast Lead Times (in hours)
FORECAST_LEAD_TIMES = [24, 48, 72]

# Default District Resource Capacities for Relief Allocation
DEFAULT_DISTRICT_RESOURCES: Dict[str, Dict[str, int]] = {
    "Majuli": {
        "sdrf_inflatable_boats": 12,
        "ndrf_motor_boats": 6,
        "medical_teams": 8,
        "food_ration_kits": 2500,
        "water_purification_kits": 2000,
    },
    "Barpeta": {
        "sdrf_inflatable_boats": 15,
        "ndrf_motor_boats": 8,
        "medical_teams": 10,
        "food_ration_kits": 3500,
        "water_purification_kits": 2800,
    },
    "Dhemaji": {
        "sdrf_inflatable_boats": 10,
        "ndrf_motor_boats": 5,
        "medical_teams": 6,
        "food_ration_kits": 2000,
        "water_purification_kits": 1600,
    },
    "Morigaon": {
        "sdrf_inflatable_boats": 10,
        "ndrf_motor_boats": 4,
        "medical_teams": 7,
        "food_ration_kits": 2200,
        "water_purification_kits": 1800,
    },
    "Dhubri": {
        "sdrf_inflatable_boats": 14,
        "ndrf_motor_boats": 7,
        "medical_teams": 9,
        "food_ration_kits": 3000,
        "water_purification_kits": 2400,
    },
    "Cachar": {
        "sdrf_inflatable_boats": 10,
        "ndrf_motor_boats": 6,
        "medical_teams": 8,
        "food_ration_kits": 2200,
        "water_purification_kits": 1900,
    },
}

# Emergency Helpline Contacts
EMERGENCY_CONTACTS = {
    "state_emergency_operation_center": "1079",
    "district_disaster_helpline": "1077",
    "national_emergency_number": "112",
    "sdrf_control_room": "0361-2237011",
}

# AI voice-call locales. Twilio <Say> has no Assamese voice, so Assamese scripts are
# read by the Bengali (bn-IN) voice, which shares the Eastern Nagari script.
VOICE_LOCALES = {
    "english": {"locale": "en-IN", "twilio_language": "en-IN", "twilio_voice": os.getenv("VOICE_EN", "Google.en-IN-Standard-A")},
    "hindi": {"locale": "hi-IN", "twilio_language": "hi-IN", "twilio_voice": os.getenv("VOICE_HI", "Google.hi-IN-Standard-A")},
    "assamese": {"locale": "as-IN", "twilio_language": "bn-IN", "twilio_voice": os.getenv("VOICE_AS", "Google.bn-IN-Standard-A")},
}

# Throttled SMS / voice dispatch. Low, steady send rates keep carriers from
# rate-limiting or blocking the sender ID during a mass alert.
DISPATCH_DEFAULTS = {
    "sms_per_minute": float(os.getenv("SMS_PER_MINUTE", "30")),     # one SMS every 2 s
    "calls_per_minute": float(os.getenv("CALLS_PER_MINUTE", "6")),  # one call every 10 s
    "max_retries": int(os.getenv("DISPATCH_MAX_RETRIES", "3")),
    "retry_backoff_seconds": float(os.getenv("DISPATCH_RETRY_BACKOFF", "15")),
}

# Twilio credentials (optional). Without them messages are simulated (dry run).
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
