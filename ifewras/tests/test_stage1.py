"""Unit tests for Stage 1 (Watch the Hills).
"""
import unittest
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.stage1_hills.catchments import get_all_catchments, get_catchment_by_id
from app.stage1_hills.rainfall_engine import RainfallEngine
from app.stage1_hills.trigger_detector import TriggerDetector

class TestStage1(unittest.TestCase):
    def setUp(self):
        self.rainfall_engine = RainfallEngine()
        self.trigger_detector = TriggerDetector()

    def test_catchment_definitions(self):
        catchments = get_all_catchments()
        self.assertGreaterEqual(len(catchments), 6)
        siang = get_catchment_by_id("CATCH_SIANG")
        self.assertEqual(siang["name"], "Siang / Upper Brahmaputra Basin")
        self.assertIn("Dhemaji", siang["downstream_districts"])

    def test_effective_runoff_calculation(self):
        # Low soil moisture
        dry_runoff = self.rainfall_engine.calculate_effective_runoff(
            catchment_id="CATCH_SIANG",
            rainfall_rate_mm_hr=20.0,
            accum_6h_mm=40.0,
            soil_moisture_pct=30.0
        )
        # High soil moisture
        saturated_runoff = self.rainfall_engine.calculate_effective_runoff(
            catchment_id="CATCH_SIANG",
            rainfall_rate_mm_hr=20.0,
            accum_6h_mm=40.0,
            soil_moisture_pct=90.0
        )
        self.assertGreater(saturated_runoff["instant_runoff_cumec"], dry_runoff["instant_runoff_cumec"])
        self.assertGreater(saturated_runoff["accum_6h_volume_mcm"], dry_runoff["accum_6h_volume_mcm"])

    def test_trigger_detection_thresholds(self):
        # Normal conditions
        normal_eval = self.trigger_detector.evaluate_catchment_trigger(
            catchment_id="CATCH_SUBANSIRI",
            rate_mm_hr=5.0,
            accum_6h_mm=15.0,
            accum_24h_mm=30.0,
            soil_moisture_pct=50.0
        )
        self.assertEqual(normal_eval["severity"], "NORMAL")
        self.assertEqual(normal_eval["action_code"], "GREEN")

        # Emergency cloudburst conditions
        emergency_eval = self.trigger_detector.evaluate_catchment_trigger(
            catchment_id="CATCH_SUBANSIRI",
            rate_mm_hr=52.0,
            accum_6h_mm=120.0,
            accum_24h_mm=210.0,
            soil_moisture_pct=92.0
        )
        self.assertEqual(emergency_eval["severity"], "FLASH_FLOOD_EMERGENCY")
        self.assertEqual(emergency_eval["action_code"], "RED_ALERT")
        self.assertGreaterEqual(emergency_eval["trigger_score"], 80.0)

if __name__ == "__main__":
    unittest.main()
