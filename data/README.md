# Data Folder Guide

This folder contains synthetic data regenerated to match the latest track-based picoclimate notes.

## Design Assumptions

- Track-based spatio-temporal data with **variable-length loc_id sequences** per track
- **10 Nantes tracks** and **6 Montpellier tracks** in the current fixture
- Track length is roughly **100-150 loc_id** per track after regeneration
- Each calendar day may contain **0-4 available slots** among `morning`, `noon`, `evening`, and `night`
- Days recorded per track vary across the 21-day horizon, and missing days are expected
- Each observation contains **23 measured variables** plus track, city, day, slot, and loc metadata
- Missing values are realistic and include:
  - cell-level missingness
  - block sensor outages

## 1) `tracks_measurements.csv` (Master track data)

- **Grain:** one record per (`track_id`, `date`, `time_slot`, `loc_id`)
- **Expected pattern:** each track has ordered `loc_index` values that act as pseudo-time along the path
- **Includes:** location metadata, temporal tags, 23 measured variables, and `true_regime`
- **Use cases:**
  - inspect missingness realism
  - test imputation strategies
  - explore spatial trajectories before representation learning or clustering

## 2) `window_features.csv` (Daily clustering representations)

- **Grain:** one record per (`track_id`, `date`)
- **Contains two representation families:**
  - `variable__slot_1..4` -> flattened daily slot profile (NaN when a slot is missing)
  - `variable__mean`, `variable__std`, `variable__trend` -> compact daily summary representation
- **Additional quality columns:**
  - `n_points` (observed rows contributing to the daily window)
  - `present_fraction` (completeness)

## 3) `variable_slices/` (One-variable day/slot files)

- **Grain:** one record per track/location point inside a single variable slice
- **Pattern:** `variable_slices/<variable>/day_<YYYY-MM-DD>_slot_<slot>.csv`
- **Current use:** primary working input for the present analysis flow
- **Use cases:**
  - inspect a single variable on a specific day and slot
  - feed sequence-aware methods that expect one variable at a time
  - mirror the long-form example discussed in the alignment notes

## 4) `cities/` (Per-city, per-date, per-slot, per-track hierarchy)

- **Grain:** one folder per city, then date, then slot, then track
- **Pattern:** `cities/<city>/<YYYY-MM-DD>/<time_slot>/<track_id>.csv`
- **Files inside each track folder:** one CSV matrix per track
- **Use cases:**
  - browse a single city, day, slot, or track without opening the master tables
  - compare daily and slot coverage side by side
  - inspect each track as a variable-by-location matrix

## Current Working Set

For now, use `variable_slices/` as the main data source when running the current workflow. The root master tables remain available for regeneration, but they are not the primary slice used in the analysis path.

The `cities/` hierarchy is rebuilt from `tracks_measurements.csv` and provides a per-city/per-date/per-slot/per-track matrix view of the same fixture.

## Labels

- `true_regime` exists in the master table and daily windows and can be used for controlled evaluation of clustering quality.

## Extra Documentation

- `csv_fields_explained.json`: detailed dictionary for the CSV outputs and slice layout.
- `metadata.json`: generation assumptions, parameters, and representation guidance.

## Roma Taxi Dataset (CRAWDAD)

The folder `data/roma-taxi/` contains CRAWDAD Roma taxi source artifacts used for real-world spatio-temporal benchmarking.

- Dataset note and citation summary: `data/roma-taxi/README.md`
- Provider instructions and ethics notice: `data/roma-taxi/roma-taxi-readme.txt`

Recommended use in this repository:

- keep raw archive and extracted traces local-only
- build sampled or windowed features for clustering workflows
- evaluate KMeans and ExKMC on identical engineered representations
