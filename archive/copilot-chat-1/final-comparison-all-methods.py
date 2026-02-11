#!/usr/bin/env python3
"""
Compare all three barycenter methods:
1. LP barycenter (fixed grid with min-max)
2. Free-support barycenter (adaptive support)
3. Simple average
"""
import sys
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

print(f"Loading {len(files)} distributions...")
all_distributions = []
all_values = []

for fpath in files:
    values = load_distribution(str(fpath))
    all_distributions.append(values)
    all_values.extend(values)
    print(f"  {fpath.name}: {len(values)} samples")

all_values = np.array(all_values)
print(f"\nTotal: {len(all_values)} samples")
print(f"Range: [{all_values.min():.3e}, {all_values.max():.3e}]")

# Prepare distributions
measures_X = []
measures_a = []

for values in all_distributions:
    X = values.reshape(-1, 1)
    a = np.ones(len(values)) / len(values)
    measures_X.append(X)
    measures_a.append(a)

# METHOD 1: LP GRID-BASED BARYCENTER
print("\n" + "="*60)
print("METHOD 1: LP GRID-BASED BARYCENTER (min-max)")
print("="*60)

n_grid = 200
grid = np.logspace(np.log10(all_values.min()), np.log10(all_values.max()), n_grid)

distributions_matrix = []
for values in all_distributions:
    bin_edges = np.concatenate([[grid[0] / 2], (grid[:-1] + grid[1:]) / 2, [grid[-1] * 2]])
    hist, _ = np.histogram(values, bins=bin_edges)
    hist = hist / hist.sum()
    distributions_matrix.append(hist)

distributions_matrix = np.array(distributions_matrix).T

cost_matrix = np.abs(np.log(grid.reshape(-1, 1)) - np.log(grid.reshape(1, -1)))

print(f"Grid: {n_grid} points, range [{grid[0]:.3e}, {grid[-1]:.3e}]")
bary_lp = ot.lp.barycenter(distributions_matrix, cost_matrix, verbose=False)

print(f"First 10 grid points mass: {bary_lp[:10].sum():.4f}")
print(f"Last 10 grid points mass: {bary_lp[-10:].sum():.4f}")
print(f"grid[0] = {grid[0]:.3e}, prob = {bary_lp[0]:.6f}")
print(f"Max probability: {bary_lp.max():.6f}")

# METHOD 2: FREE-SUPPORT BARYCENTER
print("\n" + "="*60)
print("METHOD 2: FREE-SUPPORT BARYCENTER")
print("="*60)

K = 100
log_min = np.log(all_values.min())
log_max = np.log(all_values.max())
X_init = np.exp(np.linspace(log_min, log_max, K)).reshape(-1, 1)

print(f"Initial support: {K} log-spaced points")
print(f"Range: [{X_init.min():.3e}, {X_init.max():.3e}]")

print("Computing free-support barycenter (this may take a minute)...")
try:
    X_bary = ot.lp.free_support_barycenter(
        measures_X, 
        measures_a, 
        X_init=X_init,
        verbose=False
    )
    
    print(f"Result: {len(X_bary)} support points")
    
    # Use uniform weights
    a_bary_free = np.ones(len(X_bary)) / len(X_bary)
    
    # Sort by value
    sorted_idx = np.argsort(X_bary.flatten())
    
    print(f"First 10 support points (sorted):")
    for i in range(min(10, len(X_bary))):
        idx = sorted_idx[i]
        print(f"  {i}: x={X_bary[idx, 0]:.3e}, a={a_bary_free[idx]:.4f}")
    
    print(f"\nFirst 10 points cumulative mass: {a_bary_free[sorted_idx[:10]].sum():.4f}")
    print(f"Max probability: {a_bary_free.max():.4f}")
    
except Exception as e:
    print(f"Error: {e}")
    X_bary = None

# METHOD 3: SIMPLE AVERAGE
print("\n" + "="*60)
print("METHOD 3: SIMPLE AVERAGE")
print("="*60)

# Discretize on the same grid as LP
distributions_simple = []
for values in all_distributions:
    bin_edges = np.concatenate([[grid[0] / 2], (grid[:-1] + grid[1:]) / 2, [grid[-1] * 2]])
    hist, _ = np.histogram(values, bins=bin_edges)
    hist = hist / hist.sum()
    distributions_simple.append(hist)

bary_avg = np.mean(distributions_simple, axis=0)

print(f"First 10 grid points mass: {bary_avg[:10].sum():.4f}")
print(f"Last 10 grid points mass: {bary_avg[-10:].sum():.4f}")
print(f"grid[0] = {grid[0]:.3e}, prob = {bary_avg[0]:.6f}")
print(f"Max probability: {bary_avg.max():.6f}")

# SUMMARY
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

print(f"\n{'Method':<30} {'First 10':<12} {'Max prob':<12} {'Notes'}")
print("-" * 80)
print(f"{'LP grid-based':<30} {bary_lp[:10].sum():<12.4f} {bary_lp.max():<12.6f} Fixed grid, {n_grid} points")

if X_bary is not None:
    print(f"{'Free-support':<30} {a_bary_free[sorted_idx[:10]].sum():<12.4f} {a_bary_free.max():<12.4f} Adaptive, {len(X_bary)} points")

print(f"{'Simple average':<30} {bary_avg[:10].sum():<12.4f} {bary_avg.max():<12.6f} Arithmetic mean")

print("\n" + "="*60)
print("INTERPRETATION")
print("="*60)
print("""
- LP grid-based: Allocates ~20% to first 10 bins (artifact from extreme outlier)
- Free-support: Should adapt to avoid left-tail artifact (true OT)
- Simple average: Only ~0.5% in first 10 (represents true sample proportion)

The free-support method trades off between:
  1. Being a true Wasserstein barycenter (optimal transport)
  2. Avoiding left-tail artifacts from extreme outliers

If free-support majority is in first 10 points: LP solver forces mass there
If free-support is balanced: Algorithm successfully avoided outlier trap
""")
