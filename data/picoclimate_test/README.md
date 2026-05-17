# Picoclimate Test Fixture (Synthetic)

This folder contains a **small, tracked synthetic** spatio-temporal dataset used as a stable fixture for notebooks and scripts.

## Contents

- `raw_measurements.csv` — point-level table (one row per location × day × slot)
- `window_features.csv` — daily window representations (one row per location × day)
- `metadata.json` — generation parameters and variable specs
- `csv_fields_explained.json` — schema dictionary for both CSVs
- `raw_samples.png`, `window_samples.png` — small visual samples of the tables

## Current dataset stats

Generated parameters (see `metadata.json`):

- Cities: **Nantes**, **Montpellier**
- Locations: **24 total** (12 per city)
- Days: **30** (2025-09-01 → 2025-09-30)
- Slots per day: **4** (`06:00`, `12:00`, `18:00`, `23:00`)

Table sizes:

- `raw_measurements.csv`: **2880 rows × 37 columns**
- `window_features.csv`: **720 rows × 167 columns**

Breakdown by city:

- Raw rows: **1440 Nantes**, **1440 Montpellier**
- Window rows: **360 Nantes**, **360 Montpellier**

Missingness summary:

- Overall missing fraction (measured variables): **0.0969**
- Block-outage rows (`missing_block_flag=1`): **155** (**5.382%**)

Window completeness (`present_fraction`) by city:

- Montpellier: mean **0.9048**, std **0.0436** (n=360)
- Nantes: mean **0.9015**, std **0.0480** (n=360)

## Regeneration

To regenerate these artifacts deterministically:

```powershell
D:\env\py128\python.exe scripts/data/generate_picoclimate_data.py \
  --outdir data/picoclimate_test \
  --seed 42 \
  --city "Nantes,Montpellier" \
  --n-locations 24 \
  --days 30
```
