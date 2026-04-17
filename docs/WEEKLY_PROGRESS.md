# Weekly Progress Log

Append weekly notes here for supervisor meetings. Prefer **short, factual bullets** and include **open questions** early.

## Template (copy/paste)

### YYYY-MM-DD (Week of YYYY-MM-DD → YYYY-MM-DD)

**Done**
- 

**Results (numbers, tables, plots)**
- 

**Issues / risks**
- 

**Next (1 week)**
- 

**Questions for supervisors**
- 

---

## Entries

### 2026-04-17 (ECG200 KMeans + XAI workflow)

**Done**
- Implemented KMeans clustering on ECG200 in two variants: raw time-point features and shapelet-distance features (with/without window z-normalization).
- Added unsupervised k selection using internal metrics (silhouette / Calinski–Harabasz / Davies–Bouldin) plus multi-seed stability (pairwise ARI across seeds).
- Benchmarked clusters post-hoc vs labels with ARI/NMI and majority-mapped accuracy (labels used only for evaluation).
- Built explainability via shallow decision-tree surrogates for cluster assignments, reporting train + CV fidelity and readable rules.
- Generated SHAP attributions on the surrogates; shapelet version also surfaces cluster-typical shapelets and summarizes cluster curve patterns (functional boxplots).

**Where**
- Notebooks: `scripts/notebooks/kmeans_ecg200.ipynb`, `scripts/notebooks/kmeans_ecg200_shapelets.ipynb`

**Next (1 week)**
- Package results into protocol-style per-cluster summaries + exportable tables.
- Add explanation-stability checks (repeat across seeds; compute top-feature overlap).
- Port the same pipeline to the picoclimate dataset (or extend to more clustering baselines — need guidance on priority).

**Questions for supervisors**
- Should the deliverable be “notebook demonstration of the workflow”, or full protocol-aligned outputs (saved tables + fixed per-cluster explanation format + stability)?
- For next week, do you prefer “apply to real picoclimate windows now” or “expand baseline methods (GMM/Agglo/DBSCAN/etc.) first”?
