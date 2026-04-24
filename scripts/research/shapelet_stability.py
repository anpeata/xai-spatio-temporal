from __future__ import annotations

import json
import math
import os
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

os.environ.setdefault("OMP_NUM_THREADS", "1")


@dataclass
class SpeedHeuristicConfig:
    max_eval_samples: int
    silhouette_sample_size: int
    n_candidates: int
    n_shapelets: int
    n_seeds: int


def z_norm_1d(values: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    mu = arr.mean()
    sd = arr.std(ddof=0)
    return (arr - mu) / (sd + eps)


def min_distance_to_shapelet(ts: np.ndarray, shapelet: np.ndarray, z_norm_windows: bool = True) -> float:
    ts = np.asarray(ts, dtype=float)
    s = np.asarray(shapelet, dtype=float)
    length = int(s.shape[0])
    if length > ts.shape[0]:
        raise ValueError("Shapelet is longer than series")

    windows = np.lib.stride_tricks.sliding_window_view(ts, window_shape=length)

    if z_norm_windows:
        w_mu = windows.mean(axis=1, keepdims=True)
        w_sd = windows.std(axis=1, ddof=0, keepdims=True)
        windows = (windows - w_mu) / (w_sd + 1e-8)
        s = z_norm_1d(s)

    d2 = ((windows - s) ** 2).sum(axis=1)
    return float(np.sqrt(d2.min()))


def extract_random_shapelets(
    x: np.ndarray,
    lengths: Sequence[int],
    n_candidates: int,
    seed: int,
) -> List[np.ndarray]:
    rng = np.random.default_rng(seed)
    n_samples, t = x.shape
    candidates: List[np.ndarray] = []

    for _ in range(int(n_candidates)):
        length = int(rng.choice(lengths))
        row = int(rng.integers(0, n_samples))
        start = int(rng.integers(0, max(1, t - length + 1)))
        candidates.append(np.asarray(x[row, start : start + length], dtype=float).copy())
    return candidates


def compute_shapelet_distances(x: np.ndarray, shapelets: Sequence[np.ndarray]) -> np.ndarray:
    n_samples = x.shape[0]
    n_shapelets = len(shapelets)
    out = np.zeros((n_samples, n_shapelets), dtype=float)
    for i in range(n_samples):
        for j, shapelet in enumerate(shapelets):
            out[i, j] = min_distance_to_shapelet(x[i], shapelet, z_norm_windows=True)
    return out


def pairwise_jaccard(sets: Sequence[set[int]]) -> float:
    vals: List[float] = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            a = sets[i]
            b = sets[j]
            union = a | b
            inter = a & b
            vals.append(float(len(inter) / len(union)) if union else 0.0)
    return float(np.mean(vals)) if vals else 0.0


def search_best_k(
    x_view: np.ndarray,
    k_grid: Sequence[int],
    silhouette_sample_size: int,
) -> Dict[str, float | int | pd.DataFrame]:
    rows: List[Dict[str, float | int]] = []

    for k in k_grid:
        sil_values: List[float] = []
        labels_by_seed: List[np.ndarray] = []

        for seed in (0, 1, 2):
            km = KMeans(n_clusters=int(k), random_state=int(seed), n_init=12)
            labels = km.fit_predict(x_view)
            labels_by_seed.append(labels)
            sil = silhouette_score(
                x_view,
                labels,
                sample_size=min(silhouette_sample_size, x_view.shape[0]),
            )
            sil_values.append(float(sil))

        pairwise_ari: List[float] = []
        for i in range(len(labels_by_seed)):
            for j in range(i + 1, len(labels_by_seed)):
                pairwise_ari.append(float(adjusted_rand_score(labels_by_seed[i], labels_by_seed[j])))

        stability_ari = float(np.mean(pairwise_ari)) if pairwise_ari else 0.0
        silhouette_mean = float(np.mean(sil_values))
        silhouette_std = float(np.std(sil_values, ddof=0))
        composite_score = silhouette_mean + 0.5 * stability_ari

        rows.append(
            {
                "k": int(k),
                "silhouette": silhouette_mean,
                "silhouette_std": silhouette_std,
                "stability_ari": stability_ari,
                "composite_score": float(composite_score),
            }
        )

    table = pd.DataFrame(rows).sort_values(
        ["composite_score", "silhouette", "stability_ari", "k"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    best = table.iloc[0].to_dict()
    best["search_table"] = table
    return best


def evaluate_dataset_stability(
    dataset_name: str,
    x_raw: np.ndarray,
    lengths: Sequence[int],
    k_grid: Sequence[int],
    config: SpeedHeuristicConfig,
) -> Dict[str, float | int | str]:
    started_at = time.perf_counter()
    rng = np.random.default_rng(42)

    x_raw = np.asarray(x_raw, dtype=float)
    x_raw = np.nan_to_num(x_raw, copy=False)

    sample_count = min(config.max_eval_samples, x_raw.shape[0])
    if sample_count < x_raw.shape[0]:
        idx = rng.choice(x_raw.shape[0], sample_count, replace=False)
        x_eval = x_raw[idx]
    else:
        x_eval = x_raw

    scaler = StandardScaler()
    x_eval = scaler.fit_transform(x_eval)

    raw_search = search_best_k(x_eval, k_grid, config.silhouette_sample_size)
    raw_best_k = int(raw_search["k"])
    raw_best_silhouette = float(raw_search["silhouette"])
    raw_best_stability = float(raw_search["stability_ari"])

    top_features_by_seed: List[set[int]] = []
    cv_fidelities: List[float] = []
    shapelet_best_ks: List[int] = []
    shapelet_best_silhouettes: List[float] = []
    shapelet_best_stabilities: List[float] = []

    for seed in range(config.n_seeds):
        candidates = extract_random_shapelets(
            x_eval,
            lengths=lengths,
            n_candidates=config.n_candidates,
            seed=seed,
        )

        dispersions: List[float] = []
        for candidate in candidates:
            d = compute_shapelet_distances(x_eval, [candidate]).ravel()
            dispersions.append(float(np.std(d)))

        top_idx = np.argsort(dispersions)[::-1][: config.n_shapelets]
        selected = [candidates[int(i)] for i in top_idx]
        x_shapelet = StandardScaler().fit_transform(compute_shapelet_distances(x_eval, selected))

        shapelet_search = search_best_k(x_shapelet, k_grid, config.silhouette_sample_size)
        shapelet_best_ks.append(int(shapelet_search["k"]))
        shapelet_best_silhouettes.append(float(shapelet_search["silhouette"]))
        shapelet_best_stabilities.append(float(shapelet_search["stability_ari"]))

        km = KMeans(n_clusters=int(shapelet_search["k"]), random_state=seed, n_init=12)
        labels = km.fit_predict(x_shapelet)

        surrogate = DecisionTreeClassifier(max_depth=3, min_samples_leaf=8, random_state=seed)
        surrogate.fit(x_shapelet, labels)

        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed)
        cv_fidelity = cross_val_score(surrogate, x_shapelet, labels, cv=cv, scoring="accuracy").mean()
        cv_fidelities.append(float(cv_fidelity))

        top5 = set(int(i) for i in np.argsort(surrogate.feature_importances_)[::-1][:5])
        top_features_by_seed.append(top5)

    counts: Dict[int, int] = {}
    for feature_set in top_features_by_seed:
        for f in feature_set:
            counts[f] = counts.get(f, 0) + 1

    overlap_ratio = max(counts.values()) / config.n_seeds if counts else 0.0
    jaccard_mean = pairwise_jaccard(top_features_by_seed)
    fid_mean = float(np.mean(cv_fidelities))
    fid_std = float(np.std(cv_fidelities, ddof=0))
    fid_cv = float(fid_std / fid_mean) if fid_mean > 0 else 0.0
    shapelet_best_silhouette = float(np.mean(shapelet_best_silhouettes)) if shapelet_best_silhouettes else 0.0
    shapelet_best_stability = float(np.mean(shapelet_best_stabilities)) if shapelet_best_stabilities else 0.0
    shapelet_best_k = int(Counter(shapelet_best_ks).most_common(1)[0][0]) if shapelet_best_ks else raw_best_k
    silhouette_delta_pct = float(
        100.0 * (shapelet_best_silhouette - raw_best_silhouette) / raw_best_silhouette
    ) if raw_best_silhouette > 0 else 0.0
    runtime_seconds = float(time.perf_counter() - started_at)

    return {
        "dataset": dataset_name,
        "n_samples_raw": int(x_raw.shape[0]),
        "n_samples_eval": int(x_eval.shape[0]),
        "n_features": int(x_raw.shape[1]),
        "raw_best_k": int(raw_best_k),
        "raw_best_silhouette": raw_best_silhouette,
        "raw_best_stability_ari": raw_best_stability,
        "shapelet_best_k": int(shapelet_best_k),
        "shapelet_best_silhouette": shapelet_best_silhouette,
        "shapelet_best_stability_ari": shapelet_best_stability,
        "shapelet_silhouette_delta_pct": silhouette_delta_pct,
        "best_k": int(raw_best_k),
        "seeds": int(config.n_seeds),
        "fidelity_mean": fid_mean,
        "fidelity_std": fid_std,
        "fidelity_cv": fid_cv,
        "feature_overlap_ratio": float(overlap_ratio),
        "feature_jaccard_mean": float(jaccard_mean),
        "direction_c_reduction_pct": float(100.0 * (1.0 - x_eval.shape[0] / x_raw.shape[0])),
        "runtime_seconds": runtime_seconds,
        "runtime_over_15min": bool(runtime_seconds >= 900.0),
    }


def load_ecg_dataset(root: Path, dataset_name: str) -> np.ndarray:
    train_path = root / dataset_name / f"{dataset_name}_TRAIN.tsv"
    test_path = root / dataset_name / f"{dataset_name}_TEST.tsv"
    train_df = pd.read_csv(train_path, sep="\t", header=None)
    test_df = pd.read_csv(test_path, sep="\t", header=None)
    full = pd.concat([train_df, test_df], ignore_index=True)
    return full.iloc[:, 1:].to_numpy(dtype=float)


def load_picoclimatic(repo_root: Path) -> np.ndarray:
    import sys

    sys.path.insert(0, str(repo_root / "scripts" / "data"))
    from generate_picoclimate_data import generate_dataset

    outdir = repo_root / "data" / "picoclimate_test"
    outdir.mkdir(parents=True, exist_ok=True)
    _, win_path, _, _ = generate_dataset(
        outdir=outdir,
        seed=42,
        city="Nantes",
        n_locations=20,
        days=45,
    )
    win = pd.read_csv(win_path)
    slot_cols = [c for c in win.columns if "__slot_" in c]
    return win[slot_cols].to_numpy(dtype=float)


def load_roma_temporal(repo_root: Path, nrows: int = 450_000) -> np.ndarray:
    raw_path = repo_root / "data" / "roma-taxi" / "extracted" / "taxi_february.txt"
    df = pd.read_csv(
        raw_path,
        sep=";",
        header=None,
        names=["driver_id", "timestamp", "point"],
        nrows=nrows,
        engine="python",
    )

    coords = df["point"].str.extract(r"POINT\(([-\d\.]+)\s+([-\d\.]+)\)")
    df["lat"] = pd.to_numeric(coords[0], errors="coerce")
    df["lon"] = pd.to_numeric(coords[1], errors="coerce")
    df["dt"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["dt", "lat", "lon"]).copy()

    if df.empty:
        raise ValueError("Roma temporal loader produced zero valid rows after parsing")

    df["window_dt"] = df["dt"].dt.floor("15min")
    grouped = (
        df.groupby(["driver_id", "window_dt"], as_index=False)
        .size()
        .rename(columns={"size": "n_points"})
    )

    hour = grouped["window_dt"].dt.hour + grouped["window_dt"].dt.minute / 60.0
    dow = grouped["window_dt"].dt.weekday
    day_fraction = hour / 24.0

    feat = pd.DataFrame(
        {
            "sin_time": np.sin(2.0 * math.pi * day_fraction),
            "cos_time": np.cos(2.0 * math.pi * day_fraction),
            "sin_hour": np.sin(2.0 * math.pi * grouped["window_dt"].dt.hour / 24.0),
            "cos_hour": np.cos(2.0 * math.pi * grouped["window_dt"].dt.hour / 24.0),
            "sin_dow": np.sin(2.0 * math.pi * dow / 7.0),
            "cos_dow": np.cos(2.0 * math.pi * dow / 7.0),
            "is_weekend": (dow >= 5).astype(float),
            "n_points": grouped["n_points"].astype(float),
        }
    )
    return feat.to_numpy(dtype=float)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    ucr_root_candidates = [
        (repo_root / "data" / "UCRArchive_2018").resolve(),
        (repo_root / "data" / "UCRArchive_2018" / "UCRArchive_2018").resolve(),
    ]
    ucr_root = next((p for p in ucr_root_candidates if p.exists()), ucr_root_candidates[0])

    config = SpeedHeuristicConfig(
        max_eval_samples=2500,
        silhouette_sample_size=1200,
        n_candidates=80,
        n_shapelets=12,
        n_seeds=6,
    )

    datasets: List[Tuple[str, np.ndarray, Sequence[int], Sequence[int]]] = [
        ("picoclimatic_synthetic", load_picoclimatic(repo_root), (8, 12, 16), (2, 3, 4, 5)),
        ("ecg200", load_ecg_dataset(ucr_root, "ECG200"), (5, 10, 15, 20), (2, 3, 4, 5)),
        ("ecg5000", load_ecg_dataset(ucr_root, "ECG5000"), (5, 10, 15, 20, 25), (2, 3, 4, 5, 6)),
        ("roma_temporal", load_roma_temporal(repo_root), (2, 3, 4), (2, 3, 4, 5, 6)),
    ]

    rows: List[Dict[str, float | int | str]] = []
    for name, x_data, lengths, k_grid in datasets:
        print(f"Running stability for {name}: shape={x_data.shape}")
        row = evaluate_dataset_stability(name, x_data, lengths, k_grid, config)
        rows.append(row)
        print(
            f"  raw silhouette={row['raw_best_silhouette']:.4f}, "
            f"shapelet silhouette={row['shapelet_best_silhouette']:.4f}, "
            f"delta={row['shapelet_silhouette_delta_pct']:.1f}%"
        )
        print(
            f"  runtime={row['runtime_seconds'] / 60.0:.1f} min"
            + (" [warning: over 15 min]" if row["runtime_over_15min"] else "")
        )

    out_dir = repo_root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows).sort_values("dataset").reset_index(drop=True)
    csv_path = out_dir / "stability_cross_dataset.csv"
    json_path = out_dir / "stability_cross_dataset.json"

    df.to_csv(csv_path, index=False)
    payload = {
        "speed_heuristic_config": asdict(config),
        "rows": df.to_dict(orient="records"),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("\nSummary table:")
    print(df.to_string(index=False))
    print(f"\nWrote {csv_path}")
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()
