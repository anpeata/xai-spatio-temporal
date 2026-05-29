# Picoclimate Test Fixture (Synthetic)

This folder contains the regenerated **track-based synthetic** picoclimate fixture used by the notebooks, slides, and clustering scripts.

## Contents

- `tracks_measurements.csv` - master track table with one row per `track_id` x `date` x `time_slot` x `loc_id`
- `window_features.csv` - daily clustering table with flattened slot features and summaries
- `cities/<city>/<track_id>/` - per-city and per-track copies of the fixture tables plus a short track README
- `variable_slices/` - per-variable day/slot CSV exports in `variable_slices/<variable>/day_<YYYY-MM-DD>_slot_<slot>.csv`
- `metadata.json` - generation parameters, table counts, and slice layout
- `csv_fields_explained.json` - schema dictionary for the CSV outputs

Current working input:

- use `variable_slices/` for the present analysis workflow
- keep the root-level CSVs as regeneration inputs and compatibility artifacts
- `cities/` is reconstructed from `variable_slices/` and now stores per-city/per-track copies of the data

## Current dataset stats

Generated parameters (see `metadata.json`):

- Cities: **Nantes**, **Montpellier**
- Tracks: **16 total** (**10 Nantes**, **6 Montpellier**)
- Track length: **102-137 loc_id** per track
- Days recorded per track: **6-14** across the 21-day horizon
- Slots per day: **1-4 observed slots** among the 4 possible slots (`morning`, `noon`, `evening`, `night`)
- Daily slices: **84 slices per variable** (`21 days x up to 4 slots/day`)

Table size:

- `tracks_measurements.csv`: **38,703 rows × 32 columns**
- `window_features.csv`: **165 rows × 196 columns**
- `cities/`: **2 city folders** with **16 track folders** in total

Missingness summary:

- Randomly missing loc_id rows per slot (~8%)
- Random NaNs in measured variables (~5%)
- Missing days and missing slots are allowed, so a track can have 0-4 available recordings on a calendar day

Hierarchy notes:

- `cities/Nantes/<track_id>/` and `cities/Montpellier/<track_id>/` contain per-track copies of `tracks_measurements.csv` and `window_features.csv`
- The root-level master CSVs remain the canonical inputs for regeneration and compatibility with the notebooks/scripts in this repo

## Regeneration

Run `scripts/data/regenerate_picoclimate_fixture.py` to rebuild the fixture locally:

```bash
python scripts/data/regenerate_picoclimate_fixture.py --data-dir data/picoclimate_test --seed 20260529 --min-loc 100 --max-loc 150 --export-variable-slices
```

This keeps the track order stable, trims each track into the new length range, rebuilds `window_features.csv`, refreshes the variable slice exports, and regenerates the per-city/per-track hierarchy.
