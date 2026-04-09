"""Synthetic spatio-temporal dataset generator aligned with internship notes.

Design assumptions from latest meeting
- Exactly 4 data points per day (fixed daily time slots).
- Each data point contains ~23 measured variables.
- Measurements follow a linear combination of spatial and temporal components.
- Missing values are realistic and include both cell-level and block-level dropouts.

Outputs
- raw_measurements.csv      : one row per (location, day, time_slot)
- window_features.csv       : one row per (location, day) with clustering representations
- metadata.json             : generation metadata and variable descriptions
- csv_fields_explained.json : compact dictionary of both tables
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class VariableSpec:
    name: str
    unit: str
    description: str
    min_value: float
    max_value: float


MEASURED_VARS: List[VariableSpec] = [
    VariableSpec("air_temp_c", "degC", "Near-surface air temperature", -15.0, 50.0),
    VariableSpec("rel_humidity_pct", "pct", "Relative humidity", 5.0, 100.0),
    VariableSpec("wind_speed_ms", "m_s", "Wind speed", 0.0, 25.0),
    VariableSpec("wind_dir_deg", "deg", "Wind direction", 0.0, 360.0),
    VariableSpec("pressure_hpa", "hPa", "Air pressure", 960.0, 1045.0),
    VariableSpec("precipitation_mm", "mm", "Precipitation amount per slot", 0.0, 50.0),
    VariableSpec("solar_wm2", "W_m2", "Shortwave solar irradiance", 0.0, 1200.0),
    VariableSpec("longwave_wm2", "W_m2", "Longwave radiation", 200.0, 700.0),
    VariableSpec("surface_temp_c", "degC", "Surface temperature", -10.0, 75.0),
    VariableSpec("soil_moisture_pct", "pct", "Top-soil moisture", 1.0, 70.0),
    VariableSpec("ndvi", "index", "Vegetation greenness proxy", 0.0, 1.0),
    VariableSpec("pm25_ugm3", "ug_m3", "PM2.5 concentration", 0.0, 220.0),
    VariableSpec("pm10_ugm3", "ug_m3", "PM10 concentration", 0.0, 320.0),
    VariableSpec("co2_ppm", "ppm", "CO2 concentration", 350.0, 3000.0),
    VariableSpec("no2_ppb", "ppb", "NO2 concentration", 0.0, 220.0),
    VariableSpec("o3_ppb", "ppb", "O3 concentration", 0.0, 180.0),
    VariableSpec("noise_db", "dB", "Ambient sound pressure level", 20.0, 110.0),
    VariableSpec("traffic_index", "index", "Traffic intensity proxy", 0.0, 1.0),
    VariableSpec("pedestrian_index", "index", "Pedestrian activity proxy", 0.0, 1.0),
    VariableSpec("sky_view_factor", "index", "Visible sky fraction", 0.05, 1.0),
    VariableSpec("impervious_fraction", "index", "Impervious surface fraction", 0.0, 1.0),
    VariableSpec("water_proximity", "index", "Relative proximity to water body", 0.0, 1.0),
    VariableSpec("heat_index_c", "degC", "Apparent temperature proxy", -20.0, 65.0),
]

SLOT_HOURS = [6, 12, 18, 23]
SLOT_NAMES = ["morning", "noon", "evening", "night"]


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _city_anchor(city: str) -> Tuple[float, float]:
    anchors = {
        "Nantes": (47.2184, -1.5536),
        "Montpellier": (43.6119, 3.8772),
    }
    if city not in anchors:
        raise ValueError(f"Unsupported city: {city}")
    return anchors[city]


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _wrap_deg(x: np.ndarray) -> np.ndarray:
    return (x % 360.0 + 360.0) % 360.0


def _build_locations(rng: np.random.Generator, n_locations: int, cities: List[str]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for idx in range(n_locations):
        city = cities[idx % len(cities)]
        lat0, lon0 = _city_anchor(city)

        # Pseudo local offsets around city center (about +/-5 km).
        dlat = rng.normal(0.0, 0.028)
        dlon = rng.normal(0.0, 0.038)

        lat = lat0 + dlat
        lon = lon0 + dlon

        # Spatial latent factors used by linear model.
        dist_center = float(np.hypot(dlat * 111_000.0, dlon * 111_000.0 * np.cos(np.deg2rad(lat0))))
        urbanity = float(_sigmoid(np.array([(2600.0 - dist_center) / 900.0]))[0])
        vegetation = float(np.clip(0.2 + 0.6 * (1.0 - urbanity) + rng.normal(0.0, 0.08), 0.0, 1.0))
        water = float(np.clip(0.3 + 0.4 * np.sin(dlon * 35.0) + rng.normal(0.0, 0.09), 0.0, 1.0))

        elevation_m = float(np.clip(30.0 + 45.0 * (1.0 - water) + rng.normal(0.0, 8.0), 5.0, 180.0))
        svf = float(np.clip(0.3 + 0.5 * (1.0 - urbanity) + rng.normal(0.0, 0.08), 0.05, 1.0))
        impervious = float(np.clip(0.15 + 0.75 * urbanity - 0.2 * vegetation, 0.0, 1.0))

        rows.append(
            {
                "location_id": f"loc_{idx:03d}",
                "city": city,
                "lat": lat,
                "lon": lon,
                "elevation_m": elevation_m,
                "spatial_urbanity": urbanity,
                "spatial_vegetation": vegetation,
                "spatial_water": water,
                "sky_view_factor": svf,
                "impervious_fraction": impervious,
                "water_proximity": water,
            }
        )

    return pd.DataFrame(rows)


def _temporal_features(ts: pd.Timestamp) -> Dict[str, float]:
    hour = float(ts.hour)
    doy = float(ts.dayofyear)
    day_cycle = 2.0 * math.pi * hour / 24.0
    year_cycle = 2.0 * math.pi * doy / 365.25
    return {
        "hour": hour,
        "day_of_year": doy,
        "temp_diurnal": math.sin(day_cycle - math.pi / 3.0),
        "radiation_diurnal": max(0.0, math.sin(day_cycle - math.pi / 2.0)),
        "seasonal": math.cos(year_cycle - 0.8),
        "weekend": float(ts.weekday() >= 5),
    }


def _linear_components(
    rng: np.random.Generator,
    n_vars: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    # Coefficients for X = bias + A_s * s + A_t * t + c * (s1*t1) + eps
    bias = rng.normal(0.0, 1.0, size=n_vars)
    a_s = rng.normal(0.0, 1.0, size=(n_vars, 3))
    a_t = rng.normal(0.0, 1.0, size=(n_vars, 4))
    inter = rng.normal(0.0, 0.7, size=n_vars)
    noise = rng.uniform(0.15, 0.55, size=n_vars)
    return bias, a_s, a_t, inter, noise


def _simulate_measurements(
    rng: np.random.Generator,
    locations: pd.DataFrame,
    start_date: datetime,
    days: int,
) -> pd.DataFrame:
    n_vars = len(MEASURED_VARS)
    bias, a_s, a_t, inter, noise_sigma = _linear_components(rng, n_vars)

    # Scale/offset so each variable lands in realistic range.
    mins = np.array([v.min_value for v in MEASURED_VARS], dtype=float)
    maxs = np.array([v.max_value for v in MEASURED_VARS], dtype=float)
    mid = 0.5 * (mins + maxs)
    span = (maxs - mins)

    rows: List[Dict[str, Any]] = []

    for _, loc in locations.iterrows():
        spatial = np.array(
            [
                float(loc["spatial_urbanity"]),
                float(loc["spatial_vegetation"]),
                float(loc["spatial_water"]),
            ],
            dtype=float,
        )

        for day_idx in range(days):
            base_day = pd.Timestamp(start_date + timedelta(days=day_idx))
            for slot_idx, (slot_name, slot_hour) in enumerate(zip(SLOT_NAMES, SLOT_HOURS)):
                ts = base_day + pd.Timedelta(hours=slot_hour)
                tf = _temporal_features(ts)

                temporal = np.array(
                    [
                        tf["temp_diurnal"],
                        tf["radiation_diurnal"],
                        tf["seasonal"],
                        tf["weekend"],
                    ],
                    dtype=float,
                )

                z = (
                    bias
                    + a_s @ spatial
                    + a_t @ temporal
                    + inter * (spatial[0] * temporal[0])
                    + rng.normal(0.0, noise_sigma)
                )

                # Map latent z to bounded variables with sigmoid squashing.
                scaled = mid + span * (1.6 * _sigmoid(z) - 0.8)
                values = np.clip(scaled, mins, maxs)

                # Domain coupling tweaks after linear core.
                var_idx = {v.name: i for i, v in enumerate(MEASURED_VARS)}

                solar = values[var_idx["solar_wm2"]]
                rh = values[var_idx["rel_humidity_pct"]]
                air_t = values[var_idx["air_temp_c"]]
                wind = values[var_idx["wind_speed_ms"]]
                traffic = values[var_idx["traffic_index"]]
                impervious = float(loc["impervious_fraction"])
                water = float(loc["water_proximity"])
                veg = float(loc["spatial_vegetation"])

                values[var_idx["surface_temp_c"]] = np.clip(
                    air_t + 0.007 * solar + 5.0 * impervious - 3.5 * veg + rng.normal(0.0, 1.3),
                    MEASURED_VARS[var_idx["surface_temp_c"]].min_value,
                    MEASURED_VARS[var_idx["surface_temp_c"]].max_value,
                )

                values[var_idx["heat_index_c"]] = np.clip(
                    air_t + 0.06 * (rh - 45.0) - 0.45 * wind + 0.004 * solar,
                    MEASURED_VARS[var_idx["heat_index_c"]].min_value,
                    MEASURED_VARS[var_idx["heat_index_c"]].max_value,
                )

                values[var_idx["pm25_ugm3"]] = np.clip(
                    values[var_idx["pm25_ugm3"]] + 20.0 * traffic - 8.0 * wind - 6.0 * water,
                    MEASURED_VARS[var_idx["pm25_ugm3"]].min_value,
                    MEASURED_VARS[var_idx["pm25_ugm3"]].max_value,
                )

                values[var_idx["pm10_ugm3"]] = np.clip(
                    1.35 * values[var_idx["pm25_ugm3"]] + rng.normal(0.0, 3.0),
                    MEASURED_VARS[var_idx["pm10_ugm3"]].min_value,
                    MEASURED_VARS[var_idx["pm10_ugm3"]].max_value,
                )

                values[var_idx["co2_ppm"]] = np.clip(
                    values[var_idx["co2_ppm"]] + 330.0 * traffic - 15.0 * wind,
                    MEASURED_VARS[var_idx["co2_ppm"]].min_value,
                    MEASURED_VARS[var_idx["co2_ppm"]].max_value,
                )

                values[var_idx["noise_db"]] = np.clip(
                    values[var_idx["noise_db"]] + 17.0 * traffic + 4.0 * tf["weekend"],
                    MEASURED_VARS[var_idx["noise_db"]].min_value,
                    MEASURED_VARS[var_idx["noise_db"]].max_value,
                )

                values[var_idx["wind_dir_deg"]] = _wrap_deg(np.array([values[var_idx["wind_dir_deg"]]]))[0]

                # Simple latent regime label for evaluation.
                if traffic > 0.65 and tf["hour"] in (12.0, 18.0):
                    regime = "traffic_peak"
                elif veg > 0.55 and water > 0.45:
                    regime = "green_humid"
                elif impervious > 0.62 and air_t > 26.0:
                    regime = "urban_heat"
                else:
                    regime = "mixed_background"

                row: Dict[str, Any] = {
                    "timestamp": ts.isoformat(),
                    "date": ts.date().isoformat(),
                    "day_index": day_idx,
                    "time_slot": slot_name,
                    "slot_index": slot_idx,
                    "location_id": loc["location_id"],
                    "city": loc["city"],
                    "lat": float(loc["lat"]),
                    "lon": float(loc["lon"]),
                    "elevation_m": float(loc["elevation_m"]),
                    "hour": tf["hour"],
                    "day_of_year": tf["day_of_year"],
                    "true_regime": regime,
                }

                for i, spec in enumerate(MEASURED_VARS):
                    row[spec.name] = float(values[i])

                # Ensure static spatial values are aligned with measured list.
                row["sky_view_factor"] = float(loc["sky_view_factor"])
                row["impervious_fraction"] = float(loc["impervious_fraction"])
                row["water_proximity"] = float(loc["water_proximity"])
                row["ndvi"] = float(np.clip(0.15 + 0.7 * float(loc["spatial_vegetation"]) + rng.normal(0.0, 0.03), 0.0, 1.0))

                rows.append(row)

    raw = pd.DataFrame(rows)
    raw["timestamp"] = pd.to_datetime(raw["timestamp"], utc=True)
    raw = raw.sort_values(["location_id", "timestamp"]).reset_index(drop=True)

    # Missingness model: base + weather-sensitive + nighttime optical issues.
    measured_cols = [v.name for v in MEASURED_VARS]
    miss_base = 0.03

    precip = raw["precipitation_mm"].to_numpy()
    night = (raw["time_slot"] == "night").to_numpy()
    weather_penalty = 0.05 * (precip > 2.0).astype(float)

    miss_matrix = rng.random((len(raw), len(measured_cols)))
    miss_prob = np.full((len(raw), len(measured_cols)), miss_base, dtype=float)
    miss_prob += weather_penalty[:, None]

    for col_name in ["solar_wm2", "surface_temp_c", "ndvi"]:
        j = measured_cols.index(col_name)
        miss_prob[:, j] += 0.07 * night.astype(float)

    mask = miss_matrix < miss_prob

    # Block outages emulate partial logger/network failures.
    block_cols = [
        "pm25_ugm3",
        "pm10_ugm3",
        "co2_ppm",
        "no2_ppb",
        "o3_ppb",
        "noise_db",
        "traffic_index",
        "pedestrian_index",
    ]
    block_idx = [measured_cols.index(c) for c in block_cols]

    block_rows = rng.random(len(raw)) < 0.06
    mask[np.ix_(block_rows, block_idx)] = True

    raw.loc[:, measured_cols] = raw.loc[:, measured_cols].mask(mask)
    raw["missing_block_flag"] = block_rows.astype(int)

    # Rounded outputs improve readability and mimic instrument precision.
    for c in ["air_temp_c", "surface_temp_c", "heat_index_c"]:
        raw[c] = raw[c].round(2)
    for c in ["rel_humidity_pct", "soil_moisture_pct", "noise_db"]:
        raw[c] = raw[c].round(1)
    for c in ["wind_speed_ms", "precipitation_mm", "traffic_index", "pedestrian_index"]:
        raw[c] = raw[c].round(3)
    for c in ["co2_ppm", "pressure_hpa", "solar_wm2", "longwave_wm2"]:
        raw[c] = raw[c].round(0)

    return raw


def _trend_four_points(values: pd.Series) -> float:
    arr = values.to_numpy(dtype=float)
    x = np.arange(len(arr), dtype=float)
    ok = np.isfinite(arr)
    if ok.sum() < 2:
        return float("nan")
    x_ok = x[ok]
    y_ok = arr[ok]
    xm = x_ok.mean()
    denom = ((x_ok - xm) ** 2).sum()
    if denom <= 0:
        return float("nan")
    return float(((x_ok - xm) * (y_ok - y_ok.mean())).sum() / denom)


def _build_window_features(raw: pd.DataFrame) -> pd.DataFrame:
    measured_cols = [v.name for v in MEASURED_VARS]
    key = ["location_id", "date", "city"]

    rows: List[Dict[str, Any]] = []

    for _, g in raw.sort_values(["slot_index"]).groupby(key, sort=False):
        out: Dict[str, Any] = {
            "location_id": g["location_id"].iloc[0],
            "date": g["date"].iloc[0],
            "city": g["city"].iloc[0],
            "n_points": int(g.shape[0]),
            "present_fraction": float(g[measured_cols].notna().to_numpy().mean()),
        }

        # Representation A: flatten 4x23 into 92 dimensions.
        ordered = g.sort_values("slot_index")
        for _, row in ordered.iterrows():
            slot = int(row["slot_index"])
            for c in measured_cols:
                out[f"{c}__slot_{slot + 1}"] = row[c]

        # Representation B: summary stats over the 4 points.
        for c in measured_cols:
            out[f"{c}__mean"] = float(g[c].mean(skipna=True))
            out[f"{c}__std"] = float(g[c].std(skipna=True))
            out[f"{c}__trend"] = _trend_four_points(ordered[c])

        mode = g["true_regime"].mode(dropna=True)
        out["true_regime"] = mode.iloc[0] if not mode.empty else np.nan

        rows.append(out)

    return pd.DataFrame(rows)


def _write_metadata(outdir: Path, args: argparse.Namespace, raw: pd.DataFrame, win: pd.DataFrame) -> None:
    measured_cols = [v.name for v in MEASURED_VARS]

    metadata: Dict[str, Any] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "generation_notes": {
            "points_per_day": 4,
            "measured_variable_count": len(MEASURED_VARS),
            "model": "X = bias + A_s*s + A_t*t + c*(s1*t1) + eps",
            "spatial_latent_factors": ["urbanity", "vegetation", "water_proximity"],
            "temporal_latent_factors": ["diurnal_temperature", "diurnal_radiation", "seasonal", "weekend"],
            "missingness": "cell-level MAR + block outages",
        },
        "parameters": {
            "seed": args.seed,
            "n_locations": args.n_locations,
            "days": args.days,
            "cities": args.city.split(",") if args.city else ["Nantes", "Montpellier"],
            "slot_hours": SLOT_HOURS,
        },
        "tables": {
            "raw_measurements.csv": {
                "rows": int(raw.shape[0]),
                "columns": int(raw.shape[1]),
                "primary_key": ["timestamp", "location_id"],
            },
            "window_features.csv": {
                "rows": int(win.shape[0]),
                "columns": int(win.shape[1]),
                "primary_key": ["date", "location_id"],
            },
        },
        "measured_variables": [asdict(v) for v in MEASURED_VARS],
        "representation_guidance": {
            "flat_4x23": "Use columns ending in __slot_1..__slot_4 for direct clustering.",
            "summary": "Use __mean/__std/__trend columns for compact clustering inputs.",
            "missing_values": "Use imputation that preserves temporal ordering (per-variable, per-location).",
        },
    }

    (outdir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    fields: Dict[str, Any] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "files": {
            "raw_measurements.csv": {
                "description": "One row per location/day/slot. Exactly 4 slots per day.",
                "primary_key": ["timestamp", "location_id"],
                "column_count": int(raw.shape[1]),
                "columns": {
                    "timestamp": "UTC timestamp of the slot sample.",
                    "date": "Calendar date.",
                    "day_index": "Offset from simulation start date.",
                    "time_slot": "One of morning/noon/evening/night.",
                    "slot_index": "0..3 slot order within day.",
                    "location_id": "Synthetic location identifier.",
                    "city": "Associated city.",
                    "lat": "Latitude in decimal degrees.",
                    "lon": "Longitude in decimal degrees.",
                    "elevation_m": "Elevation in meters.",
                    "hour": "Hour-of-day feature used by temporal component.",
                    "day_of_year": "Day-of-year feature used by seasonal component.",
                    "missing_block_flag": "1 when a sensor block outage was applied.",
                    "true_regime": "Latent regime label for evaluation.",
                },
            },
            "window_features.csv": {
                "description": "Daily representations for clustering with flat and summarized encodings.",
                "primary_key": ["date", "location_id"],
                "column_count": int(win.shape[1]),
                "patterns": {
                    "<variable>__slot_1..4": "Flattened 4-point daily profile (4 x 23 representation).",
                    "<variable>__mean": "Daily mean over 4 slots.",
                    "<variable>__std": "Daily std over 4 slots.",
                    "<variable>__trend": "Linear trend over slot index 0..3.",
                },
                "core_columns": {
                    "location_id": "Synthetic location identifier.",
                    "date": "Calendar date.",
                    "city": "Associated city.",
                    "n_points": "Expected to be 4.",
                    "present_fraction": "Observed fraction of non-missing measured cells.",
                    "true_regime": "Majority regime among the 4 slots.",
                },
            },
        },
    }

    for spec in MEASURED_VARS:
        fields["files"]["raw_measurements.csv"]["columns"][spec.name] = spec.description

    (outdir / "csv_fields_explained.json").write_text(json.dumps(fields, indent=2), encoding="utf-8")


def generate_dataset(
    outdir: Path,
    seed: int,
    city: str,
    n_locations: int,
    days: int,
) -> Tuple[Path, Path, Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)

    if days <= 0:
        raise ValueError("days must be > 0")
    if n_locations <= 0:
        raise ValueError("n_locations must be > 0")

    rng = _rng(seed)
    cities = [c.strip() for c in city.split(",") if c.strip()]
    if not cities:
        cities = ["Nantes", "Montpellier"]

    start_date = datetime(2025, 9, 1, 0, 0, 0, tzinfo=timezone.utc)

    locations = _build_locations(rng, n_locations=n_locations, cities=cities)
    raw = _simulate_measurements(rng, locations=locations, start_date=start_date, days=days)
    win = _build_window_features(raw)

    raw_path = outdir / "raw_measurements.csv"
    win_path = outdir / "window_features.csv"

    raw.to_csv(raw_path, index=False)
    win.to_csv(win_path, index=False)

    args_stub = argparse.Namespace(seed=seed, n_locations=n_locations, days=days, city=city)
    _write_metadata(outdir, args_stub, raw, win)

    return (
        raw_path,
        win_path,
        outdir / "metadata.json",
        outdir / "csv_fields_explained.json",
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate 4-point-per-day synthetic spatio-temporal dataset")
    p.add_argument("--outdir", type=str, required=True, help="Output directory for CSV/JSON artifacts")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--city", type=str, default="Nantes,Montpellier", help="Comma-separated cities")
    p.add_argument("--n-locations", type=int, default=24)
    p.add_argument("--days", type=int, default=90)
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    outdir = Path(args.outdir)

    raw_path, win_path, meta_path, fields_path = generate_dataset(
        outdir=outdir,
        seed=args.seed,
        city=args.city,
        n_locations=args.n_locations,
        days=args.days,
    )

    print(f"Wrote: {raw_path}")
    print(f"Wrote: {win_path}")
    print(f"Wrote: {meta_path}")
    print(f"Wrote: {fields_path}")


if __name__ == "__main__":
    main()
