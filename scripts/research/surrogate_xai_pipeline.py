from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explain cluster assignments with supervised surrogate model")
    parser.add_argument("--data", type=str, required=True, help="Path to window_features.csv")
    parser.add_argument("--outdir", type=str, required=True, help="Output directory")
    parser.add_argument("--k", type=int, default=6, help="Number of clusters for K-Means")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--top", type=int, default=12, help="Top features per cluster explanation")
    parser.add_argument("--max-samples", type=int, default=0, help="Optional cap on number of rows for faster experiments (0 = all)")
    parser.add_argument("--n-estimators", type=int, default=300, help="Number of trees in surrogate RandomForest")
    parser.add_argument("--perm-repeats", type=int, default=6, help="Permutation importance repeats")
    parser.add_argument("--n-jobs", type=int, default=1, help="Parallel workers for sklearn components")
    return parser.parse_args()


def load_xy(df: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame, List[str]]:
    id_cols = ["city", "device_id", "window_start", "true_regime"]
    feature_cols = [
        c
        for c in df.columns
        if c not in id_cols and pd.api.types.is_numeric_dtype(df[c])
    ]
    X_df = df[feature_cols].copy()

    preprocess = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    X = preprocess.fit_transform(X_df)
    return X, X_df, feature_cols


def cluster_and_train(X: np.ndarray, k: int, seed: int, n_estimators: int, n_jobs: int) -> Tuple[np.ndarray, RandomForestClassifier, Dict[str, float], np.ndarray, np.ndarray]:
    cluster = KMeans(n_clusters=k, n_init=20, random_state=seed).fit_predict(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        cluster,
        test_size=0.25,
        random_state=seed,
        stratify=cluster,
    )

    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=seed,
        n_jobs=n_jobs,
        class_weight="balanced_subsample",
    )
    clf.fit(X_train, y_train)
    pred = clf.predict(X_test)

    metrics = {
        "surrogate_accuracy": float(accuracy_score(y_test, pred)),
        "surrogate_macro_f1": float(f1_score(y_test, pred, average="macro")),
    }
    return cluster, clf, metrics, X_test, y_test


def global_importance(
    clf: RandomForestClassifier,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_cols: List[str],
    seed: int,
    perm_repeats: int,
    n_jobs: int,
) -> pd.DataFrame:
    imp = permutation_importance(
        clf,
        X_test,
        y_test,
        n_repeats=perm_repeats,
        random_state=seed,
        n_jobs=n_jobs,
        scoring="f1_macro",
    )
    out = pd.DataFrame(
        {
            "feature": feature_cols,
            "perm_importance_mean": imp.importances_mean,
            "perm_importance_std": imp.importances_std,
        }
    ).sort_values("perm_importance_mean", ascending=False)
    return out


def cluster_profiles(df: pd.DataFrame, cluster: np.ndarray, feature_cols: List[str]) -> pd.DataFrame:
    prof = df.assign(cluster=cluster).groupby("cluster")[feature_cols].mean(numeric_only=True)
    return prof


def top_drivers_per_cluster(profiles: pd.DataFrame, top: int) -> pd.DataFrame:
    z = (profiles - profiles.mean(axis=0)) / (profiles.std(axis=0) + 1e-9)

    rows = []
    for cid in z.index:
        s = z.loc[cid].sort_values(ascending=False)
        top_pos = s.head(top)
        top_neg = s.tail(top).sort_values(ascending=True)

        for name, val in top_pos.items():
            rows.append({"cluster": int(cid), "direction": "positive", "feature": name, "z": float(val)})
        for name, val in top_neg.items():
            rows.append({"cluster": int(cid), "direction": "negative", "feature": name, "z": float(val)})

    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    if args.max_samples and args.max_samples > 0 and len(df) > args.max_samples:
        df = df.sample(n=args.max_samples, random_state=args.seed).reset_index(drop=True)

    X, X_df, feature_cols = load_xy(df)

    cluster, clf, s_metrics, X_test, y_test = cluster_and_train(
        X,
        args.k,
        args.seed,
        n_estimators=args.n_estimators,
        n_jobs=args.n_jobs,
    )

    g_imp = global_importance(
        clf,
        X_test,
        y_test,
        feature_cols,
        args.seed,
        perm_repeats=args.perm_repeats,
        n_jobs=args.n_jobs,
    )
    profiles = cluster_profiles(X_df, cluster, feature_cols)
    drivers = top_drivers_per_cluster(profiles, top=args.top)

    g_imp.to_csv(outdir / "global_feature_importance.csv", index=False)
    profiles.to_csv(outdir / "cluster_profiles.csv")
    drivers.to_csv(outdir / "cluster_top_drivers_fixed_format.csv", index=False)

    summary = {
        "data": str(data_path),
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "k": int(args.k),
        "max_samples": int(args.max_samples),
        "n_estimators": int(args.n_estimators),
        "perm_repeats": int(args.perm_repeats),
        "n_jobs": int(args.n_jobs),
        "surrogate": "RandomForestClassifier",
        **s_metrics,
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Surrogate XAI pipeline completed")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
