from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Any, Any, Any, Any, Any, Any, Dict, List, LiteralString, LiteralString, Sequence, Tuple

import numpy as np
import pandas as pd
from pandas import DataFrame
from pandas import DataFrame
from pandas import Series
from pandas import Series
from pandas import Series
from pandas import Series
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

try:
    import hdbscan  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    hdbscan = None

@dataclass
class SummaryConfig:
    lengths: Tuple[int, ...]
    max_rows: int
    eval_rows: int
    max_pool: int
    target_shapelets: int
    min_std: float
    corr_threshold: float
    k_min: int
    k_max: int
    top_n: int
    output_dir: Path


def parse_lengths(text: str) -> Tuple[int, ...]:
    vals: List[int] = [int(v.strip()) for v: LiteralString in text.split(",") if v.strip()]
    if not vals:
        raise ValueError("lengths must be a comma-separated list")
    return tuple(vals)


def slot_columns(columns: Sequence[str]) -> Dict[int, List[str]]:
    slot_map: Dict[int, List[str]] = {}
    for col: str in columns:
        if "__slot_" not in col:
            continue
        base, slot = col.rsplit("__slot_", 1)
        if not slot.isdigit():
            continue
        slot_idx = int(slot)
        slot_map.setdefault(slot_idx, []).append(col)
    return slot_map


def transform_wind_dir(df: pd.DataFrame, slot_map: Dict[int, List[str]]) -> pd.DataFrame:
    df = df.copy()
    for slot_idx, cols in slot_map.items():
        wind_col: str = f"wind_dir_deg__slot_{slot_idx}"
        if wind_col not in df.columns:
            continue
        theta = np.deg2rad(pd.to_numeric(df[wind_col], errors="coerce"))
        df[f"wind_dir_sin__slot_{slot_idx}"] = np.sin(theta)
        df[f"wind_dir_cos__slot_{slot_idx}"] = np.cos(theta)
        df = df.drop(columns=[wind_col])
        cols.remove(wind_col)
        cols.extend([f"wind_dir_sin__slot_{slot_idx}", f"wind_dir_cos__slot_{slot_idx}"])
    return df


def reorder_by_slot(slot_map: Dict[int, List[str]]) -> List[str]:
    ordered: List[str] = []
    for slot_idx in sorted(slot_map):
        bases: List[LiteralString] = [c.rsplit("__slot_", 1)[0] for c: str in slot_map[slot_idx]]
        for base in sorted(set(bases)):
            col: str = f"{base}__slot_{slot_idx}"
            if col in slot_map[slot_idx]:
                ordered.append(col)
    return ordered


def drop_low_variance(df: pd.DataFrame, cols: List[str], min_std: float) -> List[str]:
    if not cols:
        return cols
    stds: float = df[cols].astype(float).std(axis=0, ddof=0)
    keep = stds[stds >= min_std].index.tolist()
    return keep


def min_distance_to_shapelet(ts: np.ndarray, shapelet: np.ndarray) -> float:
    ts = np.asarray(ts, dtype=float)
    s = np.asarray(shapelet, dtype=float)
    length = int(s.shape[0])
    if length > ts.shape[0]:
        raise ValueError("Shapelet is longer than series")
    windows = np.lib.stride_tricks.sliding_window_view(ts, window_shape=length)
    w_mu = windows.mean(axis=1, keepdims=True)
    w_sd = windows.std(axis=1, ddof=0, keepdims=True)
    windows = (windows - w_mu) / (w_sd + 1e-8)
    s = (s - s.mean()) / (s.std(ddof=0) + 1e-8)
    d2 = ((windows - s) ** 2).sum(axis=1)
    return float(np.sqrt(d2.min()))


