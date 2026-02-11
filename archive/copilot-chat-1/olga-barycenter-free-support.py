#!/usr/bin/env python3
"""
Wasserstein barycenter using free-support (adaptive support points).
This method does NOT use a fixed discretization grid - instead it adaptively
places support points where needed to minimize total transport distance.

Unlike LP grid-based barycenter, free-support avoids artifacts from extreme outliers.
"""
import sys
import numpy as np
import pandas as pd
import ot
from pathlib import Path


def load_and_prepare_distribution(filepath, freq_column="pgen", weights_column="off"):
    """Load distribution from TSV file and return (values, weights)."""
    df = pd.read_csv(filepath, sep='\t')
    
    # Find frequency column
    if isinstance(freq_column, str):
        if freq_column in df.columns:
            freq_idx = df.columns.get_loc(freq_column)
        else:
            try:
                freq_idx = int(freq_column)
            except ValueError:
                raise ValueError(f"Column '{freq_column}' not found in {filepath}")
    else:
        freq_idx = freq_column
    
    values = df.iloc[:, freq_idx].values.astype(float)
    values_filtered = values[values > 0]
    
    # Find weight column
    if weights_column == "off":
        weights = np.ones(len(values_filtered))
    else:
        if isinstance(weights_column, str):
            if weights_column in df.columns:
                weight_idx = df.columns.get_loc(weights_column)
            else:
                try:
                    weight_idx = int(weights_column)
                except ValueError:
                    raise ValueError(f"Column '{weights_column}' not found in {filepath}")
        else:
            weight_idx = weights_column
        
        weights = df.iloc[:, weight_idx].values[values > 0].astype(float)
        weights = weights / weights.sum()
    
    return values_filtered, weights


