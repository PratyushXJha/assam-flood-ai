"""Loader and validator for the hourly 72-hour flood telemetry dataset.

CSV layout (one row per hour, hours 0..72):
    hour,
    <CATCHMENT_ID>__rate_mm_hr, <CATCHMENT_ID>__accum_6h_mm,
    <CATCHMENT_ID>__accum_24h_mm, <CATCHMENT_ID>__soil_moisture_pct, ...  (per catchment)
    <GAUGE_ID>, ...                                                        (observed river level, m)
"""
import csv
import io
import os
from typing import Any, Dict, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEFAULT_DATASET_PATH = os.path.join(DATA_DIR, "assam_72h_dataset.csv")

TELEMETRY_FIELDS = ("rate_mm_hr", "accum_6h_mm", "accum_24h_mm", "soil_moisture_pct")
MAX_HOURS = 72


class DatasetError(ValueError):
    pass


def parse_dataset_csv(text: str) -> List[Dict[str, Any]]:
    """Parse CSV text into a list of hourly frames sorted by hour."""
    reader = csv.DictReader(io.StringIO(text.strip()))
    if not reader.fieldnames or "hour" not in reader.fieldnames:
        raise DatasetError("Dataset must be a CSV with an 'hour' column.")

    catchment_ids = sorted({c.split("__")[0] for c in reader.fieldnames if "__" in c})
    gauge_ids = [c for c in reader.fieldnames if c.startswith("GAUGE_")]
    if not catchment_ids or not gauge_ids:
        raise DatasetError("Dataset needs catchment columns (CATCH_X__rate_mm_hr, ...) and gauge columns (GAUGE_X).")

    frames: List[Dict[str, Any]] = []
    for line_no, row in enumerate(reader, start=2):
        try:
            hour = int(float(row["hour"]))
            telemetry = {
                cid: {f: float(row[f"{cid}__{f}"]) for f in TELEMETRY_FIELDS if row.get(f"{cid}__{f}") not in (None, "")}
                for cid in catchment_ids
            }
            gauges = {gid: float(row[gid]) for gid in gauge_ids if row.get(gid) not in (None, "")}
        except (TypeError, ValueError) as exc:
            raise DatasetError(f"Invalid number on CSV line {line_no}: {exc}") from exc
        frames.append({"hour": hour, "stage1_telemetry": telemetry, "stage2_gauge_readings": gauges})

    frames.sort(key=lambda fr: fr["hour"])
    hours = [fr["hour"] for fr in frames]
    if not hours or hours[0] != 0:
        raise DatasetError("Dataset must start at hour 0.")
    if hours != list(range(len(hours))):
        raise DatasetError("Dataset hours must be contiguous (0, 1, 2, ...).")
    if len(hours) > MAX_HOURS + 1:
        raise DatasetError(f"Dataset may contain at most {MAX_HOURS + 1} hourly rows (0..{MAX_HOURS}).")
    return frames


def load_default_dataset() -> List[Dict[str, Any]]:
    with open(DEFAULT_DATASET_PATH, encoding="utf-8") as f:
        return parse_dataset_csv(f.read())
