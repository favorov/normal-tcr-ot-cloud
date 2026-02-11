#!/usr/bin/env python3
"""
Detailed analysis of the distribution matrix structure and barycenter issue.
"""

import numpy as np
import pandas as pd
import glob
import os
import ot


def get_column_index(df, column_param):
    try:
        col_idx = int(column_param)
        if 0 <= col_idx < len(df.columns):
            return col_idx
    except (ValueError, TypeError):
        pass
    
    if column_param in df.columns:
        return df.columns.get_loc(column_param)
    raise ValueError(f"Column '{column_param}' not found")


# Load all data
input_folder = "input/test-cloud-Tumeh2014"
tsv_files = sorted(glob.glob(os.path.join(input_folder, "*.tsv")))

all_values = []
for filepath in tsv_files:
    df = pd.read_csv(filepath, sep='\t')
    freq_idx = get_column_index(df, 'pgen')
    values = df.iloc[:, freq_idx].values.astype(float)
    all_values.append(values[values > 0])

# Create grid (full 25 files)
all_concatenated = np.concatenate(all_values)
min_val = all_concatenated.min()
max_val = all_concatenated.max()
n_grid = 20
grid = np.logspace(np.log10(min_val), np.log10(max_val), n_grid)

# Discretize
distributions = []
for values in all_values:
    bin_edges = np.concatenate([[grid[0] / 2], (grid[:-1] + grid[1:]) / 2, [grid[-1] * 2]])
    hist, _ = np.histogram(values, bins=bin_edges)
    hist = hist / (hist.sum() if hist.sum() > 0 else 1)
    distributions.append(hist)

distributions_matrix = np.array(distributions)

print("=" * 70)
print("DISTRIBUTION MATRIX ANALYSIS")
print("=" * 70)
print(f"Shape: {distributions_matrix.shape}")
print(f"Total zeros: {(distributions_matrix == 0).sum()} / {distributions_matrix.size}")
print(f"Sparsity: {(distributions_matrix == 0).sum() / distributions_matrix.size * 100:.1f}%")
print()

# Look at left tail columns
print("-" * 70)
print("LEFT TAIL COLUMNS (first 3 grid points)")
print("-" * 70)
for i in range(3):
    col = distributions_matrix[:, i]
    nonzero_count = (col > 0).sum()
    print(f"Grid[{i}]={grid[i]:.3e}")
    print(f"  Non-zero: {nonzero_count}/25 distributions")
    print(f"  Mean: {col.mean():.6f}, Max: {col.max():.6f}, Sum: {col.sum():.6f}")
    if nonzero_count > 0:
        print(f"  Files with mass: {[j for j, val in enumerate(col) if val > 0]}")
print()

# Compare methods with details
print("-" * 70)
print("LP BARYCENTER vs SIMPLE AVERAGE")
print("-" * 70)

cost_matrix = np.abs(grid.reshape(-1, 1) - grid.reshape(1, -1))

# LP
barycenter_lp = ot.lp.barycenter(
    distributions_matrix.T,
    cost_matrix,
    weights=None,
    verbose=False
)

# Average
barycenter_avg = distributions_matrix.mean(axis=0)

print("\nFirst 3 grid points comparison:")
for i in range(3):
    print(f"Grid[{i}]={grid[i]:.3e}")
    print(f"  LP:      {barycenter_lp[i]:.6f}")
    print(f"  Average: {barycenter_avg[i]:.6f}")
    if barycenter_avg[i] > 0:
        ratio = barycenter_lp[i] / barycenter_avg[i]
        print(f"  Ratio (LP/Avg): {ratio:.1f}x")
    else:
        ratio = float('inf') if barycenter_lp[i] > 0 else 1.0
        print(f"  Ratio (LP/Avg): {'inf' if barycenter_lp[i] > 0 else '1'}x")
print()

# Check which file has the leftmost point
leftmost_file_idx = None
for j, vals in enumerate(all_values):
    if vals.min() == min_val:
        leftmost_file_idx = j
        break

print(f"File with extreme outlier: Patient{leftmost_file_idx:02d}")
print(f"In discretized dist[{leftmost_file_idx}], grid point 0 has: {distributions_matrix[leftmost_file_idx, 0]:.6f}")
print()

print("=" * 70)
print("HYPOTHESIS")
print("=" * 70)
print("The LP solver sees that file Patient{:02d} has ALL its mass in grid[0],".format(leftmost_file_idx+1))
print("while others have zero there. To minimize transport cost to that file,")
print("LP must put a lot of mass in grid[0] in the barycenter.")
print()
print("Solution: Use a discretization that groups extreme outliers together")
print("rather than creating a dedicated left-tail bin.")
print("=" * 70)
