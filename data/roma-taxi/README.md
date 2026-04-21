# Roma Taxi Dataset Note

## Source

- Name: CRAWDAD `roma/taxi`
- DOI: `10.15783/C7QC7M`
- Primary citation:
  Lorenzo Bracciale, Marco Bonola, Pierpaolo Loreti, Giuseppe Bianchi,
  Raul Amici, Antonello Rabuffi, `roma/taxi`, https://doi.org/10.15783/C7QC7M

## Context

- City: Rome, Italy
- Period: 2014-02-01 to 2014-03-02
- Fleet size: about 320 taxis
- Sampling interval: about every 7 seconds
- Sanitization: driver names replaced with integer IDs

## Local Files

- `roma-taxi-readme.txt`: provider instructions, ethics/legal note, citation text
- `taxi_february.tar.gz`: raw archive (local only)
- `extracted/taxi_february.txt`: extracted raw trace (local only)

## Raw Trace Format

Each line is:

`DRIVER_ID;TIMESTAMP;POINT(latitude longitude)`

Example:

`156;2014-02-01 00:00:00.739166+01;POINT(41.8836718276551 12.4877775603346)`

## Suggested Preprocessing for This Repository

1. Parse `driver_id`, timestamp, latitude, and longitude.
2. Sort by (`driver_id`, timestamp).
3. Build fixed windows (for example 15-min or 60-min bins) per driver.
4. Engineer stable features for clustering:
   - mean/std latitude and longitude
   - point count per bin
   - optional speed or displacement aggregates
   - cyclical time features (sin/cos of minute-of-day)
5. Standardize features before clustering.

## Benchmark Suitability

This dataset is suitable as a real-world spatio-temporal benchmark for KMeans and ExKMC pipelines, with two caveats:

- it has no direct cluster ground truth for the intended task
- it is large, so sampled or chunked EDA is recommended before full-scale runs

## Responsible Use Reminder

Use this dataset ethically and avoid any attempt to infer true identities from trace data.
Refer to `roma-taxi-readme.txt` for full policy text.
