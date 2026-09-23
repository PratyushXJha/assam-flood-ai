"""Offline NLP engine for the FloodCast AI assistant.

Used when no Claude API credentials are configured. It classifies the question into an
intent with weighted keyword matching (English, Hindi and Assamese keywords), pulls out
entities (village, district, zone level) with fuzzy matching, then answers from the same
read-only situation tools the Claude assistant uses.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from app.assistant import tools

INTENT_KEYWORDS: Dict[str, List[str]] = {
    "overview": ["status", "situation", "overview", "summary", "summarise", "summarize", "brief", "update",
                 "happening", "report", "current", "now", "sitrep", "स्थिति", "हालात", "सारांश",
                 "অৱস্থা", "পৰিস্থিতি", "খবৰ"],
    "zones": ["zone", "zones", "red", "yellow", "green", "area", "areas", "where", "affected", "hotspot",
              "क्षेत्र", "ইলাকা", "অঞ্চল"],
    "gauges": ["river", "gauge", "gauges", "level", "levels", "water", "danger", "mark", "brahmaputra", "barak",
               "dibrugarh", "nematighat", "tezpur", "pandu", "goalpara", "dhubri", "silchar", "नदी", "जलस्तर",
               "নদী", "পানী"],
    "forecast": ["forecast", "predict", "prediction", "next", "tomorrow", "upcoming", "peak", "will", "expected",
                 "outlook", "24h", "48h", "72h", "पूर्वानुमान", "আগলৈ"],
    "rainfall": ["rain", "rainfall", "hill", "hills", "catchment", "upstream", "cloudburst", "arunachal",
                 "meghalaya", "बारिश", "वर्षा", "বৰষুণ"],
    "relief": ["boat", "boats", "relief", "rescue", "medical", "ration", "rations", "supplies", "resources",
               "inventory", "reserve", "reserves", "ndrf", "sdrf", "shortfall", "राहत", "नाव", "সাহায্য", "নাও"],
    "alerts": ["sms", "alert", "alerts", "message", "messages", "calls", "notify", "dispatch", "dispatched",
               "delivered", "sent", "queue", "संदेश", "বাৰ্তা"],
    "actions": ["recommend", "recommendation", "should", "next step", "next steps", "priority", "priorities",
                "do next", "should we", "what to do", "what now",
                "action", "actions", "todo", "advise", "suggest", "क्या करें", "কি কৰিব"],
    "contacts": ["helpline", "contact", "contacts", "number", "phone", "hotline", "हेल्पलाइन", "সহায়"],
    "safety": ["safety", "safe", "evacuate", "evacuation", "prepare", "precaution", "tips", "kit", "सुरक्षा",
               "সুৰক্ষা"],
    "help": ["help", "hello", "hi", "hey", "what can you", "who are you", "नमस्ते", "নমস্কাৰ"],
}

TIE_ORDER = ["relief", "alerts", "actions", "forecast", "zones", "rainfall", "contacts", "safety",
             "gauges", "overview", "help"]

SUGGESTIONS = [
    "Give me a situation overview",
    "Which zones are red?",
    "What should we do next?",
    "Status of Mandia Char",
    "River levels and forecast",
    "How many alerts have been sent?",
]


def detect_language(text: str) -> str:
    if re.search(r"[ঀ-৿]", text):
        return "assamese"
    if re.search(r"[ऀ-ॿ]", text):
        return "hindi"
    return "english"


def _tokens(text: str) -> List[str]:
    return re.findall(r"[\wऀ-৿]+", text.lower())


def classify(text: str) -> Tuple[str, Dict[str, Any]]:
    """Return (intent, entities)."""
    low = text.lower()
    toks = set(_tokens(text))
    scores = {}
    for intent, words in INTENT_KEYWORDS.items():
        scores[intent] = sum((2 if " " in w else 1) for w in words if (w in toks or (" " in w and w in low)))

    entities: Dict[str, Any] = {}
    state = tools._state()
    village = _find_village(low, tools._village_names(state))
    if village:
        entities["village"] = village
    districts = list(state["stage3"]["allocation"]["district_remaining_inventory"].keys())
    district = next((d for d in districts if d.lower() in low), None)
    if district:
        entities["district"] = district
    for level in ("red", "yellow", "green"):
        if level in toks:
            entities["level"] = level.upper()

    if village and scores["gauges"] < 2 and scores["relief"] == 0:
        return "village", entities
    river_words = {"river", "gauge", "gauges", "level", "levels", "water", "forecast"}
    if district and not (toks & river_words) and max(scores["relief"], scores["alerts"], scores["actions"]) == 0:
        return "district", entities
    # Ties go to the more specific intent (place names alone shouldn't win "gauges")
    best = max(scores, key=lambda k: (scores[k], -TIE_ORDER.index(k)))
    if scores[best] == 0:
        return ("village", entities) if village else ("overview", entities)
    # Forecast questions usually also mention rivers/levels
    if best == "gauges" and scores["forecast"]:
        best = "forecast"
    return best, entities


def _find_village(low: str, names: List[str]) -> Optional[str]:
    for name in names:
        base = name.lower().split(" (")[0]
        if base in low or any(len(part) > 4 and part in low for part in base.split()):
            return name
    return None


# ---------------------------------------------------------------------------
# Answer composers (markdown-lite: **bold** and "- " bullets)
# ---------------------------------------------------------------------------

def _overview() -> str:
    o = tools.get_situation_overview()
    lines = [f"**{o['time']}** ({o['phase']})", o["phase_description"], ""]
    if o["red_zones"]:
        lines.append(f"**{len(o['red_zones'])} red zone(s):** " + ", ".join(
            f"{z['district']} ({z['people_at_risk']:,} at risk)" for z in o["red_zones"]))
    else:
        lines.append("**No red zones** right now.")
    lines += [
        f"- Gauges above danger level: **{o['gauges_above_danger']}**",
        f"- Flooded area: **{o['flooded_area_sq_km']} km²**",
        f"- Extreme-risk (P1) villages: **{o['p1_extreme_risk_villages']}**",
        f"- Rescue boats deployed: **{o['rescue_boats_deployed']}**",
        f"- Alerts: {o['alerts']['sms_sent']} SMS sent ({o['alerts']['sms_waiting']} waiting), "
        f"{o['alerts']['calls_placed']} AI calls placed ({o['alerts']['calls_waiting']} waiting)",
        "", "**Highest-risk villages:**",
    ]
    lines += [f"- {v['village']} ({v['district']}): risk {v['risk_score']}, depth {v['depth_m']} m" for v in o["top_risk_villages"][:3]]
    acts = tools.get_recommended_actions()["actions"][:2]
    lines += ["", "**Next steps:**"] + [f"- {a}" for a in acts]
    return "\n".join(lines)


def _district(name: str) -> str:
    zones = [z for z in tools.get_zones()["zones"] if name.lower() in z["district"].lower()]
    relief = tools.get_relief_status(name)
    lines = [f"**{name} district**"]
    for z in zones:
        lines.append(f"- Zone **{z['level']}**: {z['reason']}" + (f", {z['people_at_risk']:,} people at risk" if z["people_at_risk"] else ""))
        lines += [f"  - {v}" for v in z["villages"]]
    for d in relief["dispatches"]:
        lines.append(f"- Relief to {d['village']}: {d['boats']} boats, {d['medical_teams']} medical · {d['status']}")
    for k, v in relief["reserves_left"].items():
        lines.append(f"- Reserves left: {v['boats']} boats, {v['medical_teams']} medical teams, {v['ration_kits']} ration kits")
    return "\n".join(lines)


def _zones(level: Optional[str]) -> str:
    zones = tools.get_zones(level)["zones"]
    if not zones:
        return f"There are no {level.lower() if level else ''} zones right now."
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2}
    zones.sort(key=lambda z: order[z["level"]])
    lines = []
    for z in zones:
        lines.append(f"- **{z['level']}**: {z['district']}: {z['reason']}"
                     + (f", {z['people_at_risk']:,} people at risk" if z["people_at_risk"] else ""))
    return "**Hazard zones:**\n" + "\n".join(lines)


def _village(name: str) -> str:
    v = tools.get_village(name)
    if "error" in v:
        return v["error"] + " Known villages: " + ", ".join(v["known_villages"])
    relief = v["relief_sent"] or {}
    boats = relief.get("sdrf_inflatable_boats", 0) + relief.get("ndrf_motor_boats", 0)
    return "\n".join([
        f"**{v['village']}** ({v['district']}){' · river char island' if v['river_char_island'] else ''}",
        f"- Risk: **{v['risk_score']}/100** ({v['risk_tier'].replace('_', ' ').title()}), rank #{v['rank']}",
        f"- Flood depth: **{v['flood_depth_m']} m** · Zone: {v['zone'] or 'n/a'}",
        f"- Main driver: {v['main_risk_driver']} · Action: {v['evacuation']}",
        f"- Shelter: {v['shelter']}",
        f"- Access: {v['access_mode'].replace('_', ' ').lower()} ({v['recommended_craft']})",
        f"- Relief: {boats} boat(s), {relief.get('medical_teams', 0)} medical team(s), "
        f"{relief.get('food_ration_kits', 0)} ration kits · {v['relief_status']}",
    ])


def _gauges(forecast: bool) -> str:
    gs = tools.get_river_gauges()["gauges"]
    lines = ["**River gauges" + (" (forecast)" if forecast else "") + ":**"]
    for g in sorted(gs, key=lambda g: -g["above_danger_by_m"]):
        flag = "above danger" if g["above_danger_by_m"] >= 0 else f"{-g['above_danger_by_m']} m below danger"
        if forecast:
            lines.append(f"- {g['gauge']}: now {g['now_m']} m ({flag}); 24h {g['forecast_24h_m']} · 48h {g['forecast_48h_m']} · 72h {g['forecast_72h_m']} m (danger {g['danger_m']} m)")
        else:
            lines.append(f"- {g['gauge']}: **{g['now_m']} m** ({flag}), trend {g['trend_cm_per_hr']:+} cm/h")
    return "\n".join(lines)


def _rainfall() -> str:
    cs = tools.get_hill_rainfall()["catchments"]
    lines = ["**Upstream hill rainfall:**"]
    for c in sorted(cs, key=lambda c: -c["rain_mm_hr"]):
        lines.append(f"- {c['catchment']}: {c['rain_mm_hr']} mm/h, soil {c['soil_saturation_pct']}% → "
                     f"{c['alert'].replace('_', ' ').title()}, reaches plains in ~{c['hours_until_plains']} h")
    return "\n".join(lines)


def _relief(district: Optional[str]) -> str:
    r = tools.get_relief_status(district)
    lines = ["**Relief dispatched:**"]
    for d in r["dispatches"][:8]:
        short = f" (short {d['unmet_boats']} boats)" if d["unmet_boats"] else ""
        lines.append(f"- {d['village']}: {d['boats']} boats, {d['medical_teams']} medical, {d['ration_kits']} rations · {d['status']}{short}")
    if len(lines) == 1:
        lines.append("- No villages need relief yet.")
    lines.append("**Reserves left:** " + "; ".join(f"{k}: {v['boats']} boats, {v['medical_teams']} medical" for k, v in r["reserves_left"].items()))
    return "\n".join(lines)


def _alerts() -> str:
    a = tools.get_alert_dispatch_status()
    return "\n".join([
        f"**Alert delivery** ({a['provider']}):",
        f"- SMS: {a['sms']['sent']} sent, {a['sms']['pending']} waiting, {a['sms']['failed']} failed (rate {a['sms_per_minute']}/min, ~{round(a['sms']['eta_seconds'] / 60)} min to clear)",
        f"- AI voice calls: {a['voice_calls']['sent']} placed, {a['voice_calls']['pending']} waiting, {a['voice_calls']['failed']} failed (rate {a['calls_per_minute']}/min)",
    ])


def _actions() -> str:
    return "**Recommended next steps:**\n" + "\n".join(f"- {a}" for a in tools.get_recommended_actions()["actions"])


def _contacts() -> str:
    h = tools.get_emergency_contacts()["helplines"]
    return ("**Emergency helplines:**\n"
            f"- State Emergency Operations Centre: **{h['state_emergency_operation_center']}**\n"
            f"- District disaster helpline: **{h['district_disaster_helpline']}**\n"
            f"- National emergency: **{h['national_emergency_number']}**\n"
            f"- SDRF control room: {h['sdrf_control_room']}")


def _safety() -> str:
    return ("**Flood safety guidance for residents:**\n"
            "- Move to the designated relief shelter as soon as an evacuation alert arrives; do not wait for water to rise.\n"
            "- Carry documents, medicines, drinking water, a torch and a charged phone in a waterproof bag.\n"
            "- Switch off electricity and gas before leaving. Move livestock to high ground if it is safe.\n"
            "- Never walk or drive through moving water; 15 cm can knock a person down.\n"
            "- Boil or purify drinking water and watch for snakes.\n"
            "- Call 1079 (State EOC) or 112 for rescue.")


def _help() -> str:
    return ("I'm the FloodCast AI assistant. I can tell you:\n"
            "- the overall situation and red zones\n- the status of any village (risk, depth, shelter, relief)\n"
            "- river levels and 72-hour forecasts\n- upstream hill rainfall\n- boats, medical teams and reserves\n"
            "- SMS and voice-call delivery\n- recommended next steps and helpline numbers")


LOCAL_HEADLINES = {
    "hindi": "यह रहा ताज़ा सारांश (विवरण अंग्रेज़ी में):",
    "assamese": "এয়া শেহতীয়া সাৰাংশ (বিৱৰণ ইংৰাজীত):",
}


def answer(message: str) -> Dict[str, Any]:
    intent, ent = classify(message)
    if intent == "overview":
        text = _overview()
    elif intent == "zones":
        text = _zones(ent.get("level"))
    elif intent == "district":
        text = _district(ent["district"])
    elif intent == "village":
        text = _village(ent["village"])
    elif intent in ("gauges", "forecast"):
        text = _gauges(intent == "forecast")
    elif intent == "rainfall":
        text = _rainfall()
    elif intent == "relief":
        text = _relief(ent.get("district"))
    elif intent == "alerts":
        text = _alerts()
    elif intent == "actions":
        text = _actions()
    elif intent == "contacts":
        text = _contacts()
    elif intent == "safety":
        text = _safety()
    else:
        text = _help()

    lang = detect_language(message)
    if lang in LOCAL_HEADLINES:
        text = LOCAL_HEADLINES[lang] + "\n" + text
    return {"reply": text, "intent": intent, "entities": ent}
