"""Unit tests for Stage 2 (Predict the Plains).
"""
import unittest
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.stage2_plains.cwc_gauges import get_all_gauges, get_gauge_by_id
from app.stage2_plains.forecast_model import RiverForecastModel
from app.stage2_plains.dem_floodfill import DEMFloodFillModel
from app.stage2_plains.village_depth import VillageDepthEngine
from app.stage2_plains.road_submersion import RoadSubmersionEngine

class TestStage2(unittest.TestCase):
    def setUp(self):
        self.forecast_model = RiverForecastModel()
        self.dem_model = DEMFloodFillModel()
        self.village_engine = VillageDepthEngine()
        self.road_engine = RoadSubmersionEngine()

    def test_gauge_metadata(self):
        gauges = get_all_gauges()
        self.assertGreaterEqual(len(gauges), 7)
        nemati = get_gauge_by_id("GAUGE_NEMATIGHAT")
        self.assertGreater(nemati["danger_level_m"], nemati["warning_level_m"])
        self.assertGreater(nemati["highest_flood_level_m"], nemati["danger_level_m"])

    def test_forecast_hydrograph_generation(self):
        fc = self.forecast_model.generate_gauge_forecast(
            gauge_id="GAUGE_NEMATIGHAT",
            current_level_m=84.50,
            upstream_surges={"CATCH_SIANG": 250.0, "CATCH_SUBANSIRI": 180.0}
        )
        self.assertEqual(len(fc["hydrograph_series"]), 13) # 0h to 72h every 6h
        self.assertIn("forecast_24h_m", fc)
        self.assertIn("forecast_48h_m", fc)
        self.assertIn("forecast_72h_m", fc)
        self.assertGreaterEqual(fc["peak_predicted_level_m"], 84.50)

    def test_dem_flood_extent(self):
        # Gauge level above bank level
        gauge_levels = {"GAUGE_NEMATIGHAT": 86.50, "GAUGE_DIBRUGARH": 106.00}
        geojson = self.dem_model.generate_full_extent_geojson(gauge_levels)
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertGreater(len(geojson["features"]), 0)
        self.assertGreater(geojson["metadata"]["total_inundated_sq_km"], 0.0)

    def test_village_depth_calculation(self):
        gauge_levels = {"GAUGE_NEMATIGHAT": 86.00} # Salmora terrain is ~84.60m
        villages = self.village_engine.compute_all_villages(gauge_levels)
        salmora = next(v for v in villages if v["village_id"] == "VIL_MAJULI_SALMORA")
        self.assertGreater(salmora["estimated_flood_depth_m"], 1.0)
        self.assertIn(salmora["impact_category"], ["MODERATE_SUBMERSION", "CRITICAL_INUNDATION"])

    def test_road_submersion_status(self):
        # Nematighat gauge at 86.5m (Majuli spine road crown is 85.3m)
        gauge_levels = {"GAUGE_NEMATIGHAT": 86.50}
        roads = self.road_engine.evaluate_all_roads(gauge_levels)
        majuli_road = next(r for r in roads if r["road_id"] == "ROAD_MAJULI_SPINE")
        self.assertEqual(majuli_road["status"], "SUBMERGED_IMPASSABLE")
        self.assertFalse(majuli_road["passable_light_vehicles"])

if __name__ == "__main__":
    unittest.main()
