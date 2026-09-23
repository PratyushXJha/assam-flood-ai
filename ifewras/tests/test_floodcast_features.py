"""Tests for FloodCast AI features: 72-hour dataset compute, red zones and throttled SMS / voice dispatch.
"""
import os
import sys
import unittest

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from starlette.testclient import TestClient
from app.main import app
from app.alerts.dispatcher import AlertDispatcher
from app.scenarios.dataset_loader import DatasetError, DEFAULT_DATASET_PATH, parse_dataset_csv, load_default_dataset
from app.scenarios.scenario_manager import ScenarioManager


class TestDatasetCompute(unittest.TestCase):
    def setUp(self):
        self.mgr = ScenarioManager()

    def test_default_dataset_has_73_hourly_rows(self):
        frames = load_default_dataset()
        self.assertEqual([f["hour"] for f in frames], list(range(73)))

    def test_compute_hour_runs_pipeline_on_dataset_row(self):
        s0 = self.mgr.compute_hour(0)
        s40 = self.mgr.compute_hour(40)
        self.assertEqual(s40["computation"]["hour"], 40)
        self.assertEqual(s40["kpi_summary"]["lead_time_hours"], 32)
        # Results come from the data, so they change as the flood builds
        self.assertGreater(s40["kpi_summary"]["flooded_area_sq_km"], s0["kpi_summary"]["flooded_area_sq_km"])
        # Gauge trends are derived from the dataset history
        self.assertTrue(s40["computation"]["gauge_trend_m_per_hr"])
        self.assertEqual(s0["computation"]["gauge_trend_m_per_hr"], {})

    def test_compute_hour_is_clamped(self):
        self.assertEqual(self.mgr.compute_hour(500)["computation"]["hour"], 72)
        self.assertEqual(self.mgr.compute_hour(-3)["computation"]["hour"], 0)

    def test_invalid_dataset_rejected(self):
        with self.assertRaises(DatasetError):
            parse_dataset_csv("foo,bar\n1,2\n")
        with self.assertRaises(DatasetError):
            parse_dataset_csv("hour,CATCH_A__rate_mm_hr,GAUGE_X\n0,1,2\n2,1,2\n")

    def test_custom_dataset_load(self):
        with open(DEFAULT_DATASET_PATH, encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        info = self.mgr.load_dataset_csv("\n".join(lines[:25]), name="first-day.csv")
        self.assertEqual(info["hours"], 23)
        self.assertEqual(self.mgr.compute_hour(72)["computation"]["hour"], 23)


class TestZones(unittest.TestCase):
    def test_zones_green_at_start_and_red_at_peak(self):
        mgr = ScenarioManager()
        start = mgr.compute_hour(0)["stage3"]["zones"]
        self.assertTrue(all(z["level"] == "GREEN" for z in start))
        peak = mgr.compute_hour(48)["stage3"]["zones"]
        red = [z for z in peak if z["level"] == "RED"]
        self.assertTrue(red)
        for z in red:
            self.assertEqual(len(z["center"]), 2)
            self.assertTrue(z["red_village_ids"] or z["overtop_depth_m"] >= 1.5)


class FailingProvider:
    name = "failing"

    def send_sms(self, to, body):
        raise RuntimeError("carrier down")

    def place_call(self, to, script, language):
        raise RuntimeError("carrier down")


class TestDispatcher(unittest.TestCase):
    def setUp(self):
        self.d = AlertDispatcher()
        self.alerts = ScenarioManager().compute_hour(48)["stage3"]["alerts"]

    def test_interval_follows_rate(self):
        self.d.update_settings({"sms_per_minute": 20, "calls_per_minute": 4})
        self.assertAlmostEqual(self.d.interval_seconds("sms"), 3.0)
        self.assertAlmostEqual(self.d.interval_seconds("voice"), 15.0)
        # Out-of-range values are clamped to safe, carrier-friendly bounds
        self.d.update_settings({"sms_per_minute": 100000})
        self.assertEqual(self.d.settings["sms_per_minute"], 120)

    def test_voice_only_for_critical_alerts(self):
        critical = [a for a in self.alerts if a["is_critical"]][:1]
        advisory = [a for a in self.alerts if not a["is_critical"]][:1]
        r = self.d.enqueue_alerts(critical + advisory, ["sms", "voice"])
        per_village = r["recipients"] // 2
        self.assertEqual(r["queued"]["sms"], per_village * 2)
        self.assertEqual(r["queued"]["voice"], per_village)
        self.assertEqual(len(self.d.feed_since(0)), 2)

    def test_messages_sent_and_failures_retried(self):
        self.d.enqueue_alerts(self.alerts[:1], ["sms"])
        self.assertGreater(self.d.drain("sms"), 0)
        self.assertEqual(self.d.status()["channels"]["sms"]["pending"], 0)

        self.d.reset()
        self.d.simulator = FailingProvider()
        self.d.update_settings({"max_retries": 1, "retry_backoff_seconds": 1})
        self.d.enqueue_alerts(self.alerts[:1], ["sms"])
        self.d.drain("sms")
        self.assertEqual({j["status"] for j in self.d.jobs.values()}, {"retrying"})
        for j in self.d.jobs.values():
            j["not_before"] = 0
        self.d.drain("sms")
        self.assertEqual({j["status"] for j in self.d.jobs.values()}, {"failed"})


class TestNewEndpoints(unittest.TestCase):
    def test_compute_dispatch_and_feed(self):
        with TestClient(app) as client:
            res = client.post("/api/v1/simulation/compute/48")
            self.assertEqual(res.status_code, 200)
            red = next(z for z in res.json()["stage3"]["zones"] if z["level"] == "RED")

            latest = client.get("/api/v1/alerts/feed").json()["latest_event_id"]
            res = client.post("/api/v1/alerts/dispatch", json={"zone_id": red["zone_id"]})
            self.assertEqual(res.status_code, 200)
            self.assertGreater(res.json()["queued"]["sms"], 0)

            feed = client.get(f"/api/v1/alerts/feed?since={latest}").json()
            self.assertTrue(feed["events"])
            self.assertIn("hindi", feed["events"][0]["messages"])

            self.assertEqual(client.get("/api/v1/stage3/zones").status_code, 200)
            self.assertEqual(client.get("/receiver").status_code, 200)
            self.assertEqual(client.post("/api/v1/simulation/dataset", content=b"bad").status_code, 400)
            self.assertEqual(client.get("/health").json()["system"], "FloodCast AI")


if __name__ == "__main__":
    unittest.main()
