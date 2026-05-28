# Picoclimate Test Fixture (Synthetic)

This folder contains a **track-based synthetic** spatio-temporal dataset used as a stable fixture for notebooks and scripts.

## Contents

- `tracks_measurements.csv` — track-level table (one row per track × loc_id × day × slot)
- `tracks_measurements_reduced.csv` — reduced sample (Nantes=10 tracks, Montpellier=6 tracks)
- `metadata.json` — generation parameters and variable specs
- `csv_fields_explained.json` — schema dictionary for the CSV

## Current dataset stats

Generated parameters (see `metadata.json`):

- Cities: **Nantes**, **Montpellier**
-- Tracks: **16 total** (Nantes: 10, Montpellier: 6) — reduced sample preserved in `tracks_measurements_reduced.csv`
- Track length: **100-200 loc_id** per track
- Days: **21 total** (each track appears on 6-14 days)
- Slots per day: **1-4** (`morning`, `noon`, `afternoon`, `night`)
- Step spacing: **10 minutes** between loc_id entries within a slot

Table size:

- `tracks_measurements.csv`: **205056 rows × 32 columns**
- `tracks_measurements_reduced.csv`: **53054 rows × 32 columns** (includes header)

Missingness summary:

- Randomly missing loc_id rows per slot (~8%)
- Random NaNs in measured variables (~5%)

## Regeneration

The track-based generator is not scripted yet. If you need a reusable script,
ask and we can add one based on the current parameters in `metadata.json`.
