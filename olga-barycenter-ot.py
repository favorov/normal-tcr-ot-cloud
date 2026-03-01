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


def load_distribution(filepath, freq_column, weights_column, productive_filter=False, vdj_filter=False):
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
    productive_filter : bool
        If True and 'productive' column exists, filter only productive sequences
    vdj_filter : bool
        If True, require non-empty v_call/d_call/j_call for existing columns
    
    Returns:
    --------
    tuple: (sample_values, weights)
    """
    df = pd.read_csv(filepath, sep='\t')
    
    # Apply productive filter if requested and column exists
    if productive_filter and 'productive' in df.columns:
        df = df[df['productive'] == True].copy()

    # Apply VDJ filter if requested (for existing columns only)
    if vdj_filter:
        for vdj_col in ['v_call', 'd_call', 'j_call']:
            if vdj_col in df.columns:
                mask = df[vdj_col].notna() & (df[vdj_col].astype(str).str.strip() != "")
                df = df[mask].copy()
    
    # Get sample values
    freq_idx = get_column_index(df, freq_column)
    sample_values = df.iloc[:, freq_idx].values.astype(float)

    if len(sample_values) == 0:
        raise ValueError(
            f"No valid rows remaining after filtering for file '{filepath}'. "
            "Check --productive-filter / --vdj-filter or input data."
        )
    
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
    if weights.sum() <= 0:
        raise ValueError(f"Weights sum to zero after filtering for file '{filepath}'.")
    weights = weights / weights.sum()
    
    return sample_values, weights


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python olga-barycenter-ot.py <input_folder> [--freq-column <col>] [--weights-column <col>] [--n-grid <n>] [--barycenter <file>] [--productive-filter] [--vdj-filter]")
        print("\nParameters:")
        print("  input_folder      : Path to folder containing TSV files")
        print("  --freq-column     : Column index (0-based) or column name for sample values (default: pgen)")
        print("  --weights-column  : Column index (0-based) or column name for weights, or 'off' (default: duplicate_frequency_percent)")
        print("  --n-grid          : Number of grid points (default: 200)")
        print("  --barycenter      : Output filename for barycenter (default: barycenter.npz)")
        print("  --productive-filter: Filter only productive sequences (default: off)")
        print("  --vdj-filter      : Require non-empty v_call/d_call/j_call for existing columns")
        print("\nExamples:")
        print("  python olga-barycenter-ot.py input/test-cloud-Tumeh2014")
        print("  python olga-barycenter-ot.py input/test-cloud-Tumeh2014 --freq-column pgen --weights-column duplicate_frequency_percent")
        print("  python olga-barycenter-ot.py input/test-cloud-Tumeh2014 --n-grid 500")
        print("  python olga-barycenter-ot.py input/test-cloud-Tumeh2014 --barycenter my_barycenter.npz")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    freq_column = "pgen"
    weights_column = "duplicate_frequency_percent"
    n_grid = 200
    barycenter_file = "barycenter.npz"
    productive_filter = False
    vdj_filter = False
    
    # Parse named arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--freq-column" and i + 1 < len(sys.argv):
            freq_column = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--weights-column" and i + 1 < len(sys.argv):
            weights_column = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--n-grid" and i + 1 < len(sys.argv):
            try:
                n_grid = int(sys.argv[i + 1])
            except ValueError:
                print(f"Error: --n-grid must be an integer, got '{sys.argv[i + 1]}'")
                sys.exit(1)
            if n_grid <= 1:
                print("Error: --n-grid must be > 1")
                sys.exit(1)
            i += 2
        elif sys.argv[i] == "--barycenter" and i + 1 < len(sys.argv):
            barycenter_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--productive-filter":
            productive_filter = True
            i += 1
        elif sys.argv[i] == "--vdj-filter":
            vdj_filter = True
            i += 1
        else:
            print(f"Error: Unknown argument '{sys.argv[i]}'")
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
            values, weights = load_distribution(filepath, freq_column, weights_column, productive_filter, vdj_filter)
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
        # Compute cost matrix using log_l1 metric (consistent with p2p, p2b)
        # L1 distance in log space for robust handling of extreme pgen ranges
        log_grid = np.log(grid)
        cost_matrix = np.abs(log_grid.reshape(-1, 1) - log_grid.reshape(1, -1))
        
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
        # Determine path for barycenter file
        if os.path.isabs(barycenter_file) or barycenter_file.startswith('~'):
            output_file = os.path.expanduser(barycenter_file)
        else:
            output_file = os.path.join(input_folder, barycenter_file)
        
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
