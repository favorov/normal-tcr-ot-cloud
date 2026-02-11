#!/usr/bin/env python3
"""
Debug script to investigate barycenter computation methods.
"""

import sys
import os
import glob
import pandas as pd
import numpy as np
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


def is_no_weights(value):
    if isinstance(value, str):
        return value.lower() in ["no", "off", "none", "disabled", "ones"]
    return False


# Setup
input_folder = "input/test-cloud-Tumeh2014"
tsv_files = sorted(glob.glob(os.path.join(input_folder, "*.tsv")))
freq_column = "pgen"
weights_column = "off"
n_grid = 20  # Small grid for inspection

# Load and discretize
all_values = []
for filepath in tsv_files[:5]:  # First 5 files for quick test
    df = pd.read_csv(filepath, sep='\t')
    freq_idx = get_column_index(df, freq_column)
    values = df.iloc[:, freq_idx].values.astype(float)
    all_values.append(values)

# Create grid
all_concatenated = np.concatenate(all_values)
all_concatenated = all_concatenated[all_concatenated > 0]
min_val = all_concatenated.min()
max_val = all_concatenated.max()
grid = np.logspace(np.log10(min_val), np.log10(max_val), n_grid)

print("=" * 70)
print("BARYCENTER METHOD COMPARISON (n_grid=20, 5 files)")
print("=" * 70)
print(f"Grid: {min_val:.3e} to {max_val:.3e}")
print()

# Discretize all distributions
distributions = []
for values in all_values:
    mask = values > 0
    values_filtered = values[mask]
    
    bin_edges = np.concatenate([[grid[0] / 2], (grid[:-1] + grid[1:]) / 2, [grid[-1] * 2]])
    hist, _ = np.histogram(values_filtered, bins=bin_edges)
    hist = hist / hist.sum()
    distributions.append(hist)

distributions_matrix = np.array(distributions)
cost_matrix = np.abs(grid.reshape(-1, 1) - grid.reshape(1, -1))

print("Input distribution sample:")
print(f"  dist[0][:5] = {distributions_matrix[0, :5]}")
print(f"  dist[0] sum = {distributions_matrix[0].sum():.6f}")
print()

# Method 1: LP barycenter (current)
print("-" * 70)
print("METHOD 1: ot.lp.barycenter()")
print("-" * 70)
try:
    barycenter_lp = ot.lp.barycenter(
        distributions_matrix.T,
        cost_matrix,
        weights=None,
        verbose=False
    )
    print(f"Result: grid[0]={grid[0]:.3e}, prob={barycenter_lp[0]:.6f}")
    print(f"  First 5 probs: {barycenter_lp[:5]}")
    print(f"  Max prob: {barycenter_lp.max():.6f}")
    print(f"  Sum: {barycenter_lp.sum():.6f}")
except Exception as e:
    print(f"ERROR: {e}")

print()

# Method 2: Sinkhorn with high regularization
print("-" * 70)
print("METHOD 2: ot.bregman.barycenter() (Sinkhorn, reg=0.1)")
print("-" * 70)
try:
    barycenter_sinkhorn = ot.bregman.barycenter(
        distributions_matrix.T,
        M=cost_matrix,
        reg=0.1,
        numItermax=10000,
        stopThr=1e-12,
        verbose=False
    )
    print(f"Result: grid[0]={grid[0]:.3e}, prob={barycenter_sinkhorn[0]:.6f}")
    print(f"  First 5 probs: {barycenter_sinkhorn[:5]}")
    print(f"  Max prob: {barycenter_sinkhorn.max():.6f}")
    print(f"  Sum: {barycenter_sinkhorn.sum():.6f}")
except Exception as e:
    print(f"ERROR: {e}")

print()

# Method 3: Simple average
print("-" * 70)
print("METHOD 3: Simple numerical average")
print("-" * 70)
barycenter_avg = distributions_matrix.mean(axis=0)
print(f"Result: grid[0]={grid[0]:.3e}, prob={barycenter_avg[0]:.6f}")
print(f"  First 5 probs: {barycenter_avg[:5]}")
print(f"  Max prob: {barycenter_avg.max():.6f}")
print(f"  Sum: {barycenter_avg.sum():.6f}")

print()
print("=" * 70)
print("ANALYSIS")
print("=" * 70)
print(f"The outlier value {min_val:.3e} is {max_val/min_val:.0e}x smaller than max")
print(f"It appears in only 1/25 files")
print(f"Expected: barycenter should have very little mass at left tail")
print(f"Actual: LP puts {barycenter_lp[0]*100:.1f}% there")
print("=" * 70)
