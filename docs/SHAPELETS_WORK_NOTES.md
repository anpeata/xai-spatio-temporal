# Shapelets Work Notes (ECG200)

## Scope
This note summarizes shapelet understanding, implementation work completed, and how to review outputs later.

## Shapelet understanding
- A shapelet is a short subsequence pattern extracted from a time series.
- Each full ECG series is represented by distances to multiple shapelets.
- Smaller distance means stronger local similarity to that shapelet pattern.
- Clustering in shapelet space is often easier to interpret than clustering directly on all raw time points.

## Work completed
### 1) Added aggregate statistics to shapelets
In the shapelets notebook, shapelet metadata now includes:
- shapelet_mean
- shapelet_max
- shapelet_variance

These are computed per shapelet from the shapelet values themselves and stored in `shapelet_meta`.

### 2) Added SHAP explanation enrichment for shapelets
The shapelets notebook now:
- keeps SHAP importance tables per view in `shap_importance_by_view`
- adds an enriched SHAP table (`shap_shapelet_enriched_by_view`) by merging SHAP importance with shapelet metadata

This allows direct reading of feature importance together with shapelet statistics (length, mean, max, variance).

### 3) Added abductive explanations for shapelet approach
A new abductive section was added to the shapelets notebook.
For sampled points per view, it computes a minimal surrogate-rule-consistent feature edit that changes the predicted cluster.

Main output variable:
- `abductive_by_view`

### 4) Added abductive explanations for raw/original approach
A matching abductive section was added to the raw ECG notebook (`kmeans_ecg200.ipynb`) so both approaches are covered.

Main output variable:
- `raw_abductive_by_view`

### 5) Added adaptive shapelet dictionary selection (real-world style)
The shapelets notebook now follows a practical pipeline instead of using a fixed dictionary size only:

1. Generate many candidate shapelets across multiple lengths.
2. Rank candidates using usefulness (distance dispersion) and seed-stability.
3. Prune redundant candidates using correlation thresholding.
4. Evaluate dictionary sizes (10/25/50/100) with unsupervised quality + stability.
5. Freeze the selected dictionary size and continue clustering/explanations.

Main output variables:
- `shapelet_candidate_scores`
- `shapelet_dictionary_size_eval`
- `shapelet_dictionary_report`
- `selected_shapelet_size`

## Abductive method details
The abductive implementation is surrogate-tree based.

High-level steps:
1. Train (existing) shallow decision tree surrogates to mimic KMeans cluster labels.
2. Extract leaf constraints as feature intervals from tree splits.
3. For each sampled instance, evaluate alternative target leaves with different cluster labels.
4. Build the smallest feature edit that satisfies the target leaf constraints.
5. Keep the best candidate using lexical ranking:
   - first minimize number of changed features
   - then minimize total absolute feature shift

Outputs include:
- original cluster
- target cluster
- number of features changed
- total absolute shift
- edited features summary

## Where to review in notebooks
### Shapelet notebook
File: `scripts/notebooks/kmeans_ecg200_shapelets.ipynb`
- Adaptive dictionary selection is built in the shapelet build cell.
- Aggregate stats added in Cell 5
- SHAP + aggregate shapelet stats section in Cells 18-19
- Abductive explanations for shapelet views in Cells 20-21

### Raw notebook
File: `scripts/notebooks/kmeans_ecg200.ipynb`
- Abductive explanations for raw views in Cells 14-15

## How to run quickly
1. Open the target notebook.
2. Run all cells in order.
3. If SHAP import fails, install SHAP in the environment, then rerun SHAP-related cells.

## Interpretation tips
- Compare `n_features_changed` between approaches.
  - Lower values suggest easier local rule-based transitions between clusters.
- Compare `total_abs_shift` between approaches.
  - Lower values suggest smaller edits needed to flip cluster assignment under the surrogate.
- For shapelets, use enriched SHAP tables to connect importance with shapelet profile stats.

## Notes and limitations
- Abductive results are surrogate-model explanations, not direct optimization on KMeans objective.
- They are faithful to the learned surrogate rules; fidelity quality depends on surrogate performance.
- Sampling is intentionally limited for readability and speed.
