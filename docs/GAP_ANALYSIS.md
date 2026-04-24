# Gap Analysis and Research Governance

Last updated: 2026-04-21

This file is the consolidated source of truth for:

- readiness gap analysis
- experiment protocol and quality standards
- skills/knowledge coverage tracking
- reporting requirements for insights, failures, experimentations, results, and implementation details

This file replaces previous separate documentation and centralizes all governance content in one place.

## Internship Requirements

1. Explainability for clustering of spatio-temporal picoclimatic data
2. Explain what defines each cluster and why one point belongs to one cluster
3. Keep explanation format stable despite input format changes
4. Compare multiple clustering approaches
5. Use ML/DL, notably representation-space methods
6. Work rigorously with scientific documentation
7. Collaborate in a multidisciplinary context (architects + ML researchers)

## Current Baseline in Repository

- Baseline notebooks for K-Means, hierarchical clustering, LIME, and SHAP
- Synthetic data generator approximating mobile urban sensing
- Reproducible research scripts in `scripts/research/`
- Documentation and outputs structure already in place
- Executable baselines already present for `KMeans`, `ExKMC`, `autoencoder + KMeans`, and a picoclimate benchmark script that now includes `HDBSCAN`

## Critical Gaps Identified

1. No complete benchmark execution archive across all target methods
2. Limited seed-stability evidence for explanation robustness
3. Representation-space pipeline exists but needs broader comparative evidence
4. Notebook-first workflows still need consistent script-first reporting outputs

## Experiment Protocol (Research Standard)

### Objective

Evaluate and explain clustering solutions for spatio-temporal picoclimate windows with reproducibility and clear scientific reporting.

### Core hypotheses

- H1: Different clustering families discover complementary picoclimate structures.
- H2: Surrogate-based explainability can provide stable cluster-level drivers when surrogate fidelity is high.
- H3: Deep latent representations improve separation and semantic interpretability over raw engineered features.

### Data policy

- Use one fixed dataset version per experiment series.
- Keep immutable input files and version output directories with timestamps.
- Track feature set used (all, meteorology-only, morphology-only, mixed).

### Reproducibility policy

- Fix random seeds for all stochastic steps.
- Record package versions and script parameters.
- Save machine-readable artifacts (CSV/JSON) and concise markdown summaries.

### Minimum method set

1. K-Means
2. Agglomerative (Ward)
3. Gaussian Mixture
4. DBSCAN (or HDBSCAN if available)
5. Spectral Clustering
6. Autoencoder latent + K-Means

### Minimum metrics

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
- Explanation stability (multiple seeds; top-feature overlap)

### Fixed explanation output format

For each cluster, always produce:

1. Cluster identity: id, size, proportion
2. Global drivers: top positive and negative features
3. Typical profile: mean or z-score per key sensor feature
4. Membership rationale: nearest-boundary examples and representative samples
5. Confidence note: surrogate fidelity and caveats

This format must remain unchanged even if temporal or spatial inputs change.
Treat this as a reporting contract, not a suggestion. Any new method must emit the same cluster summary structure before it is considered ready.

### Reporting template (per experiment)

- Question
- Data and feature setup
- Methods and parameters
- Quantitative results table
- Cluster interpretation summary
- XAI summary with caveats
- Failure modes and next iteration

### Statistical robustness

- Repeat each stochastic setup at least 5 seeds.
- Report mean plus/minus std for key metrics.
- Prefer conclusions stable across seeds over single-run best score.
