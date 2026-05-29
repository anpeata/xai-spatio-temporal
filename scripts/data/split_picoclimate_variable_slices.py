"""Split Picoclimate variable slices into per-city and per-date CSVs.

The source of truth for this split is data/picoclimate_test/variable_slices/.
The script reconstructs a wide track table from the long-form variable slices,
then writes flat per-date CSVs under data/picoclimate_test/variable_slices/cities/.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import List

import pandas as pd


VALUE_COLUMNS = [
    "air_temp_c",
    "rel_humidity_pct",
    "wind_speed_ms",
    "wind_dir_deg",
    "pressure_hpa",
    "precipitation_mm",
    "solar_wm2",
    "longwave_wm2",
    "surface_temp_c",
    "soil_moisture_pct",
    "ndvi",
    "pm25_ugm3",
    "pm10_ugm3",
    "co2_ppm",
    "no2_ppb",
    "o3_ppb",
    "noise_db",
    "traffic_index",
    "pedestrian_index",
    "sky_view_factor",
    "impervious_fraction",
    "water_proximity",
    "heat_index_c",
]

BASE_KEYS = ["track_id", "city", "date", "time_slot", "slot_index", "loc_index", "timestamp"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split Picoclimate variable slices into city/track folders")
    parser.add_argument("--data-dir", type=Path, default=Path("data/picoclimate_test"))
    return parser.parse_args()


def _load_variable_table(variable_dir: Path, variable: str) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for csv_path in sorted(variable_dir.glob("day_*.csv")):
        frame = pd.read_csv(csv_path, low_memory=False)
        frame = frame.rename(columns={"value": variable})
        frames.append(frame)
    if not frames:
        raise RuntimeError(f"No slice files found for {variable} in {variable_dir}")
    return pd.concat(frames, ignore_index=True)


def _reconstruct_wide_table(variable_root: Path) -> pd.DataFrame:
    long_frames: List[pd.DataFrame] = []
    for variable in VALUE_COLUMNS:
        variable_dir = variable_root / variable
        frame = _load_variable_table(variable_dir, variable)
        frame = frame[BASE_KEYS + [variable]].copy()
        frame["loc_index"] = pd.to_numeric(frame["loc_index"], errors="coerce")
        long_frames.append(frame)

    long_df = pd.concat(long_frames, ignore_index=True)
    wide = long_df.pivot_table(index=BASE_KEYS, values=VALUE_COLUMNS, aggfunc="first").reset_index()
    wide.insert(5, "loc_id", pd.NA)
    wide["true_regime"] = pd.NA
    wide["timestamp"] = pd.to_numeric(wide["timestamp"], errors="coerce")
    wide = wide.sort_values(["track_id", "date", "slot_index", "loc_index"], kind="mergesort").reset_index(drop=True)
    return wide


def _write_date_csv(date_df: pd.DataFrame, date_csv: Path) -> None:
    date_csv.parent.mkdir(parents=True, exist_ok=True)

    date_df = date_df.copy().sort_values(["track_id", "slot_index", "loc_index"], kind="mergesort").reset_index(drop=True)
    date_df.to_csv(date_csv, index=False)


def main() -> None:
    args = _parse_args()
    data_dir = args.data_dir
    source_root = data_dir / "variable_slices"
    if not source_root.exists():
        raise SystemExit(f"Missing input folder: {source_root}")

    wide = _reconstruct_wide_table(source_root)

    city_root = source_root / "cities"
    if city_root.exists():
        shutil.rmtree(city_root)
    city_root.mkdir(parents=True, exist_ok=True)

    for city, city_df in wide.groupby("city", sort=True):
        for date, date_df in city_df.groupby("date", sort=True):
            _write_date_csv(date_df, city_root / city / f"{date}.csv")

    print(f"Wrote city hierarchy under: {city_root}")


if __name__ == "__main__":
    main()