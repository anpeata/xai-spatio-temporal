from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import shap
from lime.lime_tabular import LimeTabularExplainer
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advanced LIME/SHAP explainability pipeline for cluster assignments")
    parser.add_argument("--data", type=str, required=True, help="Path to window_features.csv")
    parser.add_argument("--outdir", type=str, required=True, help="Output directory")
    parser.add_argument("--k", type=int, default=6, help="Number of clusters for K-Means pseudo-labels")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--max-samples", type=int, default=3000, help="Row cap for runtime control")
    parser.add_argument("--shap-sample", type=int, default=1200, help="Sample size used for SHAP global importance")
    parser.add_argument("--lime-samples", type=int, default=2500, help="Perturbation samples for LIME")
    parser.add_argument("--topn", type=int, default=15, help="Top features to keep in figures/tables")
    parser.add_argument("--n-estimators", type=int, default=220, help="RandomForest number of trees")
    parser.add_argument("--n-jobs", type=int, default=1, help="Parallel jobs for sklearn")
    return parser.parse_args()


def load_features(df: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame, List[str]]:
    id_cols = ["city", "device_id", "window_start", "true_regime"]
    feature_cols = [
        col
        for col in df.columns
        if col not in id_cols and pd.api.types.is_numeric_dtype(df[col])
    ]

    x_df = df[feature_cols].copy()
    preprocess = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    x = preprocess.fit_transform(x_df)
    return x, x_df, feature_cols


def mean_abs_shap(shap_values: object) -> np.ndarray:
    if isinstance(shap_values, list):
        stacked = np.stack([np.asarray(sv) for sv in shap_values], axis=0)
        return np.mean(np.abs(stacked), axis=(0, 1))

    values = np.asarray(shap_values)
    if values.ndim == 2:
        return np.mean(np.abs(values), axis=0)
    if values.ndim == 3:
        if values.shape[1] < values.shape[2]:
            return np.mean(np.abs(values), axis=(0, 2))
        return np.mean(np.abs(values), axis=(0, 1))

    raise ValueError(f"Unsupported SHAP values shape: {values.shape}")


