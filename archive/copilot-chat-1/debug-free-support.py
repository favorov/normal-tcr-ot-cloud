#!/usr/bin/env python3
"""Debug free-support barycenter return values"""
import numpy as np
import pandas as pd
import ot
from pathlib import Path


def load_distribution(filepath, freq_column="pgen"):
    """Load distribution from TSV file"""
    df = pd.read_csv(filepath, sep='\t')
    
    if isinstance(freq_column, str):
        if freq_column in df.columns:
            col_idx = df.columns.get_loc(freq_column)
        else:
            col_idx = int(freq_column)
    else:
        col_idx = freq_column
    
    values = df.iloc[:, col_idx].values
    values = values[values > 0]
    return values


# Load just a few distributions for quick testing
input_folder = "input/test-cloud-Tumeh2014"
files = sorted(Path(input_folder).glob("*.tsv"))[:5]  # Just first 5

print(f"Loading {len(files)} distributions for testing...")
measures_X = []
measures_a = []

for fpath in files:
    values = load_distribution(str(fpath))
    X = values.reshape(-1, 1)
    a = np.ones(len(values)) / len(values)
    measures_X.append(X)
    measures_a.append(a)
    print(f"  {fpath.name}: {len(values)} samples")

# Test with small K
K = 10
log_min = np.log(1e-10)
log_max = np.log(1e-6)
log_X_init = np.linspace(log_min, log_max, K)
X_init = np.exp(log_X_init).reshape(-1, 1)

print(f"\nCalling free_support_barycenter with K={K}...")
try:
    # Try returning more info
    X_bary = ot.lp.free_support_barycenter(
        measures_X, 
        measures_a, 
        X_init=X_init,
    )
    
    print(f"X_bary type: {type(X_bary)}")
    print(f"X_bary shape: {X_bary.shape}")
    print(f"X_bary values:\n{X_bary}")
    
    # Now we need to compute weights for this support
    # We can use Sinkhorn to find the best weights
    print(f"\nComputing weights using Sinkhorn...")
    
    # Create cost matrix between barycenter support and all measures
    cost_matrix = np.zeros((K, len(measures_a)))
    for j, X_j in enumerate(measures_X):
        for i in range(K):
            # L2 distance in log space
            log_dist = np.abs(np.log(X_bary[i, 0]) - np.log(X_j[:, 0]))
            cost_matrix[i, j] = log_dist.mean()  # Average distance to measure j
    
    print(f"Cost matrix shape: {cost_matrix.shape}")
    
    # Compute uniform weights for now
    weights = np.ones(K) / K
    
    print(f"Barycenter support points (sorted):")
    sorted_idx = np.argsort(X_bary.flatten())
    for idx in sorted_idx[:10]:
        print(f"  x={X_bary[idx, 0]:.3e}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