def compute_shapelet_distances(x: np.ndarray, shapelets: Sequence[np.ndarray]) -> np.ndarray:
    n_samples: int = x.shape[0]
    n_shapelets: int = len(shapelets)
    out: np.ndarray[Tuple[int], np.dtype[np.float64]] = np.zeros((n_samples, n_shapelets), dtype=float)
    for i: int in range(n_samples):
        for j, shapelet in enumerate(shapelets):
            out[i, j] = min_distance_to_shapelet(x[i], shapelet)
    return out


def generate_candidates(x: np.ndarray, lengths: Sequence[int], max_rows: int) -> List[np.ndarray]:
    n_rows: int = min(max_rows, x.shape[0])
    candidates: List[np.ndarray] = []
    for i: int in range(n_rows):
        ts = x[i]
        for length: int in lengths:
            if length > ts.shape[0]:
                continue
            windows = np.lib.stride_tricks.sliding_window_view(ts, window_shape=length)
            for w in windows:
                candidates.append(np.asarray(w, dtype=float).copy())
    return candidates


def dedupe_candidates(candidates: Sequence[np.ndarray], decimals: int) -> List[np.ndarray]:
    seen = set()
    unique: List[np.ndarray] = []
    for cand in candidates:
        key = tuple(np.round(cand, decimals=decimals).tolist())
        if key in seen:
            continue
        seen.add(key)
        unique.append(cand)
    return unique


def score_candidates(
    candidates: Sequence[np.ndarray],
    x_eval: np.ndarray,
    max_eval_rows: int,
) -> np.ndarray:
    n_rows: int = min(max_eval_rows, x_eval.shape[0])
    idx: np.ndarray[Tuple[int], np.dtype[np.signedinteger[Any]]] = np.arange(n_rows)
    scores: np.ndarray[Tuple[int], np.dtype[np.float64]] = np.zeros(len(candidates), dtype=float)
    for i, cand in enumerate(candidates):
        dists: List[float] = [min_distance_to_shapelet(x_eval[j], cand) for j in idx]
        scores[i] = float(np.std(dists))
    return scores


def select_shapelets(
    candidates: Sequence[np.ndarray],
    scores: np.ndarray,
    target: int,
    corr_threshold: float,
) -> List[np.ndarray]:
    order: np.ndarray[Tuple[int, ...], np.dtype[np.signedinteger[np._32Bit | np._64Bit]]] = np.argsort(scores)[::-1]
    selected: List[np.ndarray] = []
    for idx in order:
        cand = candidates[int(idx)]
        keep = True
        for chosen in selected:
            if cand.shape[0] != chosen.shape[0]:
                continue
            corr: np.ndarray[Tuple[int, ...], np.dtype[np.floating[Any]]] = np.corrcoef(cand, chosen)[0, 1]
            if abs(corr) >= corr_threshold:
                keep = False
                break
        if keep:
            selected.append(cand)
        if len(selected) >= target:
            break
    return selected


def kmeans_grid(x: np.ndarray, k_min: int, k_max: int) -> Tuple[int, List[Tuple[int, float]]]:
    rows = []
    best_k: int = k_min
    best_score: float = -1.0
    for k: int in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=0)
        labels = km.fit_predict(x)
        if len(set(labels)) < 2:
            score: float = -1.0
        else:
            score = float(silhouette_score(x, labels))
        rows.append((k, score))
        if score > best_score:
            best_score: float = score
            best_k: int = k
    return best_k, rows


def _safe_silhouette(x: np.ndarray, labels: np.ndarray) -> float:
    unique = set(labels)
    if len(unique) < 2:
        return -1.0
    return float(silhouette_score(x, labels))


def _hdbscan_summary(x: np.ndarray) -> Tuple[np.ndarray, Dict[str, float] | None]:
    if hdbscan is None:
        return np.array([], dtype=int), None
    clusterer = hdbscan.HDBSCAN(min_cluster_size=25)
    labels = clusterer.fit_predict(x)
    mask = labels != -1
    if mask.sum() > 1 and len(set(labels[mask])) > 1:
        sil = float(silhouette_score(x[mask], labels[mask]))
    else:
        sil: float = -1.0
    summary = {
        "n_clusters": int(len(set(labels)) - (1 if -1 in labels else 0)),
        "noise_fraction": float(np.mean(labels == -1)),
        "silhouette": sil,
    }
    return labels, summary


