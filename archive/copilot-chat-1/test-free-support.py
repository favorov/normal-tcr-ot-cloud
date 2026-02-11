#!/usr/bin/env python3
"""Test free-support barycenter (no fixed discretization grid)"""
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
    
    print("\n" + "="*60)
    print("Testing free-support barycenter...")
    print("="*60)
    
    # Prepare distributions as list of (samples, weights)
    measures_X = []
    measures_a = []
    
    for values in all_distributions:
        X = values.reshape(-1, 1)
        a = np.ones(len(values)) / len(values)
        measures_X.append(X)
        measures_a.append(a)
    
    # Method 1: Use all data points as initial support
    print("\nMethod 1: free_support_barycenter with all data as initial support")
    try:
        X_init = all_values.reshape(-1, 1)
        print(f"  Initial support size: {len(X_init)}")
        print(f"  Number of measures: {len(measures_a)}")
        
        result = ot.lp.free_support_barycenter(
            measures_X, 
            measures_a, 
            X_init=X_init,
        )
        
        print(f"  Result has {len(result)} elements")
        
        bary_X = result[0]
        bary_a = result[1]
        
        print(f"  Barycenter support size: {len(bary_X)}")
        print(f"  Barycenter support (first 10 points):")
        sorted_indices = np.argsort(bary_X.flatten())
        for i in sorted_indices[:10]:
            print(f"    x={bary_X[i, 0]:.6e}, a={bary_a[i]:.6f}")
        
        print(f"  Barycenter statistics:")
        print(f"    Total probability: {bary_a.sum():.10f}")
        print(f"    Max probability: {bary_a.max():.10e}")
        print(f"    Left-tail cumulative (first 10 points): {bary_a[sorted_indices[:10]].sum():.6f}")
        
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Method 2: Use K points sampled uniformly from range
    print("\n" + "-"*60)
    print("Method 2: free_support_barycenter with K=50 sampled points")
    try:
        K = 50
        
        # Sample K points uniformly in log space
        log_min = np.log(all_values.min())
        log_max = np.log(all_values.max())
        log_X_init = np.linspace(log_min, log_max, K)
        X_init = np.exp(log_X_init).reshape(-1, 1)
        
        print(f"  Initial support size: {K}")
        
        result = ot.lp.free_support_barycenter(
            measures_X, 
            measures_a, 
            X_init=X_init,
        )
        
        print(f"  Result has {len(result)} elements")
        
        bary_X = result[0]
        bary_a = result[1]
        
        print(f"  Barycenter support size: {len(bary_X)}")
        print(f"  Barycenter support (sorted by value):")
        sorted_indices = np.argsort(bary_X.flatten())
        print(f"  First 10 points:")
        for i, idx in enumerate(sorted_indices[:10]):
            print(f"    i={i}: x={bary_X[idx, 0]:.6e}, a={bary_a[idx]:.6f}")
        
        print(f"\n  Last 10 points:")
        for i, idx in enumerate(sorted_indices[-10:]):
            print(f"    i={K-10+i}: x={bary_X[idx, 0]:.6e}, a={bary_a[idx]:.6f}")
        
        print(f"\n  Barycenter statistics:")
        print(f"    Total probability: {bary_a.sum():.10f}")
        print(f"    Max probability: {bary_a.max():.10e}")
        print(f"    Left-tail cumulative (first 5 points): {bary_a[sorted_indices[:5]].sum():.6f}")
        print(f"    Left-tail cumulative (first 10 points): {bary_a[sorted_indices[:10]].sum():.6f}")
        
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
