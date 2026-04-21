# Gap Analysis and Research Governance

Last updated: 2026-04-21

This file is the consolidated source of truth for:

- internship readiness gap analysis
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

## Skills and Knowledge Matrix

Scoring: 0 = missing, 1 = beginner, 2 = working, 3 = strong

| Requirement | Evidence in repository | Score | Action to reach internship-ready |
|---|---|---:|---|
| Classical clustering (K-Means, hierarchical) | notebooks 01, 02 + benchmark script | 3 | Add DBSCAN/GMM/Spectral comparisons in reports |
| Explainability methods (LIME/SHAP) | notebooks 03, 04 + surrogate_xai_pipeline | 3 | Evaluate explanation stability across seeds/samples |
| Clustering explanation framing | profile tables + local explanations | 2 | Standardize per-cluster explanation template |
| Spatio-temporal data handling | synthetic generator with trajectories/windows | 2 | Add temporal/route-split validation |
| Deep learning (PyTorch/TensorFlow) | deep_representation_clustering.py (PyTorch) | 2 | Extend to contrastive/sequence encoder |
| Representation-space clustering | latent clustering pipeline | 2 | Compare latent vs raw feature clustering statistically |
| Scientific rigor and reproducibility | protocol + deterministic seeds + exported outputs | 3 | Keep experiment logs for every run |
| Documentation quality | README + consolidated governance file | 3 | Maintain progress notes with evidence |
| Multidisciplinary communication | cluster summaries for non-ML audience | 2 | Add architect-facing visual narratives |

## Mandatory Reporting Scope

Yes, repository reporting should cover all of the following for each significant experiment cycle:

- insights
- failures
- experimentations
- results
- implementation details

Use:

- `docs/PROGRESS.md` for ongoing updates
- this file for standards, readiness tracking, and decision criteria

## Priority Actions (Next 2 Weeks)

1. Run and archive outputs for all core scripts and method families
2. Produce one concise comparison report on identical splits
3. Add explanation stability analysis across seeds
4. Prepare a short architect-facing narrative of cluster meaning
