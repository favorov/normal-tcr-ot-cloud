#!/usr/bin/env python3
"""
Calculate Wasserstein barycenter of distributions from all TSV files in a folder.
"""

import sys
import os
import glob
import pandas as pd
import numpy as np
import ot


def is_no_weights(value):
    """Check if the weights column should be disabled."""
    if isinstance(value, str):
        return value.lower() in ["no", "off", "none", "disabled", "ones"]
    return False


def get_column_index(df, column_param):
    """
    Get column index from either a number or column name.
    
    Parameters:
    -----------
    df : DataFrame
        The pandas DataFrame
    column_param : str or int
        Either a column index (string representation of number) or column name
    
    Returns:
    --------
    int: Column index
    """
    # Try to interpret as a number first
    try:
        col_idx = int(column_param)
        if 0 <= col_idx < len(df.columns):
            return col_idx
    except (ValueError, TypeError):
        pass
    
    # Try to find by column name
    if column_param in df.columns:
        return df.columns.get_loc(column_param)
    
    # If not found, raise an error
    raise ValueError(f"Column '{column_param}' not found. Available columns: {list(df.columns)}")


def load_distribution(filepath, freq_column, weights_column):
    """
    Load TSV file and extract sample values and their weights.
    
    Parameters:
    -----------
    filepath : str
        Path to the TSV file
    freq_column : str or int
        Column index or name for sample values
    weights_column : str or int
        Column index or name for weights, or "NO"/"off" to disable weights
    
    Returns:
    --------
    tuple: (sample_values, weights)
    """
    df = pd.read_csv(filepath, sep='\t')
    
    # Get sample values
    freq_idx = get_column_index(df, freq_column)
    sample_values = df.iloc[:, freq_idx].values.astype(float)
    
    # Check if we should use weights
    use_weights = not is_no_weights(weights_column)
    
    if use_weights:
        try:
            weights_idx = get_column_index(df, weights_column)
            weights = df.iloc[:, weights_idx].values.astype(float)
        except (ValueError, IndexError) as e:
            print(f"Warning ({os.path.basename(filepath)}): {e}. Using uniform weights.")
            weights = np.ones(len(sample_values))
    else:
        weights = np.ones(len(sample_values))
    
    # Normalize weights
    weights = weights / weights.sum()
    
    return sample_values, weights


