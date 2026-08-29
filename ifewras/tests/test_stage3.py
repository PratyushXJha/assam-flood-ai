"""Unit tests for Stage 3 (Help the People - Relief Allocation & Alerts).
"""
import unittest
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.stage3_relief.risk_scorer import RiskScorer
from app.stage3_relief.access_profiler import AccessProfiler
from app.stage3_relief.allocation_engine import ReliefAllocationEngine
from app.stage3_relief.alert_generator import AlertGenerator

class TestStage3(unittest.TestCase):
    def setUp(self):
        self.risk_scorer = RiskScorer()
        self.access_profiler = AccessProfiler()
        self.allocation_engine = ReliefAllocationEngine()
        self.alert_generator = AlertGenerator()

    def test_risk_scoring_explainability(self):
        village_data = {
            "village_id": "VIL_MAJULI_SALMORA",
            "village_name": "Salmora",
            "district": "Majuli",
            "latitude": 26.88,
            "longitude": 94.27,
            "population": 4800,
            "char_island_status": True,
            "vulnerability_index": 0.88,
            "estimated_flood_depth_m": 1.60
        }
        scored = self.risk_scorer.compute_risk_score(village_data, is_road_cut_off=True)
        self.assertGreaterEqual(scored["final_risk_score"], 60.0)
        self.assertIn("explainability", scored)
        self.assertIn("depth_subscore", scored["explainability"])
        self.assertIn("primary_driver", scored)

    def test_access_profiler(self):
        char_village = {
            "village_id": "VIL_BARPETA_MANDIA",
            "village_name": "Mandia Char",
            "district": "Barpeta",
            "char_island_status": True,
            "estimated_flood_depth_m": 1.20
        }
        profile = self.access_profiler.evaluate_village_access(char_village)
        self.assertEqual(profile["access_mode"], "BOAT_ONLY")
        self.assertTrue(profile["is_boat_accessible"])

    def test_resource_constrained_allocation(self):
        mock_villages = [
            {
                "village_id": "V1",
                "village_name": "Village High Risk",
                "district": "Majuli",
                "rank": 1,
                "final_risk_score": 88.0,
                "risk_tier": "EXTREME_PRIORITY_P1",
                "estimated_flood_depth_m": 2.0,
                "population": 5000,
                "char_island_status": True,
                "access_profile": {"access_mode": "BOAT_ONLY", "recommended_craft": "Motor Boat"}
            }
        ]
        result = self.allocation_engine.allocate_resources(mock_villages)
        self.assertEqual(len(result["dispatch_plan"]), 1)
        plan_item = result["dispatch_plan"][0]
        self.assertEqual(plan_item["dispatch_status"], "DISPATCHED_EN_ROUTE")
        self.assertGreater(plan_item["allocated"]["sdrf_inflatable_boats"] + plan_item["allocated"]["ndrf_motor_boats"], 0)

    def test_multilingual_alert_generation(self):
        plan_item = {
            "village_id": "VIL_MAJULI_SALMORA",
            "village_name": "Salmora",
            "district": "Majuli",
            "risk_score": 82.5,
            "risk_tier": "EXTREME_PRIORITY_P1",
            "estimated_flood_depth_m": 1.75,
            "staging_hub": "Salmora Higher Secondary Relief Shelter",
            "access_mode": "BOAT_ONLY"
        }
        alerts = self.alert_generator.generate_village_alerts(plan_item)
        self.assertIn("assamese", alerts["languages"])
        self.assertIn("bodo", alerts["languages"])
        self.assertIn("english", alerts["languages"])

        # Check Assamese characters present
        assamese_text = alerts["languages"]["assamese"]["sms_body"]
        self.assertTrue(any(ord(c) >= 0x0980 and ord(c) <= 0x09FF for c in assamese_text))

        # Check Bodo / Devanagari characters present
        bodo_text = alerts["languages"]["bodo"]["sms_body"]
        self.assertTrue(any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in bodo_text))

if __name__ == "__main__":
    unittest.main()
