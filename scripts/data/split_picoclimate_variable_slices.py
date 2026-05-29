"""Split Picoclimate variable slices into per-city and per-track folders.

The source of truth for this split is data/picoclimate_test/variable_slices/.
The script reconstructs a wide track table from the long-form variable slices,
then writes the city/track hierarchy under data/picoclimate_test/variable_slices/cities/.
"""

from __future__ import annotations

import argparse
import importlib.util
from functools import reduce
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


def _load_window_builder(repo_root: Path):
    script_path = repo_root / "scripts" / "data" / "build_window_features_from_tracks.py"
    spec = importlib.util.spec_from_file_location("build_window_features_from_tracks", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import window builder from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "_build_window_features"):
        raise RuntimeError("build_window_features_from_tracks.py must expose _build_window_features")
    return module


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


def _write_track_bundle(track_df: pd.DataFrame, track_dir: Path, builder) -> None:
    track_dir.mkdir(parents=True, exist_ok=True)

    track_df = track_df.copy().sort_values(["date", "slot_index", "loc_index"], kind="mergesort").reset_index(drop=True)
    track_features = builder._build_window_features(track_df)

    track_df.to_csv(track_dir / "tracks_measurements.csv", index=False)
    track_features.to_csv(track_dir / "window_features.csv", index=False)


def main() -> None:
    args = _parse_args()
    data_dir = args.data_dir
    source_root = data_dir / "variable_slices"
    if not source_root.exists():
        raise SystemExit(f"Missing input folder: {source_root}")

    repo_root = data_dir.parent.parent
    builder = _load_window_builder(repo_root)
    wide = _reconstruct_wide_table(source_root)

    city_root = source_root / "cities"
    city_root.mkdir(parents=True, exist_ok=True)

    for city, city_df in wide.groupby("city", sort=True):
        city_dir = city_root / city
        city_dir.mkdir(parents=True, exist_ok=True)

        city_tracks = sorted(city_df["track_id"].unique().tolist())

        for track_id in city_tracks:
            track_dir = city_dir / track_id
            track_df = city_df[city_df["track_id"] == track_id].copy()
            _write_track_bundle(track_df, track_dir, builder)

    print(f"Wrote city hierarchy under: {city_root}")


if __name__ == "__main__":
    main()