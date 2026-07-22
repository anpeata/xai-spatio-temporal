# Notebook Workspace

This folder is organized by topic so notebooks stay in predictable places.

## Layout

- `eda/`: exploratory data analysis notebooks
- `experiments/`: end-to-end workflows, comparisons, and model runs
- `shapelets/`: shapelet discovery, comparison, and explainability notebooks
- `pipelines/`: clustering pipeline notebooks and small cached artifacts
- `examples/`: compact sample or demonstration notebooks
- `cache/`: notebook-local cached binaries and derived artifacts

## Notes

- Keep generated figures and tables out of the notebook folders when possible.
- Put reusable plots in `scripts/figures/`.
- Put notebook caches and binary artifacts in `scripts/notebooks/cache/`.
- Prefer these topic folders instead of adding new notebooks at the top level of `scripts/notebooks/`.