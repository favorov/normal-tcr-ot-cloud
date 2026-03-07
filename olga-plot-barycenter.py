#!/usr/bin/env python3
"""
Plot distributions from TSV files and their Wasserstein barycenter on a single figure.
"""

import sys
import os
import glob
import argparse
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


def load_distribution(filepath, freq_column, weights_column, productive_filter=False, vdj_filter=False, vj_filter=False):
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
    vj_filter : bool
        If True, require non-empty v_call/j_call for existing columns
    
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

    # Apply VJ filter if requested (for existing columns only)
    if vj_filter:
        for vj_col in ['v_call', 'j_call']:
            if vj_col in df.columns:
                mask = df[vj_col].notna() & (df[vj_col].astype(str).str.strip() != "")
                df = df[mask].copy()
    
    # Get sample values
    freq_idx = get_column_index(df, freq_column)
    sample_values = df.iloc[:, freq_idx].values.astype(float)

    if len(sample_values) == 0:
        raise ValueError(
            f"No valid rows remaining after filtering for file '{filepath}'. "
            "Check --productive-filter / --vdj-filter / --vj-filter or input data."
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


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Plot distributions from TSV files and their Wasserstein barycenter.",
    )
    parser.add_argument("input_folder", help="Path to folder containing TSV files")
    parser.add_argument("--barycenter", default="barycenter.npz", dest="barycenter_file")
    parser.add_argument("--freq-column", default="pgen", dest="freq_column")
    parser.add_argument(
        "--weights-column",
        default="duplicate_frequency_percent",
        dest="weights_column",
    )
    parser.add_argument("--output-plot", default="barycenter_plot.png", dest="output_plot")
    parser.add_argument("--productive-filter", action="store_true", dest="productive_filter")
    parser.add_argument("--vdj-filter", action="store_true", dest="vdj_filter")
    parser.add_argument("--vj-filter", action="store_true", dest="vj_filter")
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()
    input_folder = args.input_folder
    barycenter_file = args.barycenter_file
    freq_column = args.freq_column
    weights_column = args.weights_column
    output_plot = args.output_plot
    productive_filter = args.productive_filter
    vdj_filter = args.vdj_filter
    vj_filter = args.vj_filter
    
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
            values, weights = load_distribution(filepath, freq_column, weights_column, productive_filter, vdj_filter, vj_filter)
            
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
