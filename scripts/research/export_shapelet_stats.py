#!/usr/bin/env python3
"""Export per-shapelet statistics from existing pipeline outputs.
Looks for docs/reports/picoclimate_2026-05-29/ and reads selected shapelets
and the distance matrix if available.
Writes CSV: docs/reports/picoclimate_2026-05-29/shapelet_stats.csv
"""
import os
import json
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
REPORT_DIR = os.path.join(ROOT, 'docs', 'reports', 'picoclimate_2026-05-29')
OUT_CSV = os.path.join(REPORT_DIR, 'shapelet_stats.csv')

if not os.path.isdir(REPORT_DIR):
    raise SystemExit('Report dir not found: ' + REPORT_DIR)

# Try to load selected shapelets JSON or CSV
sel_json = os.path.join(REPORT_DIR, 'selected_shapelets.json')
metrics_csv = os.path.join(REPORT_DIR, 'picoclimate_shapelet_metrics.csv')

if os.path.exists(sel_json):
    with open(sel_json, 'r') as f:
        sel = json.load(f)
    # assume sel is list of dicts with keys 'id', 'series', 'start', 'length', 'values'
    rows = []
    for s in sel:
        vals = np.asarray(s.get('values', []), dtype=float)
        rows.append({'shapelet_id': s.get('id'), 'length': len(vals), 'mean': np.nanmean(vals) if vals.size else np.nan, 'std': np.nanstd(vals) if vals.size else np.nan, 'max': np.nanmax(vals) if vals.size else np.nan})
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print('Wrote', OUT_CSV)
elif os.path.exists(metrics_csv):
    dfm = pd.read_csv(metrics_csv)
    # try to aggregate per-shapelet columns if present
    # fallback: write metrics_csv as-is to shapelet_stats.csv
    dfm.to_csv(OUT_CSV, index=False)
    print('Copied metrics to', OUT_CSV)
else:
    raise SystemExit('No selected_shapelets.json or metrics CSV found in ' + REPORT_DIR)
