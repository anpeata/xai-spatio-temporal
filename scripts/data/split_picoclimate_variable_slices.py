"""Split Picoclimate tracks into a city/date/slot/track hierarchy.

The source of truth for this split is data/picoclimate_test/tracks_measurements.csv.
The script writes one wide matrix per track under data/picoclimate_test/cities/
with rows as variables and columns as location_id values.
"""

from __future__ import annotations

import argparse
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

ID_COLUMNS = ["track_id", "city", "date", "time_slot", "slot_index", "loc_id", "loc_index", "timestamp"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split Picoclimate variable slices into city/track folders")
    parser.add_argument("--data-dir", type=Path, default=Path("data/picoclimate_test"))
    return parser.parse_args()


def _load_tracks(data_dir: Path) -> pd.DataFrame:
    tracks_path = data_dir / "tracks_measurements.csv"
    if not tracks_path.exists():
        raise SystemExit(f"Missing input file: {tracks_path}")

    raw = pd.read_csv(tracks_path, low_memory=False)
    missing = set(ID_COLUMNS) - set(raw.columns)
    if missing:
        raise SystemExit(f"tracks_measurements.csv is missing required columns: {sorted(missing)}")

    raw = raw.sort_values(["city", "date", "slot_index", "track_id", "loc_index"], kind="mergesort").reset_index(drop=True)
    return raw


def _write_track_matrix(track_df: pd.DataFrame, track_csv: Path) -> None:
    track_csv.parent.mkdir(parents=True, exist_ok=True)

    numeric = track_df.copy()
    for column in VALUE_COLUMNS:
        numeric[column] = pd.to_numeric(numeric[column], errors="coerce")
    numeric["loc_index"] = pd.to_numeric(numeric["loc_index"], errors="coerce")

    loc_order = numeric[["loc_index", "loc_id"]].drop_duplicates(subset=["loc_index"], keep="first").sort_values("loc_index", kind="mergesort")
    loc_ids = loc_order["loc_id"].tolist()

    matrix = numeric[["loc_id"] + VALUE_COLUMNS].copy().set_index("loc_id")
    matrix = matrix.reindex(loc_ids)
    matrix = matrix.T
    matrix.index.name = "variable"
    matrix.reset_index().to_csv(track_csv, index=False)


def main() -> None:
    args = _parse_args()
    data_dir = args.data_dir
    wide = _load_tracks(data_dir)

    city_root = data_dir / "cities"
    city_root.mkdir(parents=True, exist_ok=True)

    for (city, date, time_slot, track_id), track_df in wide.groupby(["city", "date", "time_slot", "track_id"], sort=True):
        _write_track_matrix(track_df, city_root / city / date / time_slot / f"{track_id}.csv")

    print(f"Wrote city hierarchy under: {city_root}")


if __name__ == "__main__":
    main()