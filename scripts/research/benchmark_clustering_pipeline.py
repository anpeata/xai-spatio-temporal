from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans, SpectralClustering
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from sklearn.cluster import HDBSCAN
except Exception:
    try:
        from hdbscan import HDBSCAN
    except Exception:
        HDBSCAN = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark clustering methods on picoclimate window features")
    parser.add_argument("--data", type=str, required=True, help="Path to window_features.csv")
    parser.add_argument("--outdir", type=str, required=True, help="Output directory")
    parser.add_argument("--k", type=int, default=6, help="Target number of clusters where relevant")
    parser.add_argument("--hdbscan-min-cluster-size", type=int, default=15, help="Minimum cluster size for HDBSCAN")
    parser.add_argument("--hdbscan-min-samples", type=int, default=10, help="Minimum samples for HDBSCAN")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser.parse_args()


def prepare_features(df: pd.DataFrame) -> tuple[np.ndarray, List[str], pd.Series | None]:
    id_cols = ["city", "device_id", "window_start", "location_id", "date"]
    label_col = "true_regime" if "true_regime" in df.columns else None

    feature_cols: List[str] = []
    for col in df.columns:
        if col in id_cols:
            continue
        if label_col is not None and col == label_col:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            feature_cols.append(col)

    X_df = df[feature_cols].copy()
    y_true = df[label_col] if label_col is not None else None

    preprocess = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    X = preprocess.fit_transform(X_df)
    return X, feature_cols, y_true


def safe_internal_metrics(X: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
    unique = np.unique(labels)
    if unique.size < 2:
        return {"silhouette": np.nan, "calinski_harabasz": np.nan, "davies_bouldin": np.nan}

    return {
        "silhouette": float(silhouette_score(X, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(X, labels)),
        "davies_bouldin": float(davies_bouldin_score(X, labels)),
    }


def safe_external_metrics(y_true: pd.Series | None, labels: np.ndarray) -> Dict[str, float]:
    if y_true is None:
        return {"ari": np.nan, "nmi": np.nan}

    yt = pd.Series(y_true).astype(str).to_numpy()
    return {
        "ari": float(adjusted_rand_score(yt, labels)),
        "nmi": float(normalized_mutual_info_score(yt, labels)),
    }


def run_methods(
    X: np.ndarray,
    k: int,
    seed: int,
    hdbscan_min_cluster_size: int,
    hdbscan_min_samples: int,
) -> Dict[str, np.ndarray]:
    outputs: Dict[str, np.ndarray] = {}

    outputs["kmeans"] = KMeans(n_clusters=k, n_init=20, random_state=seed).fit_predict(X)

    outputs["agglomerative_ward"] = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(X)

    outputs["gmm"] = GaussianMixture(n_components=k, covariance_type="full", random_state=seed).fit(X).predict(X)

    outputs["spectral"] = SpectralClustering(
        n_clusters=k,
        random_state=seed,
        affinity="nearest_neighbors",
        assign_labels="kmeans",
        n_neighbors=12,
    ).fit_predict(X)

    outputs["dbscan"] = DBSCAN(eps=0.9, min_samples=15).fit_predict(X)

    if HDBSCAN is not None:
        outputs["hdbscan"] = HDBSCAN(
            min_cluster_size=int(hdbscan_min_cluster_size),
            min_samples=int(hdbscan_min_samples),
        ).fit_predict(X)

    return outputs


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    X, feature_cols, y_true = prepare_features(df)

    method_labels = run_methods(
        X,
        k=args.k,
        seed=args.seed,
        hdbscan_min_cluster_size=args.hdbscan_min_cluster_size,
        hdbscan_min_samples=args.hdbscan_min_samples,
    )

    rows: List[Dict[str, float | str | int]] = []
    labels_df = pd.DataFrame(index=df.index)

    for method, labels in method_labels.items():
        labels_df[method] = labels
        n_clusters = int(pd.Series(labels[labels >= 0]).nunique()) if np.any(labels >= 0) else 0
        noise_ratio = float(np.mean(labels == -1))

        row: Dict[str, float | str | int] = {
            "method": method,
            "n_clusters_excluding_noise": n_clusters,
            "noise_ratio": noise_ratio,
        }
        row.update(safe_internal_metrics(X, labels))
        row.update(safe_external_metrics(y_true, labels))
        rows.append(row)

    results = pd.DataFrame(rows).sort_values("silhouette", ascending=False)
    results.to_csv(outdir / "clustering_benchmark.csv", index=False)
    labels_df.to_csv(outdir / "cluster_labels.csv", index=False)

    summary = {
        "data": str(data_path),
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "feature_count": len(feature_cols),
        "has_true_regime": bool(y_true is not None),
        "hdbscan_min_cluster_size": int(args.hdbscan_min_cluster_size),
        "hdbscan_min_samples": int(args.hdbscan_min_samples),
        "best_by_silhouette": results.iloc[0].to_dict() if len(results) else None,
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Benchmark completed")
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
