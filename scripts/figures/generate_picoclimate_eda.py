#!/usr/bin/env python3
"""Generate EDA figures for picoclimate tracks dataset.
Outputs three PNG files into scripts/figures/:
 - picoclimate_track_length_dist.png
 - picoclimate_numeric_hist_topvars.png
 - picoclimate_sample_timeseries.png
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(HERE)
DATA_PATH = os.path.join(os.path.dirname(HERE), '..', 'data', 'picoclimate_test', 'tracks_measurements.csv')

os.makedirs(FIG_DIR, exist_ok=True)

print('Loading', DATA_PATH)
df = pd.read_csv(DATA_PATH)

# Compute track lengths
if 'track_id' in df.columns:
    lengths = df.groupby('track_id').size()
else:
    # fallback: assume each row is a track-window; approximate
    lengths = pd.Series([1])

# Plot distribution of track lengths
plt.figure(figsize=(6,3))
plt.title('Track length distribution')
sns.histplot(lengths, bins=30, kde=False)
plt.xlabel('Number of measurements per track')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'picoclimate_track_length_dist.png'), dpi=150)
plt.close()
print('Wrote track length figure')

# Numeric histograms for top variables: pick numeric cols excluding time/index
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
# remove id/time-like columns heuristically
remove = [c for c in num_cols if 'id' in c.lower() or 'time' in c.lower() or 'date' in c.lower()]
num_cols = [c for c in num_cols if c not in remove]
if len(num_cols) == 0:
    print('No numeric columns found for histograms')
else:
    topvars = num_cols[:6]
    fig, axes = plt.subplots(2, 3, figsize=(10,5))
    for ax, col in zip(axes.flatten(), topvars):
        sns.histplot(df[col].dropna(), bins=40, ax=ax, kde=False)
        ax.set_title(col)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'picoclimate_numeric_hist_topvars.png'), dpi=150)
    plt.close()
    print('Wrote numeric histograms')

# Sample time-series: pick one track and plot first 3 numeric vars
sample_track = None
if 'track_id' in df.columns:
    sample_track = df['track_id'].unique()[0]
    sdf = df[df['track_id'] == sample_track]
else:
    sdf = df

if len(num_cols) >= 3:
    cols = num_cols[:3]
else:
    cols = num_cols

plt.figure(figsize=(8,4))
for col in cols:
    plt.plot(sdf[col].values, label=col)
plt.legend()
plt.title(f'Sample time-series (track={sample_track})')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'picoclimate_sample_timeseries.png'), dpi=150)
plt.close()
print('Wrote sample time-series figure')
