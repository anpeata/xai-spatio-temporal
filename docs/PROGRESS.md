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
- Next (1 week)
- Questions for supervisors

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

**Next (1 week)**
- 

**Questions for supervisors**
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

**Next (1 week)**
- Package results into protocol-style per-cluster summaries and exportable tables.
- Add explanation-stability checks across seeds and feature rankings.
- Port the same pipeline to the picoclimate dataset or expand clustering baselines.

**Questions for supervisors**
- Should deliverable priority be protocol-aligned fixed outputs or notebook demonstration quality?
- For immediate next step, prefer real picoclimate windows now or additional baseline families first?

### 2026-04-21 (Documentation consolidation and tracking alignment)

**Experimentations**
- Consolidated governance documentation into one source of truth.

**Results (numbers, tables, plots)**
- Merged protocol, internship gap analysis, and skills matrix into `docs/GAP_ANALYSIS.md`.
- Renamed weekly tracking document to `docs/PROGRESS.md`.
- Updated root markdown references to the new names.

**Insights**
- A single governance document reduces duplication and improves reporting consistency.

**Failures / issues / risks**
- External notes or bookmarks may still reference old file names.
- Full multi-method benchmark evidence still needs execution and archiving.

**Implementation details**
- Removed superseded docs replaced by consolidated governance content.
- Preserved prior technical progress history for continuity.

**Next (1 week)**
- Run protocol-complete benchmark set and log metrics by seed.
- Add explanation stability summary (feature overlap and fidelity consistency).

**Questions for supervisors**
- Should priority be real picoclimate runs now, or broader synthetic method comparisons first?