def main():
    """Main function."""
    if len(sys.argv) < 4:
        print("Usage: python olga-barycenter-ot.py <input_folder> <freq_column> <weights_column> [n_grid]")
        print("\nParameters:")
        print("  input_folder    : Path to folder containing TSV files")
        print("  freq_column     : Column index (0-based) or column name for sample values")
        print("  weights_column  : Column index (0-based) or column name for weights,")
        print("                    or 'NO'/'off' to disable weights")
        print("  n_grid          : Number of grid points (default: 200)")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    freq_column = sys.argv[2]
    weights_column = sys.argv[3]
    n_grid = 200
    if len(sys.argv) >= 5:
        try:
            n_grid = int(sys.argv[4])
        except ValueError:
            print(f"Error: n_grid must be an integer, got '{sys.argv[4]}'")
            sys.exit(1)
        if n_grid <= 1:
            print("Error: n_grid must be > 1")
            sys.exit(1)
    
    # Find all TSV files
    tsv_files = sorted(glob.glob(os.path.join(input_folder, "*.tsv")))
    
    if not tsv_files:
        print(f"Error: No TSV files found in {input_folder}")
        sys.exit(1)
    
    print(f"Found {len(tsv_files)} TSV file(s)")
    print(f"Frequency column: {freq_column}")
    print(f"Weights column: {weights_column}")
    print()
    
    try:
        # Load all distributions
        all_values = []
        all_weights = []
        
        for filepath in tsv_files:
            filename = os.path.basename(filepath)
            values, weights = load_distribution(filepath, freq_column, weights_column)
            all_values.append(values)
            all_weights.append(weights)
            print(f"  Loaded {filename}: {len(values)} samples")
        
        # Create common support grid (log scale for pgen values)
        # Find min and max across all distributions
        all_concatenated = np.concatenate(all_values)
        # Filter out zero values
        all_concatenated = all_concatenated[all_concatenated > 0]
        
        if len(all_concatenated) == 0:
            print("Error: No valid (non-zero) values found in data")
            sys.exit(1)
        
        min_val = all_concatenated.min()
        max_val = all_concatenated.max()
        
        # Create log-spaced grid
        # Note: Grid size should be ~2-3x smaller than average number of samples
        # to avoid too sparse distributions (which make barycenter uniform)
        grid = np.logspace(np.log10(min_val), np.log10(max_val), n_grid)
        
        print()
        print(f"Creating common support grid with {n_grid} points")
        print(f"  Range: [{min_val:.3e}, {max_val:.3e}]")
        print()
        
        # Discretize each distribution onto the grid
        # Use histogram with consistent binning
        discretized_distributions = []
        
        # Define bin edges for consistent histogramming
        bin_edges = np.concatenate([[grid[0] / 2], (grid[:-1] + grid[1:]) / 2, [grid[-1] * 2]])
        
        for values, weights in zip(all_values, all_weights):
            # Filter out zero values
            mask = values > 0
            values_filtered = values[mask]
            weights_filtered = weights[mask]
            
            if len(values_filtered) == 0:
                # Use uniform if no valid values
                hist = np.ones(len(grid)) / len(grid)
            else:
                # Create histogram on the grid with consistent bins
                hist, _ = np.histogram(values_filtered, bins=bin_edges, weights=weights_filtered)
                # Normalize to probability distribution
                hist_sum = hist.sum()
                if hist_sum > 0:
                    hist = hist / hist_sum
                else:
                    hist = np.ones(len(grid)) / len(grid)
            
            discretized_distributions.append(hist)
        
        # Stack into a matrix (n_distributions x n_grid)
        distributions_matrix = np.array(discretized_distributions)
        
        # Compute barycenter using POT's barycenter algorithm
        # Precompute cost matrix (L1 distance, grid already log-spaced)
        cost_matrix = np.abs(grid.reshape(-1, 1) - grid.reshape(1, -1))
        
        print("Computing Wasserstein barycenter...")
        
        # Use linear program barycenter (exact optimal transport solution)
        # Note: ot.bregman.barycenter() (Sinkhorn) fails with sparse discretized data,
        # returning uniform distribution. LP solver is more robust but slower.
        barycenter = ot.lp.barycenter(
            distributions_matrix.T,  # Transpose: columns are distributions
            cost_matrix,
            weights=None,  # Equal weights for all distributions
            verbose=False
        )
        
        print(f"Barycenter computation complete")
        
        # Display results
        print("=" * 60)
        print("WASSERSTEIN BARYCENTER")
        print("=" * 60)
        print(f"Number of files: {len(tsv_files)}")
        print(f"Grid size: {len(grid)}")
        print(f"Barycenter (first 10 grid points):")
        for i in range(min(10, len(grid))):
            print(f"  grid[{i}] = {grid[i]:.6e}, prob = {barycenter[i]:.6e}")
        print(f"Barycenter statistics:")
        print(f"  Total probability: {barycenter.sum():.10f}")
        print(f"  Max probability: {barycenter.max():.10e}")
        nonzero = barycenter[barycenter > 0]
        if len(nonzero) > 0:
            entropy = -np.sum(nonzero * np.log(nonzero))
            print(f"  Entropy: {entropy:.6f}")
        print("=" * 60)
        
        # Save barycenter to file
        output_file = os.path.join(input_folder, "barycenter.npz")
        np.savez(output_file, grid=grid, barycenter=barycenter)
        print(f"\nBarycenter saved to: {output_file}")
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
