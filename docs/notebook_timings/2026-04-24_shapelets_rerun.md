# Shapelet Notebook Rerun Timing

Date: 2026-04-24

This log records the total execution time for the two shapelet notebooks that were rerun after the root-detection and optional-summary fixes.

| Notebook | Result | Total runtime |
| --- | --- | ---: |
| [scripts/notebooks/shapelets_ecg200.ipynb](../../scripts/notebooks/shapelets_ecg200.ipynb) | Success | 98.36 s |
| [scripts/notebooks/shapelets_ecg5000.ipynb](../../scripts/notebooks/shapelets_ecg5000.ipynb) | Success | 1607.19 s |

Notes:
- These are total notebook runtimes, not per-cell timings.
- For future runs, enable cell-level timing capture so each executed cell records start/end/duration information.
- The current notebook timing convention is documented in [README.md](README.md).
