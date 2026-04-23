import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

print("Starting comprehensive shapelet comparison...")

# ============================================================================
# Helper Functions
# ============================================================================

def extract_shapelets(X, lengths, num_candidates, seed=42):
    '''Extract random shapelets of specified lengths'''
    np.random.seed(seed)
    n_samples, n_steps = X.shape
    shapelets = []
    
    for length in lengths:
        for _ in range(num_candidates // len(lengths)):
            sample_idx = np.random.randint(0, n_samples)
            start_idx = np.random.randint(0, n_steps - length + 1)
            shapelet = X[sample_idx, start_idx:start_idx + length].copy()
            shapelet = (shapelet - np.mean(shapelet)) / (np.std(shapelet) + 1e-8)
            shapelets.append(shapelet)
    
    return shapelets

def compute_shapelet_distances(X, shapelets):
    '''Compute minimum distance between each time series and all shapelets'''
    n_samples = X.shape[0]
    distances = np.zeros((n_samples, len(shapelets)))
    
    for i in range(n_samples):
        ts = X[i]
        ts_normalized = (ts - np.mean(ts)) / (np.std(ts) + 1e-8)
        
        for j, shapelet in enumerate(shapelets):
            correlations = []
            for k in range(len(ts_normalized) - len(shapelet) + 1):
                segment = ts_normalized[k:k + len(shapelet)]
                corr = np.dot(segment, shapelet) / (len(shapelet) * (np.std(segment) + 1e-8) * (np.std(shapelet) + 1e-8) + 1e-10)
                correlations.append(abs(corr))
            
            max_corr = max(correlations) if correlations else 0
            distances[i, j] = 1 - max_corr
    
    return distances

def compute_composite_score(distances, labels, silhouette_val):
    '''Compute composite score'''
    # Normalize distances
    if np.max(distances) > np.min(distances):
        distances_norm = (distances - np.min(distances)) / (np.max(distances) - np.min(distances))
    else:
        distances_norm = distances
    
    unique_labels = np.unique(labels)
    intra_dists = []
    for label in unique_labels:
        mask = labels == label
        if np.sum(mask) > 1:
            intra_dists.append(np.mean(distances_norm[mask][:, np.where(mask)[0]]))
    
    avg_intra = np.mean(intra_dists) if intra_dists else 0
    composite = (1 - avg_intra) * 0.5 + silhouette_val * 0.5
    return composite

# ============================================================================
# 1. ECG5000 DATASET
# ============================================================================
print("\n=== ECG5000 ===")

ecg5000_train = pd.read_csv(r"D:\repositories\personal\xai-spatio-temporal\data\UCRArchive_2018\ECG5000\ECG5000_TRAIN.tsv", sep='\t', header=None)
ecg5000_test = pd.read_csv(r"D:\repositories\personal\xai-spatio-temporal\data\UCRArchive_2018\ECG5000\ECG5000_TEST.tsv", sep='\t', header=None)

X_ecg5000 = pd.concat([ecg5000_train, ecg5000_test], ignore_index=True).iloc[:, 1:].values
X_ecg5000 = StandardScaler().fit_transform(X_ecg5000)

print(f"Shape: {X_ecg5000.shape}")

results_ecg5000 = []

for seed in [0, 1, 2]:
    # Mixed-length
    shapelets_m = extract_shapelets(X_ecg5000, (5, 10, 15, 20, 25), 120, seed)
    dist_m = compute_shapelet_distances(X_ecg5000, shapelets_m)
    
    for k in [2, 3, 4, 5, 6]:
        km_m = KMeans(n_clusters=k, n_init=12, random_state=seed)
        labels_m = km_m.fit_predict(dist_m)
        sil_m = silhouette_score(dist_m, labels_m)
        
        for size in [10, 25, 50]:
            top_feats = np.argsort(np.var(dist_m, axis=0))[-min(size, len(shapelets_m)):]
            dist_m_sel = dist_m[:, top_feats]
            
            km_m_sel = KMeans(n_clusters=k, n_init=12, random_state=seed)
            labels_m_sel = km_m_sel.fit_predict(dist_m_sel)
            sil_m_sel = silhouette_score(dist_m_sel, labels_m_sel)
            comp_m = compute_composite_score(dist_m_sel, labels_m_sel, sil_m_sel)
            
            results_ecg5000.append({'seed': seed, 'k': k, 'size': size, 'profile': 'mixed', 
                                   'selected_dictionary_size': len(top_feats), 
                                   'avg_composite_score': comp_m, 'avg_silhouette': sil_m_sel})
    
    # Fixed-length
    shapelets_f = extract_shapelets(X_ecg5000, [15], 120, seed)
    dist_f = compute_shapelet_distances(X_ecg5000, shapelets_f)
    
    for k in [2, 3, 4, 5, 6]:
        km_f = KMeans(n_clusters=k, n_init=12, random_state=seed)
        labels_f = km_f.fit_predict(dist_f)
        sil_f = silhouette_score(dist_f, labels_f)
        
        for size in [10, 25, 50]:
            top_feats = np.argsort(np.var(dist_f, axis=0))[-min(size, len(shapelets_f)):]
            dist_f_sel = dist_f[:, top_feats]
            
            km_f_sel = KMeans(n_clusters=k, n_init=12, random_state=seed)
            labels_f_sel = km_f_sel.fit_predict(dist_f_sel)
            sil_f_sel = silhouette_score(dist_f_sel, labels_f_sel)
            comp_f = compute_composite_score(dist_f_sel, labels_f_sel, sil_f_sel)
            
            results_ecg5000.append({'seed': seed, 'k': k, 'size': size, 'profile': 'fixed', 
                                   'selected_dictionary_size': len(top_feats), 
                                   'avg_composite_score': comp_f, 'avg_silhouette': sil_f_sel})

df_ecg5000 = pd.DataFrame(results_ecg5000)
summary_ecg5000 = df_ecg5000.groupby('profile')[['selected_dictionary_size', 'avg_composite_score', 'avg_silhouette']].mean().round(4)

print("\nECG5000 Summary:")
print(summary_ecg5000)

# Save to CSV
df_ecg5000.to_csv('ecg5000_results.csv', index=False)
summary_ecg5000.to_csv('ecg5000_summary.csv')

