# xai-spatio-temporal

M2 internship preparation repository for LIRMM.

Focus: explainable clustering for spatio-temporal picoclimatic data, with reproducible scripts and a stable explanation format.

## Repository Layout

- `docs/`: protocol and internship-alignment documents
- `scripts/data/`: synthetic data generation and reduction utilities
- `scripts/research/`: clustering and XAI experiment pipelines
- `data/`: lightweight dataset documentation and metadata

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

## Notes

- Use `docs/EXPERIMENT_PROTOCOL.md` as the standard for experimental rigor and reporting.
- Use `docs/SKILLS_MATRIX.md` and `docs/INTERNSHIP_GAP_ANALYSIS.md` to track internship-readiness coverage.
- Keep generated outputs under `outputs/` locally unless explicitly needed in version control.
