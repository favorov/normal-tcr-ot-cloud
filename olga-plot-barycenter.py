#!/usr/bin/env python3
"""
Plot distributions from TSV files and their Wasserstein barycenter on a single figure.
"""

import sys
import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


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


def discretize_on_grid(values, weights, grid):
    """
    Discretize a weighted distribution onto a grid.
    
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
    if len(sys.argv) < 2:
        print("Usage: python olga-plot-barycenter.py <input_folder> [--barycenter <file>] [--weights-column <col>] [--freq-column <col>] [--output-plot <file>]")
        print("\nParameters:")
        print("  input_folder        : Path to folder containing TSV files")
        print("  --barycenter <file> : Path to barycenter NPZ file (default: barycenter.npz in input_folder)")
        print("  --freq-column       : Column for frequencies (default: pgen)")
        print("  --weights-column    : Column for weights (default: off)")
        print("  --output-plot <file>: Output plot filename (default: barycenter_plot.png)")
        print("\nExamples:")
        print("  python olga-plot-barycenter.py input/test-cloud-Tumeh2014")
        print("  python olga-plot-barycenter.py input/test-cloud-Tumeh2014 --barycenter ~/data/mybarycenter.npz")
        print("  python olga-plot-barycenter.py input/test-cloud-Tumeh2014 --output-plot my_plot.png")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    barycenter_file = "barycenter.npz"
    freq_column = "pgen"
    weights_column = "off"
    output_plot = "barycenter_plot.png"
    
    # Parse remaining arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--freq-column" and i + 1 < len(sys.argv):
            freq_column = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--weights-column" and i + 1 < len(sys.argv):
            weights_column = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--barycenter" and i + 1 < len(sys.argv):
            barycenter_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--output-plot" and i + 1 < len(sys.argv):
            output_plot = sys.argv[i + 1]
            i += 2
        else:
            print(f"Error: Unknown argument '{sys.argv[i]}'")
            sys.exit(1)
    
    # Determine path to barycenter file
    if os.path.isabs(barycenter_file) or barycenter_file.startswith('~'):
        # Absolute or relative path with ~
        barycenter_path = os.path.expanduser(barycenter_file)
    else:
        # Just a filename - search in input_folder
        barycenter_path = os.path.join(input_folder, barycenter_file)
    
    # Check if barycenter file exists
    if not os.path.exists(barycenter_path):
        print(f"Error: Barycenter file not found: {barycenter_path}")
        sys.exit(1)
    
    # Load barycenter and grid
    print(f"Loading barycenter from: {barycenter_path}")
    data = np.load(barycenter_path)
    grid = data['grid']
    barycenter = data['barycenter']
    print(f"  Grid size: {len(grid)}")
    print(f"  Grid range: [{grid[0]:.3e}, {grid[-1]:.3e}]")
    print()
    
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
        discretized_distributions = []
        filenames = []
        
        for filepath in tsv_files:
            filename = os.path.basename(filepath)
            values, weights = load_distribution(filepath, freq_column, weights_column)
            
            # Discretize on the barycenter's grid
            dist = discretize_on_grid(values, weights, grid)
            discretized_distributions.append(dist)
            filenames.append(filename)
            
            print(f"  Loaded {filename}: {len(values)} samples")
        
        print()
        print("Generating plot...")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(26, 14))
        
        # Plot all individual distributions in light gray
        for i, dist in enumerate(discretized_distributions):
            ax.plot(grid, dist, color='gray', alpha=0.25, linewidth=1.0, label='Individual distributions' if i == 0 else '')
        
        # Plot barycenter in red with thicker line
        ax.plot(grid, barycenter, color='red', linewidth=2.5, label='Wasserstein Barycenter', zorder=10)
        
        # Set logarithmic scale for x-axis
        ax.set_xscale('log')
        
        # Labels and formatting
        ax.set_xlabel('pgen (log scale)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Probability Density', fontsize=12, fontweight='bold')
        ax.set_title(f'Wasserstein Barycenter of {len(discretized_distributions)} TCR Distributions', fontsize=14, fontweight='bold')
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add legend
        ax.legend(fontsize=11, loc='best')
        
        # Make layout tight
        plt.tight_layout()
        
        # Save figure - determine output path
        if os.path.isabs(output_plot) or os.path.dirname(output_plot):
            output_path = os.path.expanduser(output_plot)
        else:
            output_path = os.path.join(input_folder, output_plot)
        
        print(f"Saving plot to: {output_path}")
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        
        print("Plot generated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
