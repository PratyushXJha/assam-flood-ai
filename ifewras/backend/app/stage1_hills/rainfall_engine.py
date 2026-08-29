"""Rainfall processing and antecedent soil moisture engine for Stage 1.
Models GPM-IMERG precipitation rates, multi-hour accumulation, and runoff generation.
"""
from typing import Dict, Any, List
import numpy as np
from app.stage1_hills.catchments import get_all_catchments, get_catchment_by_id

class RainfallEngine:
    def __init__(self):
        self.catchments = get_all_catchments()

    def calculate_effective_runoff(
        self,
        catchment_id: str,
        rainfall_rate_mm_hr: float,
        accum_6h_mm: float,
        soil_moisture_pct: float
    ) -> Dict[str, float]:
        """
        Calculate effective precipitation and estimated runoff discharge (cumecs).
        Soil moisture saturation acts as a non-linear multiplier on runoff fraction.
        """
        catchment = get_catchment_by_id(catchment_id)
        base_c = catchment["runoff_coefficient"]
        area_sq_km = catchment["area_sq_km"]

        # Soil moisture multiplier: dry soil (<40%) absorbs more; saturated (>75%) produces flash runoff
        if soil_moisture_pct > 75.0:
            moisture_factor = 1.0 + ((soil_moisture_pct - 75.0) / 25.0) * 0.45  # Up to 1.45x
        elif soil_moisture_pct < 40.0:
            moisture_factor = 0.70 + (soil_moisture_pct / 40.0) * 0.30
        else:
            moisture_factor = 1.0

        effective_c = min(0.98, base_c * moisture_factor)

        # Rational Runoff equation conversion: Q (m³/s) = (C * I * A) / 3.6
        # I in mm/hr, A in km²
        instant_runoff_cumec = (effective_c * rainfall_rate_mm_hr * area_sq_km) / 3.6
        accum_6h_volume_mcm = (effective_c * accum_6h_mm * area_sq_km) / 1000.0  # Million Cubic Meters

        return {
            "effective_runoff_coefficient": round(effective_c, 3),
            "instant_runoff_cumec": round(instant_runoff_cumec, 1),
            "accum_6h_volume_mcm": round(accum_6h_volume_mcm, 2),
            "moisture_factor": round(moisture_factor, 2)
        }

    def process_telemetry_snapshot(self, snapshot_data: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """
        Process a full snapshot of rainfall readings across all hill catchments.
        snapshot_data format: { catchment_id: { "rate_mm_hr": ..., "accum_6h_mm": ..., "accum_24h_mm": ..., "soil_moisture_pct": ... } }
        """
        results = []
        for catchment in self.catchments:
            cid = catchment["id"]
            telemetry = snapshot_data.get(cid, {
                "rate_mm_hr": 5.0,
                "accum_6h_mm": 18.0,
                "accum_24h_mm": 40.0,
                "soil_moisture_pct": 55.0
            })

            runoff_metrics = self.calculate_effective_runoff(
                catchment_id=cid,
                rainfall_rate_mm_hr=telemetry["rate_mm_hr"],
                accum_6h_mm=telemetry["accum_6h_mm"],
                soil_moisture_pct=telemetry["soil_moisture_pct"]
            )

            results.append({
                "catchment_id": cid,
                "catchment_name": catchment["name"],
                "region": catchment["region"],
                "rate_mm_hr": round(telemetry["rate_mm_hr"], 2),
                "accum_6h_mm": round(telemetry["accum_6h_mm"], 2),
                "accum_24h_mm": round(telemetry["accum_24h_mm"], 2),
                "soil_moisture_pct": round(telemetry["soil_moisture_pct"], 1),
                "runoff_metrics": runoff_metrics,
                "downstream_districts": catchment["downstream_districts"],
                "downstream_gauges": catchment["downstream_gauges"],
                "lag_time_hours": catchment["lag_time_hours"]
            })
        return results
