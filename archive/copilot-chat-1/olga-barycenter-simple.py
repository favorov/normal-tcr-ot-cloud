#!/usr/bin/env python3
"""
Compute simple average (arithmetic mean) of all distributions.
Better than OT barycenter for summary statistics when outliers are present.
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path


def load_and_prepare_distribution(filepath, freq_column="pgen", weights_column="off"):
    """
    Load distribution from TSV file and return (values, weights).
    
    Parameters:
    - filepath: Path to TSV file
    - freq_column: Column name or 0-based index for frequency values
    - weights_column: Column name / index for sample weights, or "off" for uniform weights
    
    Returns:
    - (values, weights): numpy arrays of floats
    """
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
        weights = weights / weights.sum()  # Normalize
    
    return values_filtered, weights


def discretize_to_grid(values, weights, grid):
    """Discretize samples onto grid points."""
    # Define bin edges
    bin_edges = np.concatenate([[grid[0] / 2], (grid[:-1] + grid[1:]) / 2, [grid[-1] * 2]])
    
    # Create histogram
    hist, _ = np.histogram(values, bins=bin_edges, weights=weights)
    
    # Normalize to probability distribution
    hist_sum = hist.sum()
    if hist_sum > 0:
        hist = hist / hist_sum
    else:
        hist = np.ones(len(grid)) / len(grid)
    
    return hist


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python olga-barycenter-simple.py <input_folder> [--freq-column <col>] [--weights-column <col>] [--n-grid <n>]")
        print("\nParameters:")
        print("  input_folder      : Path to folder containing TSV files")
        print("  --freq-column     : Column index (0-based) or column name for frequencies (default: pgen)")
        print("  --weights-column  : Column index (0-based) or column name for weights, or 'off' (default: off)")
        print("  --n-grid          : Number of grid points (default: 200)")
        print("\nExamples:")
        print("  python olga-barycenter-simple.py input/test-cloud-Tumeh2014")
        print("  python olga-barycenter-simple.py input/test-cloud-Tumeh2014 --freq-column pgen --weights-column duplicate_frequency_percent")
        print("  python olga-barycenter-simple.py input/test-cloud-Tumeh2014 --n-grid 500")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    freq_column = "pgen"
    weights_column = "off"
    n_grid = 200
    
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
        all_values = []
        distributions_list = []
        
        for fpath in tsv_files:
            values, weights = load_and_prepare_distribution(str(fpath), freq_column, weights_column)
            all_values.extend(values)
            distributions_list.append((values, weights))
            print(f"  Loaded {fpath.name}: {len(values)} samples")
        
        all_values = np.array(all_values)
        
        # Create common support grid (log scale for pgen values)
        all_concatenated = np.concatenate([v for v, w in distributions_list])
        all_concatenated = all_concatenated[all_concatenated > 0]
        
        if len(all_concatenated) == 0:
            print("Error: No valid (non-zero) values found in data")
            sys.exit(1)
        
        min_val = all_concatenated.min()
        max_val = all_concatenated.max()
        
        # Create log-spaced grid
        grid = np.logspace(np.log10(min_val), np.log10(max_val), n_grid)
        
        print()
        print(f"Creating common support grid with {n_grid} points")
        print(f"  Range: [{min_val:.3e}, {max_val:.3e}]")
        print()
        
        # Discretize each distribution onto the grid
        distributions_matrix = []
        for values, weights in distributions_list:
            hist = discretize_to_grid(values, weights, grid)
            distributions_matrix.append(hist)
        
        distributions_matrix = np.array(distributions_matrix)  # Shape: (n_files, n_grid)
        
        # Compute simple average (arithmetic mean)
        print("Computing simple average (arithmetic mean of distributions)...")
        barycenter = distributions_matrix.mean(axis=0)
        
        # Save to NPZ file
        output_file = input_path / "barycenter_simple.npz"
        np.savez(output_file, grid=grid, barycenter=barycenter)
        
        print("Simple average computation complete")
        print("=" * 60)
        print("SIMPLE AVERAGE BARYCENTER")
        print("=" * 60)
        print(f"Number of files: {len(distributions_matrix)}")
        print(f"Grid size: {n_grid}")
        print("Barycenter (first 10 grid points):")
        for i in range(min(10, len(grid))):
            print(f"  grid[{i}] = {grid[i]:.6e}, prob = {barycenter[i]:.10e}")
        
        print("Barycenter statistics:")
        print(f"  Total probability: {barycenter.sum():.10f}")
        print(f"  Max probability: {barycenter.max():.10e}")
        print(f"  Entropy: {-np.sum(barycenter[barycenter > 0] * np.log(barycenter[barycenter > 0])):.6f}")
        print("=" * 60)
        
        print(f"\nBarycenter saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
