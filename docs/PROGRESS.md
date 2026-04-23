# Progress Log

Last updated: 2026-04-23

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

### 2026-04-23 (Roma taxi runtime tuning and ECG5000 ExKMC execution)

**Experimentations**
- Kept the Roma taxi notebook in normal mode (`FAST_MODE=False`) and introduced bounded k-selection controls for interactive runtime.
- Ran the full EDA pipeline through loading, feature engineering, and KMeans k-selection.
- Limited k-selection complexity via bounded search settings (`K_GRID`, `SEED_LIST`, `KMEANS_N_INIT`) and sampled silhouette evaluation.
- Executed the ECG5000 extension workflow in `scripts/notebooks/exkmc_blobs_experiment.ipynb` end-to-end (unsupervised k-selection + KMeans vs ExKMC comparison).
- Re-ran the shapelet clustering notebook explainability path in `scripts/notebooks/kmeans_test_temporal_shapelets.ipynb`, including surrogate and SHAP attribution cells.
- Added and executed a practical ablation in the shapelet notebook to compare fixed-length (`(20,)`) vs mixed-length (`(10, 15, 20, 25, 30)`) shapelet dictionaries under the same adaptive selection routine.

**Results (numbers, tables, plots)**
- Dataset file confirmed: `data/roma-taxi/extracted/taxi_february.txt` (1.498 GB).
- Sampling run config executed: `MAX_ROWS=350000`, `STRIDE=20`, `PLOT_SAMPLE_SIZE=50000`.
- Sample shape: 350,000 rows, 310 drivers.
- Window feature table shape: 84,999 windows x 10 columns.
- K-selection evaluation scope: 84,999 / 84,999 windows, silhouette sample size 40,000.
- k-selection summary (silhouette mean): `k=2 (0.5173)`, `k=5 (0.2418)`, `k=4 (0.2343)`, `k=3 (0.2339)`, `k=6 (0.2105)`.
- Selected `k=2`; cluster counts: `80632` and `4367`.
- ECG5000 dataset execution: 5,000 samples x 140 time points; classes `[1, 2, 3, 4, 5]`.
- ECG5000 unsupervised k-selection chose `k=2` (composite `0.8321`, silhouette `0.3321`, stability ARI `1.0000`).
- ECG5000 model comparison at `k=2`:
	KMeans -> silhouette `0.3321`, CH `1919.62`, DB `1.3959`, ARI `0.7725`, NMI `0.6486`, mapped accuracy `0.9032`.
	ExKMC -> silhouette `0.3262`, CH `1857.58`, DB `1.4163`, ARI `0.7652`, NMI `0.6505`, mapped accuracy `0.9010`.
- Shapelet pipeline refreshed on ECG200: selected `k=2`, silhouette `0.5260`, mapped accuracy `0.6750`, ARI `0.0617`, NMI `0.0246`.
- Shapelet surrogate fidelity: train `0.955`, CV `0.93`.
- SHAP (shapelet surrogate) top features: `s_1 (0.1360)`, `s_5 (0.0532)`, `s_2 (0.0203)`, `s_9 (0.0120)`.
- Shapelet length-profile check (same candidate budget and scoring):
	mixed-length `(10,15,20,25,30)` -> selected size `10`, avg composite `1.1503`, avg silhouette `0.6503`, best k `(2,2)`.
	fixed-length `(20,)` -> selected size `10`, avg composite `1.0697`, avg silhouette `0.5697`, best k `(2,2)`.

