#!/usr/bin/env python3
"""
Debug script to inspect distributions in the left tail region.
"""

import sys
import os
import glob
import pandas as pd
import numpy as np
import ot


def get_column_index(df, column_param):
    """Get column index from either a number or column name."""
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
    """Check if weights should be disabled."""
    if isinstance(value, str):
        return value.lower() in ["no", "off", "none", "disabled", "ones"]
    return False


# Load barycenter
barycenter_file = "input/test-cloud-Tumeh2014/barycenter.npz"
data = np.load(barycenter_file)
grid = data['grid']
barycenter = data['barycenter']

# Find left tail (first 5 grid points)
print("=" * 70)
print("LEFT TAIL ANALYSIS (first 5 grid points)")
print("=" * 70)
print(f"\nGrid points: {grid[:5]}")
print(f"Barycenter probs: {barycenter[:5]}")
print(f"Barycenter mass in first 5 points: {barycenter[:5].sum():.6f}")
print()

# Now load all distributions and check their left tails
input_folder = "input/test-cloud-Tumeh2014"
tsv_files = sorted(glob.glob(os.path.join(input_folder, "*.tsv")))

print("Individual distribution mass in left tail:")
print("-" * 70)

total_left_mass = 0
count_with_left_mass = 0

for filepath in tsv_files:
    filename = os.path.basename(filepath)
    df = pd.read_csv(filepath, sep='\t')
    
    # Get pgen values
    pgen_idx = get_column_index(df, 'pgen')
    values = df.iloc[:, pgen_idx].values.astype(float)
    
    # Count samples in left tail (< lowest grid point * 100)
    left_threshold = grid[0] * 100
    left_mask = (values > 0) & (values < left_threshold)
    left_count = left_mask.sum()
    
    if left_count > 0:
        count_with_left_mass += 1
        print(f"{filename}: {left_count:3d} samples < {left_threshold:.3e}")
        total_left_mass += left_count

print()
print(f"Files with samples in left tail: {count_with_left_mass} / {len(tsv_files)}")
print(f"Total samples in left tail across all files: {total_left_mass}")
print()
print("=" * 70)
print("CONCLUSION:")
if total_left_mass == 0:
    print("⚠️  NO samples in left tail, but barycenter has {:.4f} mass there!".format(barycenter[:5].sum()))
    print("   This suggests a numerical issue in the LP solver.")
else:
    print(f"✓ Found {total_left_mass} samples in left tail → barycenter tail is expected")
print("=" * 70)
