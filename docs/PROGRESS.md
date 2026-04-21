# Progress Log

Last updated: 2026-04-21

Use this file for weekly or milestone updates for supervisor meetings.
Each entry should remain short, factual, and auditable.

Ordering rule: keep entries in chronological order and append each new update at the bottom.

## Required Sections for Each Entry

- Experimentations
- Results (numbers, tables, plots)
- Insights
- Failures / issues / risks
- Implementation details
- Next
- Possible questions/concerns

## Template (copy/paste)

### YYYY-MM-DD (Week of YYYY-MM-DD to YYYY-MM-DD)

**Experimentations**
- 

**Results (numbers, tables, plots)**
- 

**Insights**
- 

**Failures / issues / risks**
- 

**Implementation details**
- 

**Next**
- 

**Possible questions/concerns**
- 

---

## Entries

### 2026-04-17 (ECG200 KMeans and XAI workflow)

**Experimentations**
- Implemented KMeans clustering on ECG200 in two variants: raw time-point features and shapelet-distance features (with and without window z-normalization).
- Added unsupervised k selection using silhouette, Calinski-Harabasz, and Davies-Bouldin plus multi-seed stability via pairwise ARI across seeds.
- Benchmarked clusters post-hoc against labels with ARI, NMI, and majority-mapped accuracy (labels used only for evaluation).
- Built explainability via shallow decision-tree surrogates for cluster assignments.
- Generated SHAP attributions on surrogates and summarized cluster curve patterns.

**Results (numbers, tables, plots)**
- Workflow and artifacts generated in notebooks listed below.

**Insights**
- Shapelet and surrogate framing improves readability of cluster rationale for non-ML stakeholders.

**Failures / issues / risks**
- Explanation stability across seeds is not yet fully quantified.
- Real picoclimate transferability still requires validation.

**Implementation details**
- Notebooks: `scripts/notebooks/kmeans_ecg200.ipynb`, `scripts/notebooks/kmeans_ecg200_shapelets.ipynb`

**Next**
- Package results into protocol-style per-cluster summaries and exportable tables.
- Add explanation-stability checks across seeds and feature rankings.
- Port the same pipeline to the picoclimate dataset or expand clustering baselines.

**Possible questions/concerns**
- Should deliverable priority be protocol-aligned fixed outputs or notebook demonstration quality?
- For immediate next step, prefer real picoclimate windows now or additional baseline families first?

### 2026-04-21 (Documentation consolidation and tracking alignment)

**Experimentations**
- Consolidated governance documentation into one source of truth.

**Results (numbers, tables, plots)**
- Merged protocol, internship gap analysis, and skills matrix into `docs/GAP_ANALYSIS.md`.
- Renamed weekly tracking document to `docs/PROGRESS.md`.
- Updated root markdown references to the new names.
- Added ECG5000 extension workflow cells in `scripts/notebooks/exkmc_blobs_experiment.ipynb` (dataset path, unsupervised k selection, ExKMC + KMeans comparison).

**Insights**
- A single governance document reduces duplication and improves reporting consistency.

**Failures / issues / risks**
- External notes or bookmarks may still reference old file names.
- Full multi-method benchmark evidence still needs execution and archiving.

**Implementation details**
- Removed superseded docs replaced by consolidated governance content.
- Preserved prior technical progress history for continuity.

**Next**
- Run protocol-complete benchmark set and log metrics by seed.
- Add explanation stability summary (feature overlap and fidelity consistency).

**Possible questions/concerns**
- Should priority be real picoclimate runs now, or broader synthetic method comparisons first?

### 2026-04-21 (Roma taxi dataset onboarding for spatio-temporal benchmarking)

**Experimentations**
- Inspected CRAWDAD Roma taxi raw assets and extracted the February trace locally.
- Designed an EDA workflow for scalable parsing and feature construction on large mobility traces.

**Results (numbers, tables, plots)**
- Confirmed archive structure: one trace file (`taxi_february.txt`).
- Confirmed raw line format: `DRIVER_ID;TIMESTAMP;POINT(latitude longitude)`.
- Created dataset note: `data/roma-taxi/README.md`.

**Insights**
- The dataset is strong for real-world spatio-temporal benchmarking, especially for route/mobility structure discovery.
- Feature engineering into fixed windows is required before KMeans/ExKMC comparison.

**Failures / issues / risks**
- No direct task-specific cluster ground truth; external metrics are limited.
- Full raw trace is large, so chunked/sampled EDA is necessary to keep iteration speed acceptable.

**Implementation details**
- Added repository pointer in `data/README.md`.
- Added local-only ignore rules for large raw archive and extracted traces.
- Added a new EDA notebook for Roma taxi in `scripts/notebooks/`.

**Next**
- Run the new Roma taxi notebook end-to-end and save summary outputs.
- Compare KMeans and ExKMC on the same engineered features and report stability across seeds.

**Possible questions/concerns**
- Should Roma taxi be a secondary benchmark after ECG200/ECG5000 baseline stabilization, or run in parallel from now?