def _top_features(
    df: pd.DataFrame,
    labels: np.ndarray,
    columns: List[str],
    top_n: int,
) -> Dict[str, List[Tuple[str, float]]]:
    global_mean: float = df[columns].mean()
    global_std = df[columns].std(ddof=0).replace(0.0, np.nan)
    results: Dict[str, List[Tuple[str, float]]] = {}

    for cluster_id in sorted(set(labels)):
        if cluster_id == -1:
            continue
        mask = labels == cluster_id
        cluster_mean = df.loc[mask, columns].mean()
        z_scores = (cluster_mean - global_mean) / global_std
        z_scores = z_scores.replace([np.inf, -np.inf], np.nan).dropna()
        top = z_scores.abs().sort_values(ascending=False).head(top_n)
        results[str(cluster_id)] = [(name, float(z_scores[name])) for name in top.index]
    return results


def run_summary(config: SummaryConfig, data_path: Path) -> Dict[str, object]:
    df: DataFrame = pd.read_csv(data_path)
    slot_map: Dict[int, List[str]] = slot_columns(df.columns)
    df: DataFrame = transform_wind_dir(df, slot_map)
    ordered_cols: List[str] = reorder_by_slot(slot_map)
    ordered_cols: List[str] = drop_low_variance(df, ordered_cols, config.min_std)

    x_raw: np.ndarray[Tuple[int], np.dtype[Any]] = df[ordered_cols].to_numpy(dtype=float)
    x_raw: np.ndarray[Tuple[int], np.dtype[Any]] = np.nan_to_num(x_raw, copy=False)

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x_raw)

    candidates = generate_candidates(x_scaled, config.lengths, config.max_rows)
    candidates = [c for c in candidates if np.std(c) >= config.min_std]
    candidates = dedupe_candidates(candidates, decimals=4)

    if len(candidates) > config.max_pool:
        variances = np.array([np.std(c) for c in candidates])
        top_idx: np.ndarray[Tuple[int, ...], np.dtype[np.signedinteger[np._32Bit | np._64Bit]]] = np.argsort(variances)[::-1][: config.max_pool]
        candidates = [candidates[int(i)] for i in top_idx]

    scores = score_candidates(candidates, x_scaled, config.eval_rows)
    selected = select_shapelets(candidates, scores, config.target_shapelets, config.corr_threshold)

    x_shapelet = compute_shapelet_distances(x_scaled, selected)
    x_shapelet = StandardScaler().fit_transform(x_shapelet)

    best_k, k_scores = kmeans_grid(x_shapelet, config.k_min, config.k_max)
    km = KMeans(n_clusters=best_k, n_init=10, random_state=0)
    km_labels = km.fit_predict(x_shapelet)
    km_sil: float = _safe_silhouette(x_shapelet, km_labels)

    ward_labels = AgglomerativeClustering(n_clusters=best_k).fit_predict(x_shapelet)
    ward_sil: float = _safe_silhouette(x_shapelet, ward_labels)

    hdb_labels, hdb_summary = _hdbscan_summary(x_shapelet)

    explain_cols: List[str] = [c for c: str in df.columns if c.endswith("__mean") or c.endswith("__std") or c.endswith("__trend")]
    explain_df: Series[Any] = df[explain_cols].copy()

    config.output_dir.mkdir(parents=True, exist_ok=True)

    summary_table = [
        {"method": "kmeans", "k": int(best_k), "silhouette": float(km_sil)},
        {"method": "ward", "k": int(best_k), "silhouette": float(ward_sil)},
    ]
    if hdb_summary is not None:
        summary_table.append(
            {
                "method": "hdbscan",
                "k": int(hdb_summary["n_clusters"]),
                "silhouette": float(hdb_summary["silhouette"]),
                "noise_fraction": float(hdb_summary["noise_fraction"]),
            }
        )

    metrics_path: Path = config.output_dir / "picoclimate_shapelet_metrics.csv"
    pd.DataFrame(summary_table).to_csv(metrics_path, index=False)

    for name, labels in [("kmeans", km_labels), ("ward", ward_labels)]:
        agg: Series[Any] = explain_df.copy()
        agg["cluster"] = labels
        cluster_means: Series[Any] = agg.groupby("cluster").mean(numeric_only=True)
        cluster_means.to_csv(config.output_dir / f"picoclimate_cluster_means_{name}.csv")

        top: Dict[str, List[Tuple[str, float]]] = _top_features(explain_df, labels, explain_cols, config.top_n)
        (config.output_dir / f"picoclimate_cluster_top_{name}.json").write_text(
            json.dumps(top, indent=2), encoding="utf-8"
        )

    if hdb_summary is not None:
        agg: Series[Any] = explain_df.copy()
        agg["cluster"] = hdb_labels
        cluster_means = agg[agg["cluster"] != -1].groupby("cluster").mean(numeric_only=True)
        cluster_means.to_csv(config.output_dir / "picoclimate_cluster_means_hdbscan.csv")

        top: Dict[str, List[Tuple[str, float]]] = _top_features(explain_df, hdb_labels, explain_cols, config.top_n)
        (config.output_dir / "picoclimate_cluster_top_hdbscan.json").write_text(
            json.dumps(top, indent=2), encoding="utf-8"
        )

    summary = {
        "rows": int(x_raw.shape[0]),
        "slot_columns": int(len(ordered_cols)),
        "lengths": list(config.lengths),
        "candidates": int(len(candidates)),
        "selected_shapelets": int(len(selected)),
        "kmeans_best_k": int(best_k),
        "kmeans_scores": k_scores,
        "ward_silhouette": float(ward_sil),
        "hdbscan": hdb_summary,
        "metrics_csv": str(metrics_path),
    }

    config_payload: Dict[str, Any] = asdict(config)
    config_payload["output_dir"] = str(config.output_dir)
    (config.output_dir / "picoclimate_cluster_summary.json").write_text(
        json.dumps({"config": config_payload, "summary": summary}, indent=2),
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Picoclimate cluster summaries for shapelet clusters.")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path("data/picoclimate_test/window_features.csv"),
    )
    parser.add_argument("--lengths", type=str, default="2,3,4,5,6")
    parser.add_argument("--max-rows", type=int, default=200)
    parser.add_argument("--eval-rows", type=int, default=120)
    parser.add_argument("--max-pool", type=int, default=2000)
    parser.add_argument("--target-shapelets", type=int, default=300)
    parser.add_argument("--min-std", type=float, default=1e-3)
    parser.add_argument("--corr-threshold", type=float, default=0.95)
    parser.add_argument("--k-min", type=int, default=2)
    parser.add_argument("--k-max", type=int, default=6)
    parser.add_argument("--top-n", type=int, default=6)
    parser.add_argument("--output-dir", type=Path, default=Path("docs/reports"))
    return parser


def main() -> None:
    parser: argparse.ArgumentParser = build_parser()
    args: argparse.Namespace = parser.parse_args()
    config = SummaryConfig(
        lengths=parse_lengths(args.lengths),
        max_rows=args.max_rows,
        eval_rows=args.eval_rows,
        max_pool=args.max_pool,
        target_shapelets=args.target_shapelets,
        min_std=args.min_std,
        corr_threshold=args.corr_threshold,
        k_min=args.k_min,
        k_max=args.k_max,
        top_n=args.top_n,
        output_dir=args.output_dir,
    )
    summary: Dict[str, object] = run_summary(config, args.data_path)

    print("Picoclimate cluster summary")
    for key, value in summary.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
