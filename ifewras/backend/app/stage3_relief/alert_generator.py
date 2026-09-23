"""Multilingual Resident Alert Generator for Stage 3 (Help the People).
Generates short SMS alerts and AI voice-call scripts in English, Hindi (हिन्दी)
and Assamese (অসমীয়া), each kept within SMS segment limits.
"""
from typing import Dict, Any, List
from app.config import EMERGENCY_CONTACTS, VOICE_LOCALES

# Max characters per language. English fits one GSM-7 SMS (160). Hindi/Assamese are
# sent as UCS-2, where one SMS holds 70 chars (67 when concatenated) -> cap at 2 parts.
SMS_CHAR_LIMITS = {"english": 160, "hindi": 134, "assamese": 134}
LANGUAGE_NAMES = {"english": "English", "hindi": "Hindi (हिन्दी)", "assamese": "Assamese (অসমীয়া)"}


def sms_segments(text: str) -> int:
    """Number of SMS parts the carrier will bill/deliver for this text."""
    is_gsm = all(ord(c) < 128 for c in text)
    single, multi = (160, 153) if is_gsm else (70, 67)
    if len(text) <= single:
        return 1
    return -(-len(text) // multi)


def _fit(lang: str, with_camp: str, without_camp: str) -> str:
    """Use the version naming the relief camp if it fits the SMS limit, else the generic one."""
    return with_camp if len(with_camp) <= SMS_CHAR_LIMITS[lang] else without_camp


class AlertGenerator:
    def __init__(self):
        self.helplines = EMERGENCY_CONTACTS

    def _sms_texts(self, vname: str, depth: float, camp: str, critical: bool) -> Dict[str, str]:
        if critical:
            return {
                "english": _fit(
                    "english",
                    f"FLOOD ALERT {vname}: {depth}m water expected. Evacuate now to {camp}. Help 1079/112 -FloodCast AI",
                    f"FLOOD ALERT {vname}: {depth}m water expected. Evacuate now to nearest relief centre. Help 1079/112 -FloodCast AI",
                ),
                "hindi": _fit(
                    "hindi",
                    f"बाढ़ चेतावनी! {vname} में {depth} मी. पानी। तुरंत {camp} जाएँ। मदद: 1079/112",
                    f"बाढ़ चेतावनी! {vname} में {depth} मी. पानी। तुरंत नज़दीकी राहत शिविर जाएँ। मदद: 1079/112",
                ),
                "assamese": _fit(
                    "assamese",
                    f"বান সতৰ্কবাৰ্তা! {vname}ত {depth} মি. পানী। এতিয়াই {camp}লৈ যাওক। সহায়: 1079/112",
                    f"বান সতৰ্কবাৰ্তা! {vname}ত {depth} মি. পানী। এতিয়াই ওচৰৰ ত্ৰাণ শিবিৰলৈ যাওক। সহায়: 1079/112",
                ),
            }
        return {
            "english": f"FLOOD WATCH {vname}: river rising ({depth}m). Stay alert, keep documents ready. Help 1079 -FloodCast AI",
            "hindi": f"बाढ़ सतर्कता: {vname} में जलस्तर बढ़ रहा है ({depth} मी.)। सतर्क रहें। मदद: 1079",
            "assamese": f"বান সতৰ্কতা: {vname}ত পানী বাঢ়িছে ({depth} মি.)। সাৱধানে থাকক। সহায়: 1079",
        }

    def _voice_scripts(self, vname: str, camp: str, critical: bool) -> Dict[str, str]:
        if critical:
            return {
                "english": (
                    f"This is a FloodCast A I emergency alert. There will be a flood in your area, {vname}. "
                    f"Please evacuate and proceed to the nearest relief centre, {camp}. For help, call 1 0 7 9."
                ),
                "hindi": (
                    f"यह फ्लडकास्ट ए आई आपातकालीन सूचना है। आपके क्षेत्र {vname} में बाढ़ आने वाली है। "
                    f"कृपया तुरंत घर खाली करें और निकटतम राहत केंद्र {camp} पहुँचें। सहायता के लिए 1 0 7 9 पर कॉल करें।"
                ),
                "assamese": (
                    f"এইটো ফ্লাডকাষ্ট এ আই জৰুৰী সতৰ্কবাৰ্তা। আপোনাৰ অঞ্চল {vname}ত বান আহিব। "
                    f"অনুগ্ৰহ কৰি ঘৰ এৰি ওচৰৰ ত্ৰাণ শিবিৰ {camp}লৈ যাওক। সহায়ৰ বাবে 1 0 7 9 নম্বৰত ফোন কৰক।"
                ),
            }
        return {
            "english": f"FloodCast A I flood watch for {vname}. River levels are rising. Stay alert and be ready to move to {camp}.",
            "hindi": f"फ्लडकास्ट ए आई बाढ़ सतर्कता, {vname}। नदी का जलस्तर बढ़ रहा है। सतर्क रहें और {camp} जाने के लिए तैयार रहें।",
            "assamese": f"ফ্লাডকাষ্ট এ আই বান সতৰ্কতা, {vname}। নদীৰ পানী বাঢ়িছে। সাৱধানে থাকক আৰু {camp}লৈ যাবলৈ সাজু থাকক।",
        }

    def generate_village_alerts(self, village_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate short localized SMS + voice-call alert payloads in English, Hindi and Assamese.
        """
        vname = village_plan.get("village_name", "Village")
        dist = village_plan.get("district", "Assam")
        depth = village_plan.get("estimated_flood_depth_m", 0.0)
        risk_score = village_plan.get("risk_score", 0.0)
        tier = village_plan.get("risk_tier", "LOW_MONITORING_P4")
        camp = village_plan.get("staging_hub", "District Relief Shelter")

        is_critical = tier == "EXTREME_PRIORITY_P1" or risk_score >= 50.0 or depth >= 0.8
        sms = self._sms_texts(vname, depth, camp, is_critical)
        voice = self._voice_scripts(vname, camp, is_critical)
        title = f"{'Flood evacuation alert' if is_critical else 'Flood watch'}: {vname}, {dist}"

        languages = {}
        for lang in ("english", "hindi", "assamese"):
            languages[lang] = {
                "language_name": LANGUAGE_NAMES[lang],
                "title": title,
                "sms_body": sms[lang],
                "sms_char_count": len(sms[lang]),
                "sms_char_limit": SMS_CHAR_LIMITS[lang],
                "sms_segments": sms_segments(sms[lang]),
                "voice_script": voice[lang],
                "voice_locale": VOICE_LOCALES[lang]["locale"],
            }

        return {
            "village_id": village_plan.get("village_id"),
            "village_name": vname,
            "district": dist,
            "risk_score": risk_score,
            "risk_tier": tier,
            "is_critical": is_critical,
            "languages": languages,
            "dispatch_channels": ["SMS", "AI_VOICE_CALL"],
            "helpline_numbers": self.helplines,
            "status": "READY",
        }

    def generate_all_alerts(self, dispatch_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate alert packages for all villages in the current dispatch plan.
        """
        return [self.generate_village_alerts(v) for v in dispatch_plan]
