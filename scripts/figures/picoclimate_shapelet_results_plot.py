from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot picoclimate shapelet clustering metrics.")
    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("docs/reports/picoclimate_shapelet_metrics.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("scripts/figures/picoclimate_shapelet_results_2026-05-27.png"),
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    df = pd.read_csv(args.metrics)
    df = df.sort_values("method")

    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    ax.bar(df["method"], df["silhouette"], color="#065A82")
    ax.set_ylabel("Silhouette")
    ax.set_xlabel("Method")
    ax.set_title("Picoclimate Shapelet Clustering (Slot-wise)")
    ax.set_ylim(min(-0.05, df["silhouette"].min() - 0.02), df["silhouette"].max() + 0.05)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    for idx, val in enumerate(df["silhouette"].tolist()):
        ax.text(idx, val + 0.005, f"{val:.3f}", ha="center", va="bottom", fontsize=8)

    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=200)


if __name__ == "__main__":
    main()