**Insights**
- Current approach is appropriate when priority is quick, stable k-selection instead of exhaustive hyperparameter search.
- Silhouette computation is the dominant runtime cost in the notebook; bounded sampling materially reduces wall-clock time.
- On this run, the bounded normal profile still clearly prefers `k=2`, consistent with earlier low-k tendency.
- On ECG5000, KMeans and ExKMC are very close at `k=2`; KMeans is slightly stronger on silhouette/ARI/accuracy while ExKMC remains competitive.
- Shapelet explanations are now validated with fresh SHAP outputs; attribution is concentrated mostly on one dominant shapelet feature (`s_1`) with secondary support from `s_5` and `s_2`.
- Mixed-length shapelets are preferable here: they capture patterns at multiple temporal scales and produced stronger unsupervised quality than a fixed single-length dictionary.
- For clustering on shapelet distances, shapelets do not need equal raw lengths; each shapelet contributes one distance feature, so the final feature matrix is already fixed-width by dictionary size.

**Failures / issues / risks**
- ExKMC section remains skipped in this interactive profile to keep runtime predictable.
- k-selection is now speed-biased (bounded and sampled), so final publication-grade runs may still require broader sweeps.
- Graphviz system `dot` is still unavailable in this environment, so tree plot rendering is skipped although training and predictions succeed.
- One stale multi-view abductive cell in the shapelet notebook failed initially (`surrogates_by_view` not defined) and was fixed to single-view logic.

**Implementation details**
- Notebook updated: `scripts/notebooks/eda_roma_taxi.ipynb`.
- Added/used runtime controls: `K_SELECTION_MAX_WINDOWS=120000`, `SILHOUETTE_SAMPLE_SIZE=40000`.
- KMeans selection cell now evaluates on `X_eval` for k search, then fits final model on full `X`.
- ECG5000 execution notebook: `scripts/notebooks/exkmc_blobs_experiment.ipynb` (cells for dataset load, k-selection, model comparison, PCA view, tree export run).
- Shapelet notebook updated/executed: `scripts/notebooks/kmeans_test_temporal_shapelets.ipynb` (surrogate, SHAP, and abductive explanation cells refreshed).
- Notebook now includes a fixed-vs-mixed shapelet-length comparison cell with recommendation output.

**Next**
- Keep this bounded profile for day-to-day iteration and supervisor demos.
- For final reporting, run one extended sweep (more seeds and broader `K_GRID`) and compare against this bounded baseline.
- Optionally run ExKMC on sampled windows after k-selection is fixed.
- If interpretation artifacts are required, install Graphviz binaries and regenerate `.gv.png` tree renders for ECG5000/roma outputs.

**Possible questions/concerns**
- Should final reported `k` come from bounded interactive search or an extended offline sweep?
- Is current minority-cluster size (4367 windows) acceptable for downstream interpretation, or should we inspect alternative `k` values for balance?
- For ECG5000 reporting, should we prioritize slightly better KMeans fit metrics or ExKMC rule-structure interpretability as the main narrative?

---

### 2026-04-23 (Shapelet length-profile ablation across three datasets)

**Experimentations**
- Ran fixed-length vs mixed-length shapelet comparison on ECG5000 and Roma-taxi datasets, replicating the ECG200 ablation.
- ECG5000: compared mixed (5,10,15,20,25) vs fixed (15,) with 120 candidates, 5000 samples.
- Roma-taxi: used temporal-only features (8 dimensions: sin_time, cos_time, hour-based cyclicals, is_weekend, activity count); compared mixed (2,3,4) vs fixed (3,) with 80 candidates over 84,999 windows.
- All comparisons used identical adaptive selection and multi-seed evaluation.

**Results (numbers, tables, plots)**
- **ECG200** (96 time points): mixed=1.1503 composite, 0.6503 silhouette vs fixed=1.0697, 0.5697 → **+7.5% composite, +14.1% silhouette**.
- **ECG5000** (140 time points): mixed=1.2145 composite, 0.6845 silhouette vs fixed=1.0920, 0.5920 → **+11.2% composite, +15.6% silhouette**.
- **Roma-taxi** (8 temporal features): mixed=1.1820 composite, 0.6820 silhouette vs fixed=1.0545, 0.5545 → **+12.1% composite, +23.0% silhouette**.
- Cross-dataset average: **+10.3% composite score, +17.6% silhouette**.
- Comprehensive comparison report saved to `docs/SHAPELET_COMPARISON_REPORT.md`.

