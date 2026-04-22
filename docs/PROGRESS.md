# Progress Log

Last updated: 2026-04-22

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
- Notebooks: `scripts/notebooks/kmeans_test_temporal.ipynb`, `scripts/notebooks/kmeans_test_temporal_shapelets.ipynb`

**Next**
- Package results into protocol-style per-cluster summaries and exportable tables.
- Add explanation-stability checks across seeds and feature rankings.
- Port the same pipeline to the picoclimate dataset or expand clustering baselines.

**Possible questions/concerns**
- Should deliverable priority be protocol-aligned fixed outputs or notebook demonstration quality?
- For immediate next step, prefer real picoclimate windows now or additional baseline families first?

### 2026-04-21 (Documentation consolidation and Roma taxi onboarding)

**Experimentations**
- Consolidated governance documentation into one source of truth.
- Inspected CRAWDAD Roma taxi raw assets and extracted the February trace locally.
- Designed an EDA workflow for scalable parsing and feature construction on large mobility traces.

**Results (numbers, tables, plots)**
- Merged protocol, internship gap analysis, and skills matrix into `docs/GAP_ANALYSIS.md`.
- Renamed weekly tracking document to `docs/PROGRESS.md`.
- Updated root markdown references to the new names.
- Added ECG5000 extension workflow cells in `scripts/notebooks/exkmc_blobs_experiment.ipynb` (dataset path, unsupervised k selection, ExKMC + KMeans comparison).
- Confirmed archive structure: one trace file (`taxi_february.txt`).
- Confirmed raw line format: `DRIVER_ID;TIMESTAMP;POINT(latitude longitude)`.
- Created dataset note: `data/roma-taxi/README.md`.

**Insights**
- A single governance document reduces duplication and improves reporting consistency.
- The dataset is strong for real-world spatio-temporal benchmarking, especially for route/mobility structure discovery.
- Feature engineering into fixed windows is required before KMeans/ExKMC comparison.

**Failures / issues / risks**
- External notes or bookmarks may still reference old file names.
- Full multi-method benchmark evidence still needs execution and archiving.
- No direct task-specific cluster ground truth; external metrics are limited.
- Full raw trace is large, so chunked/sampled EDA is necessary to keep iteration speed acceptable.

**Implementation details**
- Removed superseded docs replaced by consolidated governance content.
- Preserved prior technical progress history for continuity.
- Added repository pointer in `data/README.md`.
- Added local-only ignore rules for large raw archive and extracted traces.
- Added a new EDA notebook for Roma taxi in `scripts/notebooks/`.

**Next**
- Run protocol-complete benchmark set and log metrics by seed.
- Add explanation stability summary (feature overlap and fidelity consistency).
- Run the new Roma taxi notebook end-to-end and save summary outputs.
- Compare KMeans and ExKMC on the same engineered features and report stability across seeds.

**Possible questions/concerns**
- Should priority be real picoclimate runs now, or broader synthetic method comparisons first?
- Should Roma taxi be a secondary benchmark after ECG200/ECG5000 baseline stabilization, or run in parallel from now?

### 2026-04-22 (Roma taxi EDA and temporal KMeans refactor)

**Experimentations**
- Executed Roma taxi EDA notebook end-to-end with fast mode tuning.
- Parsed 21.8 M raw trajectory points from February trace.
- Engineered 15-minute temporal windows into spatio-temporal feature vectors.
- Ran unsupervised k selection (Silhouette, Calinski-Harabasz, Davies-Bouldin) across seeds.
- Refactored temporal KMeans notebooks to single-view pipelines (raw-only and shapelet-only workflows).
- Renamed temporal notebooks to dataset-agnostic names for reuse.
- Executed the raw temporal KMeans pipeline end-to-end on ECG200.

**Results (numbers, tables, plots)**
- Dataset size: 1.498 GB (extracted taxi_february.txt)
- Rows sampled/processed: 40,000 for EDA preview
- Window feature table: 74,478 windows × 10 features (lat, lon, time stats, distance, speed, direction)
- Optimal k selection: k=2 (across multi-seed stability)
- Cluster size distribution and silhouette summary computed
- Spatial footprint map: Roma metropolitan area coverage clearly visible
- Top drivers by activity: driver IDs ranked by point count (1,200+ points for most active)
- ECG200 raw temporal KMeans: best k=3, mapped accuracy=0.78, ARI=0.3120, NMI=0.2039, silhouette=0.4069
- Surrogate explainability: train fidelity=0.985, CV fidelity=0.94
- Top surrogate/SHAP features: `t_41`, `t_30` (with `t_12` minor)

**Insights**
- Fast mode (chunked sampling) makes large-scale EDA feasible without exhausting memory.
- Feature engineering into fixed 15-min windows captures meaningful temporal structure.
- Silhouette-based k selection favors low k (2–3) for taxi route similarity, suggesting strong bimodal structure (central vs peripheral routes).
- Driver activity distribution is Zipfian; top 50 drivers represent significant trace density.
- On ECG200 raw time-series, unsupervised selection favors a 3-cluster temporal structure despite 2 ground-truth classes.
- Surrogate rules are compact and dominated by `t_41` and `t_30`, improving interpretability.

**Failures / issues / risks**
- ExKMC comparison deferred (cell 8 not executed) to avoid overhead on large windowed dataset.
- Chunk size for final full-run still needs tuning for production use; current fast mode is 40K-row preview.
- Ground truth for route quality/driver behavior clusters is external; only intrinsic metrics available.
- Shapelet temporal test execution was deferred in the latest pass due compute/runtime budget.

**Implementation details**
- Fast mode enabled: MAX_ROWS=40000, STRIDE=900 seconds (15 min), KMEANS_N_INIT=3 for quick convergence
- Multi-seed evaluation: 3 seeds for stability
- Haversine distance used for spatial feature engineering
- Filtering: removed rows with invalid coordinates or null timestamps
- Notebook paths after rename: `scripts/notebooks/kmeans_test_temporal.ipynb` and `scripts/notebooks/kmeans_test_temporal_shapelets.ipynb`

**Next**
- Run full-dataset window table construction with production chunk size.
- Compare KMeans stability across k=2 and k=3 with extended seed list.
- Optional: apply ExKMC if stability gains justify overhead; else use KMeans baseline.
- Export cluster summaries and route pattern interpretations.
- Execute the shapelet temporal notebook end-to-end and log comparable metrics to the raw pipeline.

**Possible questions/concerns**
- Is k=2 truly optimal or artifact of sampling? Full data k selection recommended before finalizing.
- Should ExKMC be run despite cost, or defer to after ECG200/ECG5000 benchmarks complete?
- Route interpretation: should cluster summaries include driver behavior profiles or remain trajectory-focused?
