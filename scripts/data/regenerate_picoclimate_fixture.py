"""Regenerate the Picoclimate test fixture from the track-based CSV.

The script trims each track to a reproducible 100-150 loc_id range, rebuilds
`window_features.csv`, and optionally exports per-variable day/slot slices.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd


VALUE_COLUMNS: Sequence[str] = (
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
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate the Picoclimate test fixture")
    parser.add_argument("--data-dir", type=Path, default=Path("data/picoclimate_test"))
    parser.add_argument("--seed", type=int, default=20260529)
    parser.add_argument("--min-loc", type=int, default=100)
    parser.add_argument("--max-loc", type=int, default=150)
    parser.add_argument(
        "--export-variable-slices",
        action="store_true",
        help="Write one CSV per variable and day/slot under variable_slices/",
    )
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


def _trim_tracks(raw: pd.DataFrame, min_loc: int, max_loc: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    trimmed_groups: List[pd.DataFrame] = []

    for track_id, group in raw.groupby("track_id", sort=False):
        ordered = group.sort_values(["loc_index", "date", "slot_index", "time_slot"], kind="mergesort")
        unique_locs = ordered[["loc_index", "loc_id"]].drop_duplicates(subset=["loc_index"], keep="first")
        current_len = len(unique_locs)
        if current_len == 0:
            continue
        target_len = int(rng.integers(min_loc, max_loc + 1))
        target_len = min(target_len, current_len)
        keep_indices = set(unique_locs.iloc[:target_len]["loc_index"].tolist())
        trimmed_groups.append(ordered[ordered["loc_index"].isin(keep_indices)].copy())

    if not trimmed_groups:
        raise RuntimeError("No tracks remained after trimming")

    trimmed = pd.concat(trimmed_groups, ignore_index=True)
    trimmed["timestamp"] = pd.to_datetime(trimmed["timestamp"], utc=True, errors="coerce")
    trimmed = trimmed.sort_values(["track_id", "date", "slot_index", "loc_index"], kind="mergesort").reset_index(drop=True)
    return trimmed


def _export_variable_slices(raw: pd.DataFrame, data_dir: Path) -> Dict[str, int]:
    slice_root = data_dir / "variable_slices"
    slice_root.mkdir(parents=True, exist_ok=True)

    counts: Dict[str, int] = {}
    base_cols = ["track_id", "city", "date", "time_slot", "slot_index", "loc_id", "loc_index", "timestamp"]
    grouped = list(raw.groupby(["date", "time_slot", "slot_index"], sort=True))

    for variable in VALUE_COLUMNS:
        variable_dir = slice_root / variable
        variable_dir.mkdir(parents=True, exist_ok=True)
        file_count = 0
        for (date, time_slot, slot_index), group in grouped:
            slice_df = group[base_cols + [variable]].copy().rename(columns={variable: "value"})
            file_name = f"day_{date}_slot_{int(slot_index)}_{time_slot}.csv"
            slice_df.to_csv(variable_dir / file_name, index=False)
            file_count += 1
        counts[variable] = file_count

    return counts


def _write_metadata(data_dir: Path, raw: pd.DataFrame, win: pd.DataFrame, slice_counts: Dict[str, int], seed: int, min_loc: int, max_loc: int) -> None:
    track_lengths = raw.groupby("track_id")["loc_index"].max().add(1)
    days_per_track = raw.groupby("track_id")["date"].nunique()

    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "generation_notes": {
            "sequence_model": "track-based with variable-length loc_id sequences",
            "loc_id_range_per_track": [min_loc, max_loc],
            "slots_per_day": "0-4 available recordings/day (missing days and missing slots allowed)",
            "cities": {"Nantes": 10, "Montpellier": 6},
            "slice_layout": "variable_slices/<variable>/day_<YYYY-MM-DD>_slot_<slot>.csv",
        },
        "parameters": {
            "seed": seed,
            "min_loc": min_loc,
            "max_loc": max_loc,
            "n_tracks_nantes": 10,
            "n_tracks_montpellier": 6,
        },
        "tables": {
            "tracks_measurements.csv": {
                "rows": int(raw.shape[0]),
                "columns": int(raw.shape[1]),
                "primary_key": ["track_id", "date", "time_slot", "loc_id"],
            },
            "window_features.csv": {
                "rows": int(win.shape[0]),
                "columns": int(win.shape[1]),
                "primary_key": ["track_id", "date"],
            },
        },
        "track_length_summary": {
            "min": int(track_lengths.min()),
            "max": int(track_lengths.max()),
            "mean": float(track_lengths.mean()),
        },
        "days_per_track_summary": {
            "min": int(days_per_track.min()),
            "max": int(days_per_track.max()),
            "mean": float(days_per_track.mean()),
        },
        "slice_counts": slice_counts,
        "representation_guidance": {
            "track_sequence": "Treat loc_index order as pseudo-time along each track.",
            "windowing": "Aggregate by track_id and date to build daily windows.",
            "slice_layout": "Use variable_slices/<variable>/day_<YYYY-MM-DD>_slot_<slot>.csv for one-variable daily exports.",
        },
    }

    (data_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    fields = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "files": {
            "tracks_measurements.csv": {
                "description": "Master track table with one row per track x date x slot x loc_id.",
                "primary_key": ["track_id", "date", "time_slot", "loc_id"],
                "column_count": int(raw.shape[1]),
                "columns": {
                    "track_id": "Synthetic track identifier.",
                    "city": "Associated city.",
                    "date": "Calendar date for the slot sample.",
                    "time_slot": "One of morning/noon/evening/night.",
                    "slot_index": "0..3 slot order within day.",
                    "loc_id": "Location identifier within a track.",
                    "loc_index": "Ordering within the track (pseudo-time).",
                    "timestamp": "UTC timestamp for the slot and loc_index ordering.",
                    "true_regime": "Latent regime label for evaluation.",
                },
            },
            "window_features.csv": {
                "description": "One row per track x date with flattened slot columns and summary statistics.",
                "primary_key": ["track_id", "date"],
                "column_count": int(win.shape[1]),
                "patterns": {
                    "<variable>__slot_1..4": "Flattened daily profile over observed slots (NaN when missing).",
                    "<variable>__mean": "Daily mean over observed slots.",
                    "<variable>__std": "Daily standard deviation over observed slots.",
                    "<variable>__trend": "Linear trend over slot index 0..3.",
                },
                "core_columns": {
                    "track_id": "Synthetic track identifier.",
                    "date": "Calendar date.",
                    "city": "Associated city.",
                    "time_slot": "Most frequent recorded slot label for the day.",
                    "n_points": "Observed number of rows contributing to the daily window.",
                    "present_fraction": "Observed fraction of non-missing measured cells.",
                    "true_regime": "Majority regime among observed rows.",
                },
            },
            "variable_slices": {
                "description": "One CSV per variable and day/slot slice.",
                "pattern": "variable_slices/<variable>/day_<YYYY-MM-DD>_slot_<slot>.csv",
                "columns": {
                    "track_id": "Synthetic track identifier.",
                    "city": "Associated city.",
                    "date": "Calendar date.",
                    "time_slot": "One of morning/noon/evening/night.",
                    "slot_index": "0..3 slot order within day.",
                    "loc_id": "Location identifier within a track.",
                    "loc_index": "Ordering within the track.",
                    "timestamp": "UTC timestamp for the slice.",
                    "value": "Selected variable value.",
                },
            },
        },
    }

    (data_dir / "csv_fields_explained.json").write_text(json.dumps(fields, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    args = _parse_args()
    data_dir = args.data_dir
    raw_path = data_dir / "tracks_measurements.csv"
    if not raw_path.exists():
        raise SystemExit(f"Missing input file: {raw_path}")

    raw = pd.read_csv(raw_path, low_memory=False)
    required = {"track_id", "city", "date", "time_slot", "slot_index", "loc_id", "loc_index", "timestamp"}
    missing = required - set(raw.columns)
    if missing:
        raise SystemExit(f"tracks_measurements.csv is missing required columns: {sorted(missing)}")

    trimmed = _trim_tracks(raw, args.min_loc, args.max_loc, args.seed)
    trimmed.to_csv(raw_path, index=False)

    repo_root = data_dir.parent.parent
    builder = _load_window_builder(repo_root)
    window = builder._build_window_features(trimmed)
    win_path = data_dir / "window_features.csv"
    window.to_csv(win_path, index=False)

    slice_counts: Dict[str, int] = {}
    if args.export_variable_slices:
        slice_counts = _export_variable_slices(trimmed, data_dir)

    _write_metadata(data_dir, trimmed, window, slice_counts, args.seed, args.min_loc, args.max_loc)

    print(f"Wrote trimmed tracks: {raw_path}")
    print(f"Wrote window features: {win_path}")
    if args.export_variable_slices:
        print(f"Wrote variable slices under: {data_dir / 'variable_slices'}")


if __name__ == "__main__":
    main()