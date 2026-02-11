#!/usr/bin/env python3
"""Verify free-support barycenter is actually computing Wasserstein distances"""
import numpy as np
import pandas as pd
import ot
from pathlib import Path


def load_distribution(filepath, freq_column="pgen"):
    df = pd.read_csv(filepath, sep='\t')
    if isinstance(freq_column, str):
        col_idx = df.columns.get_loc(freq_column) if freq_column in df.columns else int(freq_column)
    else:
        col_idx = freq_column
    
    values = df.iloc[:, col_idx].values
    return values[values > 0]


input_folder = "input/test-cloud-Tumeh2014"
files = sorted(Path(input_folder).glob("*.tsv"))

print("Loading distributions...")
measures_X = []
measures_a = []

for fpath in files[:5]:  # Just first 5 for speed
    values = load_distribution(str(fpath))
    X = values.reshape(-1, 1)
    a = np.ones(len(values)) / len(values)
    measures_X.append(X)
    measures_a.append(a)
    print(f"  {fpath.name}: {len(values)} samples")

# Free-support barycenter
K = 20
all_values = np.concatenate([v.flatten() for v in measures_X])
log_min = np.log(all_values.min())
log_max = np.log(all_values.max())
X_init = np.exp(np.linspace(log_min, log_max, K)).reshape(-1, 1)

print(f"\nComputing free-support barycenter with K={K}...")
X_bary = ot.lp.free_support_barycenter(measures_X, measures_a, X_init=X_init)

print(f"Barycenter support points (first 10):")
for i in range(min(10, len(X_bary))):
    print(f"  {i}: {X_bary[i, 0]:.6e}")

# Use uniform weights for the barycenter
a_bary = np.ones(len(X_bary)) / len(X_bary)

print(f"\n" + "="*60)
print("Computing Wasserstein distances...")
print("="*60)

# Cost matrix for Wasserstein
M_all = np.abs(np.log(all_values.reshape(-1, 1)) - np.log(all_values.reshape(1, -1)))

total_distance = 0
for i, (X_i, a_i) in enumerate(zip(measures_X, measures_a)):
    # Cost between barycenter and measure i
    M = np.abs(np.log(X_bary) - np.log(X_i.T))
    # Wasserstein distance (using LP solver)
    W_dist = ot.emd2(a_bary, a_i, M)
    print(f"W(barycenter, measure {i}): {W_dist:.6e}")
    total_distance += W_dist

print(f"\nTotal Wasserstein distance: {total_distance:.6e}")

# Now compare with a random "bad" barycenter (uniform distribution)
print(f"\n" + "-"*60)
print("Comparison: random uniform barycenter")
print("-"*60)

X_random = np.exp(np.linspace(log_min, log_max, K)).reshape(-1, 1)
a_random = np.ones(K) / K

total_random = 0
for i, (X_i, a_i) in enumerate(zip(measures_X, measures_a)):
    M = np.abs(np.log(X_random) - np.log(X_i.T))
    W_dist = ot.emd2(a_random, a_i, M)
    print(f"W(random, measure {i}): {W_dist:.6e}")
    total_random += W_dist

print(f"\nTotal Wasserstein distance (random): {total_random:.6e}")
print(f"\nImprovement: {(total_random - total_distance) / total_random * 100:.1f}%")