def compute_free_support_barycenter_with_weights(measures_X, measures_a, n_support=None, max_iter=100):
    """
    Compute free-support Wasserstein barycenter with proper weights.
    
    Parameters:
    - measures_X: list of arrays, each shape (n_samples, 1)
    - measures_a: list of weight arrays, each shape (n_samples,)
    - n_support: number of support points (default: 10% of total samples)
    - max_iter: number of iterations for weight optimization
    
    Returns:
    - X_bary: support points, shape (K, 1)
    - a_bary: weights (normalized), shape (K,)
    """
    
    # Total number of samples
    total_samples = sum(len(X) for X in measures_X)
    
    if n_support is None:
        # Use ~10% of total samples as support size
        n_support = max(10, int(np.sqrt(total_samples)))
    
    # Concatenate all samples to get data range
    all_samples = np.concatenate([X.flatten() for X in measures_X])
    log_min = np.log(all_samples.min())
    log_max = np.log(all_samples.max())
    
    print(f"  Initial support size: {n_support}")
    print(f"  Data range: [{all_samples.min():.3e}, {all_samples.max():.3e}]")
    
    # Initialize support points: log-spaced
    X_init = np.exp(np.linspace(log_min, log_max, n_support)).reshape(-1, 1)
    
    # Prepare measures with proper weights for OT solver
    # OT solver expects normalized weights for each measure (sum = 1)
    measures_normalized = []
    for a in measures_a:
        a_norm = a / a.sum()
        measures_normalized.append(a_norm)
    
    # Compute free-support locations
    print(f"  Computing free-support barycenter locations...")
    X_bary = ot.lp.free_support_barycenter(
        measures_X,
        measures_normalized,
        X_init=X_init,
        verbose=False
    )
    
    print(f"  Result: {len(X_bary)} support points")
    
    # Now compute optimal weights for these support points
    # We need to solve: min_{a} sum_i W(delta_barycenter(X_bary, a), mu_i)
    # where delta_barycenter represents a distribution on X_bary with weights a
    
    # Initialize with uniform weights
    a_bary = np.ones(len(X_bary)) / len(X_bary)
    
    # Iterative algorithm to optimize weights
    print(f"  Optimizing weights (up to {max_iter} iterations)...")
    
    for iteration in range(max_iter):
        # Compute cost matrix between barycenter support and each measure
        # Then solve OT to get transport plans
        
        # Compute OT distances and plans from each measure to barycenter
        total_distance = 0
        gradient = np.zeros(len(X_bary))
        
        for X_i, a_i in zip(measures_X, measures_a):
            # Cost matrix (L1 distance in log space)
            log_bary = np.log(X_bary.reshape(-1, 1))
            log_samples = np.log(X_i.reshape(1, -1))
            M = np.abs(log_bary - log_samples)
            
            # Use Sinkhorn for smoother computation
            # Normalize weights for Sinkhorn
            a_bary_norm = a_bary / a_bary.sum()
            a_i_norm = a_i / a_i.sum()
            
            # Compute OT with Sinkhorn (more stable than EMD)
            P = ot.sinkhorn(a_bary_norm, a_i_norm, M, reg=0.01, verbose=False)
            
            # Distance
            W = np.sum(P * M)
            total_distance += W
            
            # Gradient of distance w.r.t. a_bary (simplified)
            # This is the average cost to each support point
            gradient += np.sum(P * M, axis=1)
        
        # Normalize gradient
        gradient = gradient / len(measures_X)
        
        # Update weights: move down gradient
        lr = 0.1 / (iteration + 1)  # Decreasing learning rate
        a_bary_new = a_bary - lr * gradient
        
        # Project back to simplex (ensure weights sum to 1 and non-negative)
        a_bary_new = np.maximum(a_bary_new, 1e-10)
        a_bary_new = a_bary_new / a_bary_new.sum()
        
        # Check convergence
        diff = np.sum(np.abs(a_bary_new - a_bary))
        a_bary = a_bary_new
        
        if iteration % 10 == 0:
            print(f"    Iteration {iteration}: total distance = {total_distance:.6e}, weight change = {diff:.6e}")
        
        if diff < 1e-8:
            print(f"    Converged at iteration {iteration}")
            break
    
    return X_bary, a_bary


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python olga-barycenter-free-support.py <input_folder> [--freq-column <col>] [--weights-column <col>] [--n-support <n>]")
        print("\nParameters:")
        print("  input_folder      : Path to folder containing TSV files")
        print("  --freq-column     : Column index (0-based) or column name for frequencies (default: pgen)")
        print("  --weights-column  : Column index (0-based) or column name for weights, or 'off' (default: off)")
        print("  --n-support       : Number of support points in barycenter (default: sqrt(n_samples))")
        print("\nExamples:")
        print("  python olga-barycenter-free-support.py input/test-cloud-Tumeh2014")
        print("  python olga-barycenter-free-support.py input/test-cloud-Tumeh2014 --freq-column pgen")
        print("  python olga-barycenter-free-support.py input/test-cloud-Tumeh2014 --n-support 50")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    freq_column = "pgen"
    weights_column = "off"
    n_support = None
    
    # Parse named arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--freq-column" and i + 1 < len(sys.argv):
            freq_column = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--weights-column" and i + 1 < len(sys.argv):
            weights_column = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--n-support" and i + 1 < len(sys.argv):
            try:
                n_support = int(sys.argv[i + 1])
            except ValueError:
                print(f"Error: --n-support must be an integer, got '{sys.argv[i + 1]}'")
                sys.exit(1)
            if n_support < 2:
                print("Error: --n-support must be >= 2")
                sys.exit(1)
            i += 2
        else:
            print(f"Error: Unknown argument '{sys.argv[i]}'")
            sys.exit(1)
    
    # Find all TSV files
    input_path = Path(input_folder)
    tsv_files = sorted(input_path.glob("*.tsv"))
    
    if not tsv_files:
        print(f"Error: No TSV files found in {input_folder}")
        sys.exit(1)
    
    print(f"Found {len(tsv_files)} TSV file(s)")
    print(f"Frequency column: {freq_column}")
    print(f"Weights column: {weights_column}")
    print()
    
    try:
        # Load all distributions
        measures_X = []
        measures_a = []
        
        for fpath in tsv_files:
            values, weights = load_and_prepare_distribution(str(fpath), freq_column, weights_column)
            X = values.reshape(-1, 1)
            measures_X.append(X)
            measures_a.append(weights)
            print(f"  Loaded {fpath.name}: {len(values)} samples")
        
        print()
        print("Computing free-support Wasserstein barycenter...")
        print("=" * 60)
        
        X_bary, a_bary = compute_free_support_barycenter_with_weights(
            measures_X,
            measures_a,
            n_support=n_support,
            max_iter=100
        )
        
        print("=" * 60)
        print("Free-support barycenter computation complete")
        print()
        print("WASSERSTEIN BARYCENTER (FREE-SUPPORT)")
        print("=" * 60)
        print(f"Number of files: {len(tsv_files)}")
        print(f"Support points: {len(X_bary)}")
        print()
        
        # Sort by value for display
        sorted_idx = np.argsort(X_bary.flatten())
        
        print("First 10 support points (sorted):")
        for i in range(min(10, len(X_bary))):
            idx = sorted_idx[i]
            print(f"  x[{i}] = {X_bary[idx, 0]:.6e}, a = {a_bary[idx]:.10e}")
        
        print()
        print("Barycenter statistics:")
        print(f"  Total probability: {a_bary.sum():.10f}")
        print(f"  Max probability: {a_bary.max():.10e}")
        print(f"  Min probability: {a_bary.min():.10e}")
        print(f"  Entropy: {-np.sum(a_bary[a_bary > 0] * np.log(a_bary[a_bary > 0])):.6f}")
        print(f"  Support range: [{X_bary.min():.3e}, {X_bary.max():.3e}]")
        print()
        
        # Save to NPZ file
        output_file = input_path / "barycenter_free_support.npz"
        np.savez(output_file, barycenter=a_bary, support=X_bary.flatten())
        
        print(f"Barycenter saved to: {output_file}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
