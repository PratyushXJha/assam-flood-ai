"""Multilingual Resident Alert Generator for Stage 3 (Help the People).
Generates localized emergency evacuation alerts in Assamese (অসমীয়া),
Bodo (बर'), and English for SMS and WhatsApp dispatch.
"""
from typing import Dict, Any, List
from app.config import EMERGENCY_CONTACTS

class AlertGenerator:
    def __init__(self):
        self.helplines = EMERGENCY_CONTACTS

    def generate_village_alerts(self, village_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate localized alert payloads across Assamese, Bodo, and English.
        """
        vname = village_plan.get("village_name", "Village")
        dist = village_plan.get("district", "Assam")
        depth = village_plan.get("estimated_flood_depth_m", 0.0)
        risk_score = village_plan.get("risk_score", 0.0)
        tier = village_plan.get("risk_tier", "LOW_MONITORING_P4")
        camp = village_plan.get("staging_hub", "District Relief Shelter")
        access_mode = village_plan.get("access_mode", "ROAD_CONNECTED")

        is_critical = risk_score >= 50.0 or depth >= 0.8

        # Assamese Text Generation (অসমীয়া)
        if is_critical:
            assamese_title = f"জৰুৰী বান সতৰ্কবাৰ্তা (ASDMA): {vname}, {dist}"
            assamese_sms = (
                f"সতৰ্কবাৰ্তা! {vname}ত পানীৰ উচ্চতা {depth} মিটাৰলৈ বৃদ্ধি পাইছে। "
                f"অনুগ্ৰহ কৰি পলম নকৰি ওচৰৰ আশ্ৰয় শিবিৰ '{camp}'লৈ যাওক। "
                f"{'SDRF নাও ঘাটত অপেক্ষাৰত।' if access_mode == 'BOAT_ONLY' else 'নিৰাপদ পথ ব্যৱহাৰ কৰক।'} "
                f"সহায়ৰ বাবে ফোন কৰক: 1079 / 112"
            )
            assamese_whatsapp = (
                f"🚨 *অসম ৰাজ্যিক দুৰ্যোগ ব্যৱস্থাপনা প্ৰাধিকৰণ (ASDMA) জৰুৰী সতৰ্কবাৰ্তা*\n\n"
                f"📍 *স্থান:* {vname}, {dist} জিলা\n"
                f"🌊 *আনুমানিক বানৰ গভীৰতা:* {depth} মিটাৰ (বিপদজনক)\n"
                f"⚠️ *আঁঁচনিৰ স্তৰ:* {tier}\n\n"
                f"🏃 *নিৰ্দেশনা:* অনতিপলমে নিজৰ পৰিয়াল আৰু পশুধন সুৰক্ষিত স্থানলৈ নিয়ক।\n"
                f"🏕️ *নিৰ্দিষ্ট আশ্ৰয় শিবিৰ:* {camp}\n"
                f"🚤 *যাতায়ত ব্যৱস্থা:* {'SDRF/NDRF নাও নিয়োজিত কৰা হৈছে।' if access_mode == 'BOAT_ONLY' else 'ওখ মথাউৰি পথৰে যাতায়ত কৰক।'}\n\n"
                f"📞 *নিয়ন্ত্ৰণ কক্ষ হেল্পলাইন:* 1079 (ৰাজ্যিক) | 1077 (জিলা) | 112 (জৰুৰী)"
            )
        else:
            assamese_title = f"বান পূৰ্বাভাস জাননী: {vname}"
            assamese_sms = f"জাননী: {vname}ত ব্ৰহ্মপুত্ৰৰ পানী বৃদ্ধি পাইছে। সাৱধান হওক আৰু প্ৰস্তুত থাকক। হেল্পলাইন: 1079"
            assamese_whatsapp = (
                f"ℹ️ *ASDMA বান সতৰ্কতা জাননী*\n\n"
                f"📍 *স্থান:* {vname}, {dist}\n"
                f"পানীৰ স্তৰ বৃদ্ধি পাইছে (বৰ্তমান {depth} মিটাৰ)। ওচৰৰ নিৰাপদ আশ্ৰয় শিবিৰ '{camp}' প্ৰস্তুত কৰা হৈছে।\n"
                f"জৰুৰী সেৱাৰ বাবে: 1079 ত যোগাযোগ কৰক।"
            )

        # Bodo Text Generation (बर')
        if is_critical:
            bodo_title = f"जायख्लं सांग्रांथि (ASDMA): {vname}, {dist}"
            bodo_sms = (
                f"सांग्रांथि! {vname} आव दैबानानि गोथौथिया {depth} मिटार जाबाय। "
                f"दावहारु खौरां लाबानो खाथिनि '{camp}' थाग्रा जायगायाव थां। "
                f"{'SDRF नाउ थाखाबाय।' if access_mode == 'BOAT_ONLY' else 'गोजौ लामाजों थां।'} "
                f"हेल्पलाइन: 1079 / 112"
            )
            bodo_whatsapp = (
                f"🚨 *ASDMA जायख्लं सांग्रांथि खौरां (Bodo Alert)*\n\n"
                f"📍 *जायगा:* {vname}, {dist}\n"
                f"🌊 *दैबानानि गोथौथि:* {depth} मिटार (खैफोदनां)\n"
                f"⚠️ *थाखो:* {tier}\n\n"
                f"🏃 *खावलायनाय:* गावनि नखर आरो जिब-जुनादखौ गोजौ जायगायाव दैथाय।\n"
                f"🏕️ *थाग्रा जायगा (Relief Camp):* {camp}\n"
                f"🚤 *राहा:* {'SDRF नाउ दैथायनाय जाबाय।' if access_mode == 'BOAT_ONLY' else 'गोजौ लामाजों खार।'}\n\n"
                f"📞 *हेल्पलाइन नम्बर:* 1079 | 1077 | 112"
            )
        else:
            bodo_title = f"सांग्रांथि खौरां: {vname}"
            bodo_sms = f"खौरां: {vname} आव दैबाना फैगासिनो दं। सांग्रां जानानै था। हेल्पलाइन: 1079"
            bodo_whatsapp = (
                f"ℹ️ *ASDMA सांग्रांथि खौरां*\n\n"
                f"📍 *जायगा:* {vname}, {dist}\n"
                f"दैबाना फैबाय (गोथौथि {depth} मिटार)। खाथिनि '{camp}' आव थाग्रा राहा खालामनाय जादों।"
            )

        # English Text Generation
        if is_critical:
            english_title = f"CRITICAL FLOOD EVACUATION ALERT: {vname}, {dist}"
            english_sms = (
                f"ALERT! Flood depth predicted at {depth}m in {vname}. "
                f"Evacuate immediately to shelter: '{camp}'. "
                f"{'SDRF rescue boats stationed at ghat.' if access_mode == 'BOAT_ONLY' else 'Use high embankment route.'} "
                f"Helpline: 1079 / 112."
            )
            english_whatsapp = (
                f"🚨 *ASDMA EMERGENCY FLOOD EVACUATION ORDER*\n\n"
                f"📍 *Location:* {vname}, District: {dist}\n"
                f"🌊 *Predicted Flood Depth:* {depth} meters (Severe Overtopping)\n"
                f"⚠️ *Priority Tier:* {tier} (Risk Score: {risk_score}/100)\n\n"
                f"🏃 *Action Required:* Move families and livestock to designated high-ground refuge immediately.\n"
                f"🏕️ *Designated Relief Camp:* {camp}\n"
                f"🚤 *Transit Modality:* {'SDRF / NDRF motorized rescue boats deployed.' if access_mode == 'BOAT_ONLY' else 'High clearance road route operational.'}\n\n"
                f"📞 *24x7 Control Room:* 1079 (State) | 1077 (District) | 112 (National Emergency)"
            )
        else:
            english_title = f"Flood Watch Advisory: {vname}"
            english_sms = f"ADVISORY: River water rising in {vname} ({depth}m). Stay vigilant. Nearest shelter: {camp}. Helpline: 1079"
            english_whatsapp = (
                f"ℹ️ *ASDMA Flood Watch Advisory*\n\n"
                f"📍 *Location:* {vname}, {dist}\n"
                f"Water levels rising ({depth}m). Relief shelter '{camp}' is on standby. Dial 1079 for emergency assistance."
            )

        return {
            "village_id": village_plan.get("village_id"),
            "village_name": vname,
            "district": dist,
            "risk_score": risk_score,
            "is_critical": is_critical,
            "languages": {
                "assamese": {
                    "language_name": "Assamese (অসমীয়া)",
                    "title": assamese_title,
                    "sms_body": assamese_sms,
                    "whatsapp_body": assamese_whatsapp
                },
                "bodo": {
                    "language_name": "Bodo (बर')",
                    "title": bodo_title,
                    "sms_body": bodo_sms,
                    "whatsapp_body": bodo_whatsapp
                },
                "english": {
                    "language_name": "English",
                    "title": english_title,
                    "sms_body": english_sms,
                    "whatsapp_body": english_whatsapp
                }
            },
            "dispatch_channels": ["SMS_CELL_BROADCAST", "WHATSAPP_BUSINESS_API", "IVRS_VOICE_CALL"],
            "helpline_numbers": self.helplines,
            "status": "QUEUED_FOR_BROADCAST"
        }

    def generate_all_alerts(self, dispatch_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate alert packages for all villages in the current dispatch plan.
        """
        alerts = []
        for v in dispatch_plan:
            alt = self.generate_village_alerts(v)
            alerts.append(alt)
        return alerts
