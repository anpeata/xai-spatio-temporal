# Data Folder Guide

This folder contains synthetic data regenerated to match the latest internship notes.

## Design Assumptions

- Exactly **4 data points per day** (slots: morning, noon, evening, night)
- Each data point contains **23 measured variables**
- Values follow a **spatio-temporal structure** based on a linear combination of:
  - spatial latent factors (urbanity, vegetation, water proximity)
  - temporal latent factors (diurnal, seasonal, weekend effects)
- Missing values are realistic and include:
  - cell-level missingness
  - block sensor outages

## 1) `raw_measurements.csv` (Point-level data)

- **Grain:** one record per (`timestamp`, `location_id`)
- **Expected pattern:** for each (`location_id`, `date`), there are 4 rows (`slot_index` 0..3)
- **Includes:** location metadata, temporal tags, 23 measured variables, `true_regime`, and `missing_block_flag`
- **Use cases:**
  - inspect missingness realism
  - test imputation strategies
  - explore spatio-temporal dynamics before representation

## 2) `window_features.csv` (Daily clustering representations)

- **Grain:** one record per (`date`, `location_id`)
- **Contains two representation families:**
  - `variable__slot_1..4` → flattened 4x23 profile (direct daily sequence representation)
  - `variable__mean`, `variable__std`, `variable__trend` → compact summary representation
- **Additional quality columns:**
  - `n_points` (should be 4)
  - `present_fraction` (completeness)

## Labels

- `true_regime` exists in both tables and can be used for controlled evaluation of clustering quality.

## Extra Documentation

- `csv_fields_explained.json`: detailed dictionary for both CSV files.
- `metadata.json`: generation assumptions, parameters, and representation guidance.
