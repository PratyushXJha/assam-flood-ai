"""End-to-End Integration and Scenario Playback Tests.
"""
import unittest
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.scenarios.scenario_manager import ScenarioManager
from app.main import app
from starlette.testclient import TestClient

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.mgr = ScenarioManager()
        self.client = TestClient(app)

    def test_scenario_progression_cascade(self):
        # Step 0: T=0h (Hills Trigger)
        s0 = self.mgr.set_step(0)
        self.assertEqual(s0["current_step"]["step_index"], 0)
        self.assertGreater(s0["kpi_summary"]["red_hill_triggers"], 0)
        self.assertEqual(s0["kpi_summary"]["danger_gauges_active"], 0)

        # Step 2: T=48h (Peak Flood Stage)
        s2 = self.mgr.set_step(2)
        self.assertEqual(s2["current_step"]["step_index"], 2)
        self.assertGreater(s2["kpi_summary"]["danger_gauges_active"], 0)
        self.assertGreater(s2["kpi_summary"]["critical_p1_villages"], 0)
        self.assertGreater(s2["kpi_summary"]["rescue_boats_deployed"], 0)

        # Step 3: T=72h (Downstream Peak)
        s3 = self.mgr.set_step(3)
        self.assertEqual(s3["current_step"]["step_index"], 3)
        self.assertGreater(s3["kpi_summary"]["flooded_area_sq_km"], 100.0)

    def test_fastapi_rest_endpoints(self):
        # Health
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "HEALTHY")

        # Stage 1 Catchments
        res = self.client.get("/api/v1/stage1/catchments")
        self.assertEqual(res.status_code, 200)
        self.assertGreater(len(res.json()["catchments"]), 0)

        # Stage 2 Gauges
        res = self.client.get("/api/v1/stage2/gauges")
        self.assertEqual(res.status_code, 200)
        self.assertIn("gauges", res.json())

        # Stage 2 Extent GeoJSON
        res = self.client.get("/api/v1/stage2/extent")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["type"], "FeatureCollection")

        # Stage 3 Risk Rankings
        res = self.client.get("/api/v1/stage3/risk-rankings")
        self.assertEqual(res.status_code, 200)
        self.assertIn("ranked_villages", res.json())

        # Stage 3 Allocation
        res = self.client.get("/api/v1/stage3/allocation")
        self.assertEqual(res.status_code, 200)
        self.assertIn("allocation_plan", res.json())

        # Stage 3 Multilingual Alerts
        res = self.client.get("/api/v1/stage3/alerts")
        self.assertEqual(res.status_code, 200)
        self.assertIn("alerts", res.json())

        # Simulation Step Jump
        res = self.client.post("/api/v1/simulation/set-step/1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["current_step"]["step_index"], 1)

if __name__ == "__main__":
    unittest.main()