def plot_pipeline_diagram(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 2.8))
    ax.axis("off")

    boxes = [
        (0.02, "Window features\n(142 vars)"),
        (0.23, "K-Means\npseudo-labels"),
        (0.42, "Surrogate RF\nclassifier"),
        (0.61, "SHAP global\nimportance"),
        (0.80, "LIME local\ninstance rationale"),
    ]

    for x, text in boxes:
        ax.add_patch(plt.Rectangle((x, 0.30), 0.16, 0.40, fill=False, linewidth=1.6))
        ax.text(x + 0.08, 0.50, text, ha="center", va="center", fontsize=10)

    for x in [0.18, 0.37, 0.56, 0.75]:
        ax.annotate("", xy=(x + 0.03, 0.50), xytext=(x, 0.50), arrowprops=dict(arrowstyle="->", lw=1.6))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    np.random.seed(args.seed)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.data)
    if args.max_samples > 0 and len(df) > args.max_samples:
        df = df.sample(n=args.max_samples, random_state=args.seed).reset_index(drop=True)

    x, x_df, feature_cols = load_features(df)

    cluster = KMeans(n_clusters=args.k, n_init=20, random_state=args.seed).fit_predict(x)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        cluster,
        test_size=0.25,
        random_state=args.seed,
        stratify=cluster,
    )

    clf = RandomForestClassifier(
        n_estimators=args.n_estimators,
        random_state=args.seed,
        n_jobs=args.n_jobs,
        class_weight="balanced_subsample",
    )
    clf.fit(x_train, y_train)

    pred = clf.predict(x_test)
    acc = float(accuracy_score(y_test, pred))
    macro_f1 = float(f1_score(y_test, pred, average="macro"))

    shap_size = min(args.shap_sample, x.shape[0])
    shap_idx = np.random.choice(x.shape[0], size=shap_size, replace=False)
    x_shap = x[shap_idx]

    explainer = shap.TreeExplainer(clf)
    shap_values = explainer.shap_values(x_shap)
    shap_global = mean_abs_shap(shap_values)
    shap_feature_cols = list(feature_cols)

    if shap_global.shape[0] == len(feature_cols) + 1:
        shap_global = shap_global[:-1]
    if shap_global.shape[0] != len(feature_cols):
        n = min(shap_global.shape[0], len(feature_cols))
        shap_global = shap_global[:n]
        shap_feature_cols = shap_feature_cols[:n]

    shap_df = pd.DataFrame({
        "feature": shap_feature_cols,
        "mean_abs_shap": shap_global,
    }).sort_values("mean_abs_shap", ascending=False)
    shap_df.to_csv(outdir / "shap_global_top_features.csv", index=False)

    top_shap = shap_df.head(args.topn).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.5, 5.6))
    ax.barh(top_shap["feature"], top_shap["mean_abs_shap"], color="#2A6EA6")
    ax.set_title("Global SHAP importance (mean |SHAP|)")
    ax.set_xlabel("Mean absolute SHAP value")
    fig.tight_layout()
    fig.savefig(outdir / "fig_shap_global_top.png", dpi=180)
    plt.close(fig)

    lime_explainer = LimeTabularExplainer(
        training_data=x_train,
        feature_names=feature_cols,
        class_names=[f"cluster_{i}" for i in range(args.k)],
        mode="classification",
        discretize_continuous=True,
        random_state=args.seed,
    )

    idx = int(np.random.randint(0, x_test.shape[0]))
    x_local = x_test[idx]
    pred_class = int(clf.predict([x_local])[0])

    lime_exp = lime_explainer.explain_instance(
        data_row=x_local,
        predict_fn=clf.predict_proba,
        num_features=args.topn,
        top_labels=1,
        num_samples=args.lime_samples,
    )

    lime_pairs = lime_exp.as_list(label=pred_class)
    lime_df = pd.DataFrame(lime_pairs, columns=["feature_condition", "weight"]) 
    lime_df.to_csv(outdir / "lime_local_explanation.csv", index=False)

    lime_sorted = lime_df.sort_values("weight")
    colors = ["#2A6EA6" if value > 0 else "#C23B22" for value in lime_sorted["weight"]]
    fig, ax = plt.subplots(figsize=(9, 5.8))
    ax.barh(lime_sorted["feature_condition"], lime_sorted["weight"], color=colors)
    ax.axvline(0.0, color="black", linewidth=1)
    ax.set_title(f"LIME local explanation (predicted cluster {pred_class})")
    ax.set_xlabel("Local contribution weight")
    fig.tight_layout()
    fig.savefig(outdir / "fig_lime_local.png", dpi=180)
    plt.close(fig)

    profiles = x_df.assign(cluster=cluster).groupby("cluster")[feature_cols].mean(numeric_only=True)
    z = (profiles - profiles.mean(axis=0)) / (profiles.std(axis=0) + 1e-9)
    feature_var = (z.max(axis=0) - z.min(axis=0)).sort_values(ascending=False)
    top_var_cols = feature_var.head(args.topn).index.tolist()

    heat = z[top_var_cols]
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    sns.heatmap(heat, cmap="coolwarm", center=0.0, ax=ax)
    ax.set_title("Cluster profile heatmap (z-score, top varying features)")
    ax.set_xlabel("Feature")
    ax.set_ylabel("Cluster")
    fig.tight_layout()
    fig.savefig(outdir / "fig_cluster_driver_heatmap.png", dpi=180)
    plt.close(fig)

    cm = confusion_matrix(y_test, pred, labels=np.arange(args.k), normalize="true")
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, cmap="Blues", vmin=0.0, vmax=1.0, ax=ax)
    ax.set_title("Surrogate confusion matrix (row-normalized)")
    ax.set_xlabel("Predicted cluster")
    ax.set_ylabel("True pseudo-cluster")
    fig.tight_layout()
    fig.savefig(outdir / "fig_surrogate_confusion_matrix.png", dpi=180)
    plt.close(fig)

    plot_pipeline_diagram(outdir / "fig_xai_pipeline.png")

    summary = {
        "data": str(args.data),
        "n_samples": int(x.shape[0]),
        "n_features": int(x.shape[1]),
        "k": int(args.k),
        "surrogate_accuracy": acc,
        "surrogate_macro_f1": macro_f1,
        "shap_sample": int(shap_size),
        "lime_num_samples": int(args.lime_samples),
        "topn": int(args.topn),
        "predicted_cluster_for_lime": pred_class,
        "top_shap_features": shap_df.head(10).to_dict(orient="records"),
    }

    (outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Advanced LIME/SHAP pipeline completed")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
