# xai-spatio-temporal

M2 internship repository (LIRMM) for explainable clustering of spatio-temporal
picoclimatic data.

Focus: explainable clustering for spatio-temporal picoclimatic data, with reproducible scripts and a stable explanation format.

## Objectives

- Compare multiple clustering families under one fixed protocol
- Explain cluster structure globally and point-level assignment locally
- Keep explanation outputs stable even when inputs evolve
- Provide reproducible scripts and auditable experiment artifacts

## Repository Layout

- `docs/`: protocol and internship-alignment documents
- `scripts/data/`: synthetic data generation and reduction utilities
- `scripts/research/`: clustering and XAI experiment pipelines
- `data/`: lightweight dataset documentation and metadata

## Core Workflow

1. Generate synthetic data into `data/`.
2. Run clustering baselines and save outputs in `outputs/benchmark/`.
3. Run surrogate explainability and advanced SHAP/LIME analyses.
4. Run latent-space clustering (autoencoder + K-Means).
5. Report results following `docs/EXPERIMENT_PROTOCOL.md`.

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Generate synthetic data:

```bash
python scripts/data/generate_picoclimate_data.py --outdir data --seed 42 --n-locations 24 --days 90
```

3. Run clustering benchmark:

```bash
python scripts/research/benchmark_clustering_pipeline.py --data data/window_features.csv --outdir outputs/benchmark
```

4. Run surrogate XAI:

```bash
python scripts/research/surrogate_xai_pipeline.py --data data/window_features.csv --outdir outputs/xai
```

5. Run deep representation + clustering:

```bash
python scripts/research/deep_representation_clustering.py --data data/window_features.csv --outdir outputs/deep --epochs 60
```

6. Run advanced LIME/SHAP pipeline:

```bash
python scripts/research/lime_shap_explainability_pipeline.py --data data/window_features.csv --outdir outputs/xai_advanced --max-samples 3000
```

## Commit Convention

- This repository uses: `type (scope): short description`
- Full policy: `docs/COMMIT_POLICY.md`
- Reusable template file: `.gitmessage`

Optional global setup:

```bash
git config --global commit.template "/absolute/path/to/this/repo/.gitmessage"
```

## Notes

- Use `docs/EXPERIMENT_PROTOCOL.md` as the standard for experimental rigor and reporting.
- Use `docs/SKILLS_MATRIX.md` and `docs/INTERNSHIP_GAP_ANALYSIS.md` to track internship-readiness coverage.
- Keep generated outputs under `outputs/` locally unless explicitly needed in version control.
