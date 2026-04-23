import os
import sys
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

print("All modules imported successfully!")

# Check if data directories exist
ecg5000_path = r"D:\repositories\personal\xai-spatio-temporal\data\UCRArchive_2018\ECG5000"
roma_taxi_path = r"D:\repositories\personal\xai-spatio-temporal\data\roma-taxi\extracted\taxi_february.txt"

print(f"ECG5000 path exists: {os.path.exists(ecg5000_path)}")
print(f"Roma-taxi path exists: {os.path.exists(roma_taxi_path)}")

# List ECG5000 directory
if os.path.exists(ecg5000_path):
    print(f"ECG5000 directory contents: {os.listdir(ecg5000_path)}")
