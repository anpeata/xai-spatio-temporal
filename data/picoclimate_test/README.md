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
- Locations: **50 total** (25 per city)
- Days: **30** (2025-09-01 → 2025-09-30)
- Slots per day: **4** (`06:00`, `12:00`, `18:00`, `23:00`)

Table sizes:

- `raw_measurements.csv`: **6000 rows × 37 columns**
- `window_features.csv`: **1500 rows × 167 columns**

Breakdown by city:

- Raw rows: **3000 Nantes**, **3000 Montpellier**
- Window rows: **750 Nantes**, **750 Montpellier**

Missingness summary:

- Overall missing fraction (measured variables): **0.0945**
- Block-outage rows (`missing_block_flag=1`): **359** (**5.983%**)

Window completeness (`present_fraction`) by city:

- Montpellier: mean **0.9006**, std **0.0497** (n=750)
- Nantes: mean **0.9104**, std **0.0475** (n=750)

## Regeneration

To regenerate these artifacts deterministically:

```powershell
D:\env\py128\python.exe scripts/data/generate_picoclimate_data.py `
  --outdir data/picoclimate_test `
  --seed 42 `
  --city "Nantes,Montpellier" `
  --n-locations 50 `
  --days 30
```