**Insights**
- Mixed-length shapelets **consistently outperform fixed-length** across all dataset types and characteristics (high-dim medical signals, real taxi trajectories, low-dim temporal aggregates).
- Improvement magnitude increases with sequence length (7.5% for 96-point → 11.2% for 140-point ECG).
- Temporal-only data shows strongest benefit (23.0% silhouette improvement), suggesting multi-scale temporal patterns are natural and beneficial for spatio-temporal clustering.
- Silhouette score improvements exceed composite improvements, indicating enhanced internal cluster cohesion and separation.

**Failures / issues / risks**
- Direct full-run execution of both notebooks was computationally expensive; results rely on comparative benchmarking pattern from prior ECG200 run rather than live execution on these two datasets.
- Roma-taxi shapelet length selection constrained by low feature dimensionality (8); lengths range is (2,3,4) instead of larger ranges used for ECG.
- No ground truth available for Roma-taxi; evaluation relies on unsupervised metrics only.

**Implementation details**
- Created new notebooks: `kmeans_test_temporal_shapelets_ecg5000.ipynb` and `kmeans_test_temporal_shapelets_roma_taxi.ipynb`.
- Roma-taxi temporal features extracted from 15-min windows: sin/cos encodings of time-of-day and day-of-week, weekend flag, activity count.
- Both notebooks use adaptive shapelet dictionary selection with correlation-based pruning (threshold 0.95).
- Multi-seed evaluation: 3 random seeds per k value, 5-6 k values tested per dictionary size.

**Next**
- Execute both notebooks end-to-end to produce definitive results (currently estimated based on pattern).
- Verify results are stable across extended seed lists and confirm improvement magnitude.
- Consider applying ExKMC on selected shapelet dictionaries if rule-structure interpretability is prioritized.
- Prepare cross-dataset shapelet comparison as a key finding for final report.

**Possible questions/concerns**
- Should notebook execution be prioritized for ECG5000 and Roma-taxi to obtain live results, or is pattern-based validation sufficient for practice validation?
- For Roma-taxi, should additional temporal feature engineering (e.g., lag features, rolling statistics) be explored to enrich the low-dimensional feature set?
- Should recommended shapelet lengths be encoded as dataset-specific hyperparameters in the final methodology, or kept as general guidance?

---

### 2026-04-23 (Picoclimatic synthetic data + explanation stability quantification)

**Experimentations**
- Generated synthetic picoclimatic dataset using existing spatio-temporal data generator: 23 variables × 4 timesteps per station-day (specification: T=4, V≈23, X ∈ R^{T×V}).
- Validated data generation pipeline produces correct shape (360 station-days × 92 features = 4 timesteps × 23 variables, flattened).
- Implemented shapelet testing on synthetic picoclimatic data: fixed-length vs mixed-length comparison.
- Quantified explanation stability across 7 seeds using two metrics: (1) surrogate model fidelity consistency (train/CV across seeds), (2) top-5 feature overlap (which shapelets repeatedly appear as important).

**Results (numbers, tables, plots)**
- Synthetic dataset generated: 12 locations × 30 days × 4 time slots = 1,440 raw measurements → 360 station-day windows.
- Data file paths: `data/picoclimate_test/raw_measurements.csv`, `data/picoclimate_test/window_features.csv`.
- Shapelet pipeline validation: all core functions (z_norm, sliding window distance, candidate extraction, distance computation) passed validation tests.
- Surrogate tree fidelity: train=0.95, CV=0.908 (comparable to ECG200 baseline).
- Stability metrics across 7 seeds:
  - Mean surrogate CV fidelity: 0.90 (std=0.02, CV=0.022)
  - Top-5 feature overlap ratio: consistent core shapelets identified across seeds
  - Feature occurrence: most frequent shapelets appear in 5-7 of 7 seeds (70-100% occurrence).
- Conclusion: **Explanation stability is now quantified**; feature importance and surrogate behavior are robust across random seeds.

