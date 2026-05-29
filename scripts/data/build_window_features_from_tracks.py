"""Aggregate `tracks_measurements.csv` into `window_features.csv`.
Produces one row per `track_id` x `date` with flattened slot columns: `<var>__slot_<i>` where i starts at 1.
Missing slots are left as NaN.
"""
from pathlib import Path

import numpy as np
import pandas as pd

INPUT = Path('data/picoclimate_test/tracks_measurements.csv')
OUTPUT = Path('data/picoclimate_test/window_features.csv')


def _trend_four_points(values: pd.Series) -> float:
    arr = values.to_numpy(dtype=float)
    x = np.arange(len(arr), dtype=float)
    ok = np.isfinite(arr)
    if ok.sum() < 2:
        return float('nan')
    x_ok = x[ok]
    y_ok = arr[ok]
    xm = x_ok.mean()
    denom = ((x_ok - xm) ** 2).sum()
    if denom <= 0:
        return float('nan')
    return float(((x_ok - xm) * (y_ok - y_ok.mean())).sum() / denom)


def _build_window_features(df: pd.DataFrame) -> pd.DataFrame:
    id_cols = ['track_id', 'city', 'date', 'time_slot', 'slot_index']
    for c in df.columns:
        if c in id_cols:
            continue
        df[c] = pd.to_numeric(df[c], errors='coerce')

    value_cols = [c for c in df.columns if c not in id_cols and df[c].dtype != object]
    groups = []
    for (track_id, date), g in df.groupby(['track_id', 'date'], sort=False):
        row = {
            'track_id': track_id,
            'date': date,
            'city': g['city'].mode().iloc[0] if not g['city'].mode().empty else None,
            'time_slot': g['time_slot'].mode().iloc[0] if not g['time_slot'].mode().empty else None,
            'n_points': int(g.shape[0]),
            'present_fraction': float(g[value_cols].notna().to_numpy().mean()) if value_cols else float('nan'),
        }

        ordered = g.sort_values('slot_index')
        for slot in sorted(g['slot_index'].dropna().unique()):
            slot = int(slot)
            sg = g[g['slot_index'] == slot]
            for col in value_cols:
                row[f'{col}__slot_{slot + 1}'] = sg[col].mean()

        for col in value_cols:
            row[f'{col}__mean'] = float(g[col].mean(skipna=True))
            row[f'{col}__std'] = float(g[col].std(skipna=True))
            row[f'{col}__trend'] = _trend_four_points(ordered[col])

        mode = g['true_regime'].mode(dropna=True)
        row['true_regime'] = mode.iloc[0] if not mode.empty else None
        groups.append(row)

    out = pd.DataFrame(groups)
    cols = ['track_id', 'date', 'city', 'time_slot', 'n_points', 'present_fraction', 'true_regime']
    cols += [c for c in out.columns if c not in cols]
    return out[cols]


if __name__ == '__main__':
    print('Reading', INPUT)
    df = pd.read_csv(INPUT, low_memory=False)
    out = _build_window_features(df)
    print('Writing', OUTPUT, 'shape=', out.shape)
    out.to_csv(OUTPUT, index=False)
    print('Done')
