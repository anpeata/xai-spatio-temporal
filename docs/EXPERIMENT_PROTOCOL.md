# Experiment Protocol (Research Standard)

## Objective

Evaluate and explain clustering solutions for spatio-temporal picoclimate windows with reproducibility and clear scientific reporting.

## Core hypotheses

- H1: Different clustering families discover complementary picoclimate structures.
- H2: Surrogate-based explainability can provide stable cluster-level drivers when surrogate fidelity is high.
- H3: Deep latent representations improve separation and semantic interpretability over raw engineered features.

## Data policy

- Use one fixed dataset version per experiment series.
- Keep immutable input files and version output directories with timestamps.
- Track feature set used (all, meteorology-only, morphology-only, mixed).

## Reproducibility policy

- Fix random seeds for all stochastic steps.
- Record package versions and script parameters.
- Save both machine-readable results (CSV/JSON) and concise markdown summaries.

## Minimum method set

1. K-Means
2. Agglomerative (Ward)
3. Gaussian Mixture
4. DBSCAN (or HDBSCAN if available)
5. Spectral Clustering
6. Autoencoder latent + K-Means

## Minimum metrics

Internal metrics:
- Silhouette score
- Calinski-Harabasz index
- Davies-Bouldin index

If synthetic ground truth is available:
- ARI
- NMI

XAI quality metrics:
- Surrogate test accuracy
- Surrogate macro-F1
- Explanation stability (repeat with multiple seeds and compute top-feature overlap)

## Explanation output format (fixed)

For each cluster, always produce:

1. Cluster identity: id, size, proportion
2. Global drivers: top positive and negative features
3. Typical profile: mean/z-score per key sensor feature
4. Membership rationale: nearest-boundary examples and representative samples
5. Confidence note: surrogate fidelity and caveats

This format must remain unchanged even if input temporal/spatial windows change.

## Reporting template (per experiment)

- Question
- Data and feature setup
- Methods and parameters
- Quantitative results table
- Cluster interpretation summary
- XAI summary with caveats
- Failure modes and next iteration

## Statistical robustness

- Repeat each stochastic setup at least 5 seeds.
- Report mean ± std for key metrics.
- Prefer conclusions stable across seeds over single-run best score.
