# Picoclimate XAI Strategic Framework

Date: April 2026

## Objective

Bridge the alignment gap between representation learning, clustering, and stable explanation for picoclimatic spatio-temporal data.

## Core Research Obligations

### 1. Stable Explanation Format

Explanations must stay in raw sensor units regardless of the internal representation.

Required output examples:

- Temperature in °C
- Humidity in %
- Wind speed in m/s

Current issue: the pipeline still exposes internal indices such as `s_1` or `t_41`. These must be mapped back to physical sensor traits so the explanation layer is usable by the urban-planner persona.

### 2. Multi-Method Benchmarking

Benchmark coverage now includes:

- KMeans + ExKMC baselines
- Autoencoder + KMeans for latent-space clustering (scripts/research/deep_representation_clustering.py)
- HDBSCAN for spatially aware clustering (scripts/research/benchmark_clustering_pipeline.py)

### 3. Scientific Rigor and Output

Target: one to two papers by early August.

Require a stability metric for explanations, using feature-overlap comparisons such as Jaccard similarity of SHAP top features across at least five random seeds.

## Technical Gap Analysis

### Current Strength

Surrogate fidelity is already high, with train/CV around 0.95/0.93. SHAP concentration on `s_1` shows a compact story, but that story is still model-faithful rather than phenomenon-stable.

### Missing Deep Learning Component

The internship requires deep learning methods. Add an autoencoder pipeline to learn latent representations and study the interpretability gap between latent spaces and raw units.

## Real-World PICOPATT Scenario

The system should support the following flow:

1. Planner selects a spatial region and time window.
2. Tool clusters picoclimatic windows.
3. Explanation layer returns a stable narrative in sensor units.
4. The narrative remains consistent across 1-hour and 6-hour slices.

Example output:

"Cluster 2 is defined by high humidity variance and low wind speed in building canyons."

## Method Roadmap

### Direction B: Statistical Aggregation First

Use Time2Feat-style summaries such as mean, variance, and quartiles.

This gives a clean baseline with strong interpretability and keeps explanations in sensor units.

### Direction A: Neural Representation Next

Add an autoencoder or joint optimization approach as the higher-complexity comparator.

This supports a performance-versus-interpretability analysis and opens the path to a methods paper.

## Architectural Hierarchy

- PICOPATT UI: planner and architect interface
- Explanation: SHAP plus abductive minimal edits
- Clustering: KMeans, HDBSCAN, or ExKMC-style objectives
- Representation: raw windows, statistical summaries, or learned embeddings

## Decision Points

- Freeze the explanation output format now so later methods stay constrained to sensor units.
- Keep fidelity separate from robustness: fidelity measures faithfulness to the surrogate, while robustness measures stability across data granularities.
- Treat the current prototype as Phase 1 and the real-data plus deep-learning extension as Phase 2.

## Working Position

The literature review is close to complete. The project should now move from shapelets as a starting point to neural and statistical representations as the standard for benchmarking and explanation.