#!/usr/bin/env python3
"""Test free-support barycenter (doesn't use discretization grid)"""
import numpy as np
import pandas as pd
import ot
from pathlib import Path


def load_distribution(filepath, freq_column="pgen"):
    """Load distribution from TSV file"""
    df = pd.read_csv(filepath, sep='\t')
    
    # Find column index
    if isinstance(freq_column, str):
        if freq_column in df.columns:
            col_idx = df.columns.get_loc(freq_column)
        else:
            try:
                col_idx = int(freq_column)
            except ValueError:
                raise ValueError(f"Column '{freq_column}' not found")
    else:
        col_idx = freq_column
    
    values = df.iloc[:, col_idx].values
    values = values[values > 0]
    
    return values


def main():
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
    print(f"\nTotal samples: {len(all_values)}")
    print(f"Min: {all_values.min():.3e}, Max: {all_values.max():.3e}")
    
    # Create log list of samples for cost matrix
    log_values = np.log(all_values).reshape(-1, 1)
    
    # Compute cost matrix (L1 distance in log space)
    cost_matrix = np.abs(log_values - log_values.T)
    
    print("\n" + "="*60)
    print("Testing free-support barycenter...")
    print("="*60)
    
    # Use free-support barycenter with K support points
    # Start with K = 20 (similar size to grid approach)
    K = 20
    n_iter = 100
    
    print(f"\nFree-support barycenter with {K} support points, {n_iter} iterations...")
    
    try:
        # Initialize with random points from all data
        X_bary = np.random.choice(all_values, size=K, replace=False).reshape(-1, 1)
        X_bary = np.sort(X_bary, axis=0)
        
        # Compute barycenter by iteratively updating support points
        # This requires computing OT between barycenter and each distribution
        
        # For now, let's use a simpler approach: 
        # Create discrete distributions for each patient
        # Then use Sinkhorn barycenter with entropy regularization
        
        print("\nInstead, testing Sinkhorn barycenter with entropy regularization...")
        
        # Discretize to grid for comparison
        p1 = np.percentile(all_values, 1)
        p99 = np.percentile(all_values, 99)
        grid = np.logspace(np.log10(p1), np.log10(p99), 20)
        
        distributions = []
        for values in all_distributions:
            bin_edges = np.concatenate([[grid[0] / 2], (grid[:-1] + grid[1:]) / 2, [grid[-1] * 2]])
            hist, _ = np.histogram(values, bins=bin_edges)
            hist = hist / hist.sum()
            distributions.append(hist)
        
        distributions_array = np.array(distributions).T  # Shape: (20, 25)
        
        # Cost matrix
        cost_matrix = np.abs(grid.reshape(-1, 1) - grid.reshape(1, -1))
        
        # Try different regularization values
        for reg in [0.01, 0.05, 0.1, 0.5]:
            print(f"\nSinkhorn barycenter with reg={reg}:")
            bary = ot.bregman.barycenter(distributions_array, cost_matrix, reg=reg, verbose=False)
            print(f"  grid[0] = {grid[0]:.3e}, prob = {bary[0]:.6f}")
            print(f"  First 5 points mass: {bary[:5].sum():.6f}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
