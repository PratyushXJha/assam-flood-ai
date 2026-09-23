"""Generate the hourly 72-hour Assam flood telemetry dataset used by the Play simulation.

The four calibrated historical snapshots (T+0h, T+24h, T+48h, T+72h) in
backend/app/scenarios/historical_assam_2024.py are used as anchor points. Hourly
values in between are produced with Catmull-Rom interpolation (gauges) and a
small deterministic diurnal/convective signal (rainfall), then written to
backend/app/data/assam_72h_dataset.csv.

Run: python scripts/generate_72h_dataset.py
"""
import csv
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.scenarios.historical_assam_2024 import SCENARIO_TIMELINE  # noqa: E402

OUT_PATH = os.path.join(ROOT, "backend", "app", "data", "assam_72h_dataset.csv")
TELEMETRY_FIELDS = ["rate_mm_hr", "accum_6h_mm", "accum_24h_mm", "soil_moisture_pct"]


def catmull_rom(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def interpolate(anchors, hour):
    """anchors: values at hours 0, 24, 48, 72."""
    seg = min(2, hour // 24)
    t = (hour - seg * 24) / 24.0
    p = [anchors[max(0, seg - 1)], anchors[seg], anchors[seg + 1], anchors[min(3, seg + 2)]]
    return catmull_rom(p[0], p[1], p[2], p[3], t)


def main():
    rng = random.Random(2024)
    catchments = list(SCENARIO_TIMELINE[0]["stage1_telemetry"].keys())
    gauges = list(SCENARIO_TIMELINE[0]["stage2_gauge_readings"].keys())

    header = ["hour"]
    for cid in catchments:
        header += [f"{cid}__{f}" for f in TELEMETRY_FIELDS]
    header += gauges

    rows = []
    for hour in range(73):
        is_anchor = hour % 24 == 0
        row = [hour]
        for cid in catchments:
            for field in TELEMETRY_FIELDS:
                anchors = [snap["stage1_telemetry"][cid][field] for snap in SCENARIO_TIMELINE]
                val = interpolate(anchors, hour)
                if not is_anchor and field == "rate_mm_hr":
                    # Afternoon convective peaks + gauge noise
                    val *= 1.0 + 0.12 * math.sin((hour - 14) / 24.0 * 2 * math.pi) + rng.uniform(-0.06, 0.06)
                if field == "soil_moisture_pct":
                    val = min(100.0, val)
                row.append(round(max(0.0, val), 1))
        for gid in gauges:
            anchors = [snap["stage2_gauge_readings"][gid] for snap in SCENARIO_TIMELINE]
            row.append(round(interpolate(anchors, hour), 2))
        rows.append(row)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} hourly rows x {len(header)} columns to {OUT_PATH}")


if __name__ == "__main__":
    main()
