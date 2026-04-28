from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autoencoder latent representation + clustering benchmark")
    parser.add_argument("--data", type=str, required=True, help="Path to window_features.csv")
    parser.add_argument("--outdir", type=str, required=True, help="Output directory")
    parser.add_argument("--k", type=int, default=6, help="Number of clusters")
    parser.add_argument("--latent-dim", type=int, default=16, help="Latent representation dimension")
    parser.add_argument("--hidden-dim", type=int, default=128, help="MLP hidden layer size")
    parser.add_argument("--epochs", type=int, default=60, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=256, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--max-samples", type=int, default=0, help="Optional cap on number of rows for faster experiments (0 = all)")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def prepare(df: pd.DataFrame) -> Tuple[np.ndarray, pd.Series | None, List[str]]:
    id_cols = ["city", "device_id", "window_start", "location_id", "date"]
    label_col = "true_regime" if "true_regime" in df.columns else None

    feature_cols = [
        col
        for col in df.columns
        if col not in id_cols and (label_col is None or col != label_col) and pd.api.types.is_numeric_dtype(df[col])
    ]

    X_df = df[feature_cols].copy()

    preprocess = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    X = preprocess.fit_transform(X_df)
    y_true = df[label_col] if label_col is not None else None
    return X, y_true, feature_cols


class Autoencoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, latent_dim: int) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        z = self.encoder(x)
        x_hat = self.decoder(z)
        return x_hat, z


def train_autoencoder(X: np.ndarray, hidden_dim: int, latent_dim: int, epochs: int, batch_size: int, lr: float, seed: int) -> Tuple[Autoencoder, List[float]]:
    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = Autoencoder(input_dim=X.shape[1], hidden_dim=hidden_dim, latent_dim=latent_dim).to(device)
    optim = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    x_tensor = torch.tensor(X, dtype=torch.float32)
    ds = TensorDataset(x_tensor)
    dl = DataLoader(ds, batch_size=batch_size, shuffle=True)

    losses: List[float] = []
    model.train()
    for _ in range(epochs):
        run_loss = 0.0
        n = 0
        for (xb,) in dl:
            xb = xb.to(device)
            optim.zero_grad()
            x_hat, _ = model(xb)
            loss = loss_fn(x_hat, xb)
            loss.backward()
            optim.step()

            run_loss += float(loss.item()) * xb.size(0)
            n += xb.size(0)

        losses.append(run_loss / max(1, n))

    return model, losses


def encode(model: Autoencoder, X: np.ndarray) -> np.ndarray:
    device = next(model.parameters()).device
    model.eval()
    with torch.no_grad():
        x = torch.tensor(X, dtype=torch.float32, device=device)
        _, z = model(x)
    return z.cpu().numpy()


def eval_labels(X: np.ndarray, labels: np.ndarray, y_true: pd.Series | None) -> Dict[str, float]:
    out: Dict[str, float] = {
        "silhouette": float(silhouette_score(X, labels)) if len(np.unique(labels)) > 1 else float("nan"),
        "calinski_harabasz": float(calinski_harabasz_score(X, labels)) if len(np.unique(labels)) > 1 else float("nan"),
        "davies_bouldin": float(davies_bouldin_score(X, labels)) if len(np.unique(labels)) > 1 else float("nan"),
    }
    if y_true is not None:
        yt = y_true.astype(str).to_numpy()
        out["ari"] = float(adjusted_rand_score(yt, labels))
        out["nmi"] = float(normalized_mutual_info_score(yt, labels))
    else:
        out["ari"] = float("nan")
        out["nmi"] = float("nan")
    return out


def main() -> None:
    args = parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.data)
    if args.max_samples and args.max_samples > 0 and len(df) > args.max_samples:
        df = df.sample(n=args.max_samples, random_state=args.seed).reset_index(drop=True)

    X, y_true, feature_cols = prepare(df)

    model, losses = train_autoencoder(
        X=X,
        hidden_dim=args.hidden_dim,
        latent_dim=args.latent_dim,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        seed=args.seed,
    )

    Z = encode(model, X)

    labels_raw = KMeans(n_clusters=args.k, n_init=20, random_state=args.seed).fit_predict(X)
    labels_latent = KMeans(n_clusters=args.k, n_init=20, random_state=args.seed).fit_predict(Z)

    raw_metrics = eval_labels(X, labels_raw, y_true)
    latent_metrics = eval_labels(Z, labels_latent, y_true)

    pd.DataFrame({"epoch": np.arange(1, len(losses) + 1), "recon_loss": losses}).to_csv(
        outdir / "training_curve.csv", index=False
    )
    pd.DataFrame({"cluster_raw": labels_raw, "cluster_latent": labels_latent}).to_csv(
        outdir / "cluster_labels.csv", index=False)

    summary = {
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "feature_count": len(feature_cols),
        "max_samples": int(args.max_samples),
        "latent_dim": int(args.latent_dim),
        "epochs": int(args.epochs),
        "raw_feature_clustering": raw_metrics,
        "latent_feature_clustering": latent_metrics,
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Deep representation clustering completed")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
