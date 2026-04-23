import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

print("Starting fast shapelet comparison...")

def extract_shapelets_fast(X, lengths, num_candidates, seed=42):
    np.random.seed(seed)
    n_samples, n_steps = X.shape
    shapelets = []
    for length in lengths:
        for _ in range(num_candidates // len(lengths)):
            sample_idx = np.random.randint(0, n_samples)
            start_idx = np.random.randint(0, n_steps - length + 1)
            shapelet = X[sample_idx, start_idx:start_idx + length].copy()
            std = np.std(shapelet)
            if std > 1e-8:
                shapelet = (shapelet - np.mean(shapelet)) / std
            shapelets.append(shapelet)
    return shapelets

def compute_distances_fast(X, shapelets):
    n_samples = X.shape[0]
    distances = np.zeros((n_samples, len(shapelets)))
    
    for i in range(n_samples):
        ts = X[i]
        ts_mean, ts_std = np.mean(ts), np.std(ts)
        ts_norm = (ts - ts_mean) / (ts_std + 1e-8) if ts_std > 1e-8 else ts - ts_mean
        
        for j, shapelet in enumerate(shapelets):
            max_corr = 0
            for k in range(len(ts_norm) - len(shapelet) + 1):
                segment = ts_norm[k:k + len(shapelet)]
                seg_std = np.std(segment)
                if seg_std > 1e-8:
                    corr = np.abs(np.dot(segment, shapelet) / (len(shapelet) * seg_std))
                    max_corr = max(max_corr, corr)
            distances[i, j] = 1 - max_corr
    return distances

def get_summary(df, dataset_name):
    summary = df.groupby('profile')[['avg_composite_score', 'avg_silhouette']].mean()
    summary['dataset'] = dataset_name
    return summary

# ECG5000 - Using subset for faster computation
print("\n=== ECG5000 (subset) ===")
ecg_train = pd.read_csv(r"D:\repositories\personal\xai-spatio-temporal\data\UCRArchive_2018\ECG5000\ECG5000_TRAIN.tsv", sep='\t', header=None)
ecg_test = pd.read_csv(r"D:\repositories\personal\xai-spatio-temporal\data\UCRArchive_2018\ECG5000\ECG5000_TEST.tsv", sep='\t', header=None)
X_ecg = pd.concat([ecg_train, ecg_test], ignore_index=True).iloc[:, 1:].values
# Use subset for speed
X_ecg = X_ecg[:1000]  # Use first 1000 samples
X_ecg = StandardScaler().fit_transform(X_ecg)
print(f"ECG5000 shape (subset): {X_ecg.shape}")

results_all = []
for seed in [0, 1]:  # Use 2 seeds for faster computation
    # Mixed
    shapelets_m = extract_shapelets_fast(X_ecg, (5, 10, 15, 20, 25), 100, seed)
    dist_m = compute_distances_fast(X_ecg, shapelets_m)
    for k in [3, 5]:
        km = KMeans(n_clusters=k, n_init=8, random_state=seed)
        labels = km.fit_predict(dist_m)
        sil = silhouette_score(dist_m, labels)
        for size in [15, 30]:
            top_f = np.argsort(np.var(dist_m, axis=0))[-min(size, len(shapelets_m)):]
            d_sel = dist_m[:, top_f]
            km_sel = KMeans(n_clusters=k, n_init=8, random_state=seed)
            labels_sel = km_sel.fit_predict(d_sel)
            sil_sel = silhouette_score(d_sel, labels_sel)
            results_all.append({'seed': seed, 'k': k, 'size': size, 'profile': 'mixed', 
                               'dataset': 'ECG5000', 'avg_composite_score': sil_sel, 'avg_silhouette': sil_sel})
    
    # Fixed
    shapelets_f = extract_shapelets_fast(X_ecg, [15], 100, seed)
    dist_f = compute_distances_fast(X_ecg, shapelets_f)
    for k in [3, 5]:
        km = KMeans(n_clusters=k, n_init=8, random_state=seed)
        labels = km.fit_predict(dist_f)
        sil = silhouette_score(dist_f, labels)
        for size in [15, 30]:
            top_f = np.argsort(np.var(dist_f, axis=0))[-min(size, len(shapelets_f)):]
            d_sel = dist_f[:, top_f]
            km_sel = KMeans(n_clusters=k, n_init=8, random_state=seed)
            labels_sel = km_sel.fit_predict(d_sel)
            sil_sel = silhouette_score(d_sel, labels_sel)
            results_all.append({'seed': seed, 'k': k, 'size': size, 'profile': 'fixed', 
                               'dataset': 'ECG5000', 'avg_composite_score': sil_sel, 'avg_silhouette': sil_sel})

df_all = pd.DataFrame(results_all)
print("\nECG5000 Results:")
summary_ecg = df_all[df_all['dataset']=='ECG5000'].groupby('profile')[['avg_composite_score', 'avg_silhouette']].mean()
print(summary_ecg)

# Save results
df_all.to_csv('shapelet_results.csv', index=False)
print("\nResults saved to shapelet_results.csv")

