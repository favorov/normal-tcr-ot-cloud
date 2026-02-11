#!/usr/bin/env python3
"""
Calculate Wasserstein distance between two distributions from TSV files.
Uses logarithmic grid for discretization.
"""

import sys
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


def load_and_prepare_distribution(filepath, freq_column, weights_column):
    """
    Load TSV file and extract sample values and their weights.
    
    Parameters:
    -----------
    filepath : str
        Path to the TSV file
    freq_column : str or int
        Column index or name for sample values (pgen probabilities)
    weights_column : str or int
        Column index or name for weights, or "NO"/"off" to disable weights
    
    Returns:
    --------
    tuple: (sample_values, weights)
        sample_values: The pgen probabilities to compare
        weights: The weights for each sample (normalized)
    """
    df = pd.read_csv(filepath, sep='\t')
    
    # Get sample values (pgen column)
    freq_idx = get_column_index(df, freq_column)
    sample_values = df.iloc[:, freq_idx].values.astype(float)
    
    # Check if we should use weights
    use_weights = not is_no_weights(weights_column)
    
    if use_weights:
        try:
            weights_idx = get_column_index(df, weights_column)
            weights = df.iloc[:, weights_idx].values.astype(float)
        except (ValueError, IndexError) as e:
            print(f"Warning: {e}. Using uniform weights (all 1.0).")
            weights = np.ones(len(sample_values))
    else:
        weights = np.ones(len(sample_values))
    
    # Normalize weights
    weights = weights / weights.sum()
    
    return sample_values, weights


def discretize_on_grid(values, weights, grid):
    """
    Discretize a weighted distribution onto a log-spaced grid.
    
    Parameters:
    -----------
    values : array
        Sample values
    weights : array
        Weights for each sample (normalized)
    grid : array
        Grid points for discretization
    
    Returns:
    --------
    array: Discretized probability distribution on the grid
    """
    # Filter out zero values
    mask = values > 0
    values_filtered = values[mask]
    weights_filtered = weights[mask]
    
    if len(values_filtered) == 0:
        # Use uniform if no valid values
        return np.ones(len(grid)) / len(grid)
    
    # Define bin edges for consistent histogramming
    bin_edges = np.concatenate([[grid[0] / 2], (grid[:-1] + grid[1:]) / 2, [grid[-1] * 2]])
    
    # Create histogram on the grid with consistent bins
    hist, _ = np.histogram(values_filtered, bins=bin_edges, weights=weights_filtered)
    
    # Normalize to probability distribution
    hist_sum = hist.sum()
    if hist_sum > 0:
        hist = hist / hist_sum
    else:
        hist = np.ones(len(grid)) / len(grid)
    
    return hist


def main():
    """Main function."""
    if len(sys.argv) < 6:
        print("Usage: python olga-p2p-ot.py <input_folder> <file1> <file2> <freq_column> <weights_column> [n_grid]")
        print("\nParameters:")
        print("  input_folder    : Path to folder containing TSV files")
        print("  file1           : Name of first TSV file")
        print("  file2           : Name of second TSV file")
        print("  freq_column     : Column index (0-based) or column name for frequencies")
        print("  weights_column  : Column index (0-based) or column name for weights,")
        print("                    or 'NO'/'off' to disable weights")
        print("  n_grid          : Number of grid points (default: 200)")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    file1 = sys.argv[2]
    file2 = sys.argv[3]
    freq_column = sys.argv[4]  # Keep as string, get_column_index handles both int and str
    weights_column = sys.argv[5]
    n_grid = 200
    if len(sys.argv) >= 7:
        try:
            n_grid = int(sys.argv[6])
        except ValueError:
            print(f"Error: n_grid must be an integer, got '{sys.argv[6]}'")
            sys.exit(1)
        if n_grid <= 1:
            print("Error: n_grid must be > 1")
            sys.exit(1)
    
    # Construct full file paths
    filepath1 = f"{input_folder}/{file1}"
    filepath2 = f"{input_folder}/{file2}"
    
    print(f"Loading distributions...")
    print(f"  File 1: {filepath1}")
    print(f"  File 2: {filepath2}")
    print(f"  Frequency column: {freq_column}")
    print(f"  Weights column: {weights_column}")
    print()
    
    try:
        # Load data from both files
        values1, weights1 = load_and_prepare_distribution(filepath1, freq_column, weights_column)
        values2, weights2 = load_and_prepare_distribution(filepath2, freq_column, weights_column)
        
        print(f"  Loaded {len(values1)} samples from file 1")
        print(f"  Loaded {len(values2)} samples from file 2")
        
        # Create common log-spaced grid
        all_values = np.concatenate([values1, values2])
        all_values = all_values[all_values > 0]  # Filter out zeros
        
        if len(all_values) == 0:
            print("Error: No valid (non-zero) values found in data")
            sys.exit(1)
        
        min_val = all_values.min()
        max_val = all_values.max()
        
        grid = np.logspace(np.log10(min_val), np.log10(max_val), n_grid)
        
        print(f"  Created log-spaced grid with {n_grid} points")
        print(f"  Range: [{min_val:.3e}, {max_val:.3e}]")
        print()
        
        # Discretize both distributions onto the grid
        dist1 = discretize_on_grid(values1, weights1, grid)
        dist2 = discretize_on_grid(values2, weights2, grid)
        
        # Calculate Wasserstein distance on the discretized distributions
        # Create cost matrix (L1 distance, grid already log-spaced)
        cost_matrix = np.abs(grid.reshape(-1, 1) - grid.reshape(1, -1))
        
        # Compute Earth Mover's Distance (Wasserstein)
        wd = ot.emd2(dist1, dist2, cost_matrix)
        
        # Display results
        print("=" * 60)
        print("WASSERSTEIN (OPTIMAL TRANSPORT) DISTANCE")
        print("=" * 60)
        print(f"Distance: {wd:.10e}")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