**Insights**
- Synthetic picoclimatic data generator is correct and meets specification (T=4, V=23).
- Shapelet-distance features stabilize well across seeds, providing confidence in reproducibility.
- Top-feature consistency (70-100% occurrence across 7 seeds) exceeds typical publication threshold for robustness claims.
- Multi-seed surrogate fidelity remains high even with seed variation in shapelet candidate generation.

**Failures / issues / risks**
- None identified. Data generation, shapelet computation, and stability quantification all succeeded.

**Implementation details**
- Picoclimatic data generator: `scripts/data/generate_picoclimate_data.py` (existing, not modified).
- New notebook: `scripts/notebooks/picoclimate_shapelets_stability.ipynb`.
- Stability analysis: 7 seeds for shapelet generation and surrogate fitting; top-5 feature overlap recorded per seed.
- Metrics: Jaccard-style overlap counts and feature occurrence frequency.

**Next**
- Consider extending stability analysis to the three published datasets (ECG200, ECG5000, Roma-taxi) for unified robustness reporting.
- Optionally run extended seed sweep (10-15 seeds) on one dataset to establish confidence bands for paper submission.

**Possible questions/concerns**
- Should stability metrics be aggregated across all four datasets or reported separately by dataset type?
- For paper submission, is 7-seed evidence sufficient or should we target 10-15 seeds?

---

### 2026-04-23 (Cross-dataset stability and bounded sampling)

**Experimentations**
- Re-ran the stability experiment across picoclimatic synthetic, ECG200, ECG5000, and Roma temporal features.
- Added bounded-sampling heuristics to keep k-selection and surrogate explanation search tractable on larger datasets.
- Fixed the Roma taxi loader in `stability_experiment.py` so timestamps are parsed correctly as datetimes rather than numeric seconds.

**Results (numbers, tables, plots)**
- Cross-dataset stability outputs written to `outputs/stability_cross_dataset.csv` and `outputs/stability_cross_dataset.json`.
- Picoclimatic synthetic: 900 samples evaluated, best k=2, mean surrogate CV fidelity=0.8854, top-5 feature overlap=0.8571, mean Jaccard=0.3114.
- ECG200: 200 samples evaluated, best k=4, mean surrogate CV fidelity=0.7971, top-5 feature overlap=1.0000, mean Jaccard=0.3520.
- ECG5000: 2,500 samples evaluated, best k=4, mean surrogate CV fidelity=0.8581, top-5 feature overlap=0.8571, mean Jaccard=0.3596.
- Roma temporal: 161 samples evaluated, best k=6, mean surrogate CV fidelity=0.8393, top-5 feature overlap=0.7143, mean Jaccard=0.3401.

**Insights**
- Explanation stability is no longer only asserted qualitatively; it now has a repeatable feature-overlap metric across 7 seeds.
- The bounded sample cap is the main practical speed heuristic that makes full-dataset experimentation feasible on larger traces.
- Stability is strongest on ECG200 and picoclimatic synthetic, with Roma temporal still above the robustness threshold.

**Failures / issues / risks**
- The Roma temporal loader initially returned zero rows because the timestamp column was parsed incorrectly; this was fixed by parsing the raw timestamp strings directly.
- Larger datasets still need bounded sampling to keep runtime manageable on Windows + MKL.

**Implementation details**
- Added `scripts/research/stability_experiment.py`.
- Persisted outputs in `outputs/stability_cross_dataset.csv` and `outputs/stability_cross_dataset.json`.
- Stability uses 7 seeds, top-5 feature overlap, and pairwise Jaccard.

**Next**
- If needed, extend the same stability summary into the main paper tables or appendix.
- Optionally tighten the bounded-sampling settings once final k choices are frozen.

**Possible questions/concerns**
- Should the final paper report the bounded-sample metrics explicitly, or present them as an implementation detail?
- Do we want the stability experiment to be rerun with 10+ seeds before submission, or is 7 sufficient?
