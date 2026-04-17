# Skills/Knowledge Matrix for the Internship

Scoring: 0 = missing, 1 = beginner, 2 = working, 3 = strong

| Requirement | Evidence in folder | Score | Action to reach internship-ready |
|---|---|---:|---|
| Classical clustering (K-Means, hierarchical) | notebooks 01, 02 + benchmark script | 3 | Add DBSCAN/GMM/Spectral comparisons in reports |
| Explainability methods (LIME/SHAP) | notebooks 03, 04 + surrogate_xai_pipeline | 3 | Evaluate explanation stability across seeds/samples |
| Clustering explanation framing | profile tables + local explanations | 2 | Standardize per-cluster explanation template |
| Spatio-temporal data handling | synthetic generator with trajectories/windows | 2 | Add temporal/route-split validation |
| Deep learning (PyTorch/TensorFlow) | deep_representation_clustering.py (PyTorch) | 2 | Extend to contrastive/sequence encoder |
| Representation-space clustering | latent clustering pipeline | 2 | Compare latent vs raw feature clustering statistically |
| Scientific rigor and reproducibility | protocol + deterministic seeds + exported outputs | 3 | Keep experiment logs for every run |
| Documentation quality | README + protocol + gap analysis | 3 | Maintain weekly findings notes |
| Multidisciplinary communication | cluster summaries for non-ML audience | 2 | Add architect-facing visual narratives |

## Priority actions (next 2 weeks)

Progress log: `docs/WEEKLY_PROGRESS.md`

1. Run all three scripts and archive outputs
2. Produce one 2-page report comparing methods on identical splits
3. Add stability analysis for SHAP/LIME explanations
4. Prepare a short slide explaining cluster meaning in urban terms
