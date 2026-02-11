#!/usr/bin/env python3
"""
Plot all distributions and the free-support Wasserstein barycenter.
Individual distributions shown in light gray, barycenter highlighted in red.
"""
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path


def load_distribution(filepath, freq_column="pgen"):
    """Load distribution from TSV file"""
    df = pd.read_csv(filepath, sep='\t')
    
    if isinstance(freq_column, str):
        if freq_column in df.columns:
            col_idx = df.columns.get_loc(freq_column)
        else:
            col_idx = int(freq_column)
    else:
        col_idx = freq_column
    
    values = df.iloc[:, col_idx].values
    return values[values > 0]


def main():
    if len(sys.argv) < 2:
        print("Usage: python olga-plot-barycenter-free-support.py <input_folder> [barycenter_file] [--freq-column <col>]")
        print("\nParameters:")
        print("  input_folder: folder with TSV files")
        print("  barycenter_file: path to barycenter NPZ file (default: barycenter_free_support.npz)")
        print("  --freq-column: column index/name for sample values (default: pgen)")
        print("\nExamples:")
        print("  python olga-plot-barycenter-free-support.py input/test-cloud-Tumeh2014")
        print("  python olga-plot-barycenter-free-support.py input/test-cloud-Tumeh2014 barycenter_free_support.npz")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    barycenter_file = "barycenter_free_support.npz"
    freq_column = "pgen"
    
    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--freq-column" and i + 1 < len(sys.argv):
            freq_column = sys.argv[i + 1]
            i += 2
        elif not sys.argv[i].startswith("--"):
            barycenter_file = sys.argv[i]
            i += 1
        else:
            i += 1
    
    input_path = Path(input_folder)
    
    # Handle relative paths (like ~/data/file.npz)
    if barycenter_file.startswith("~"):
        barycenter_path = Path(barycenter_file).expanduser()
    else:
        barycenter_path = input_path / barycenter_file
    
    print(f"Loading barycenter from: {barycenter_path}")
    
    if not barycenter_path.exists():
        print(f"Error: Barycenter file not found: {barycenter_path}")
        sys.exit(1)
    
    # Load barycenter
    barycenter_data = np.load(barycenter_path)
    barycenter_weights = barycenter_data['barycenter']
    barycenter_support = barycenter_data['support']
    
    print(f"  Support points: {len(barycenter_support)}")
    print(f"  Support range: [{barycenter_support.min():.3e}, {barycenter_support.max():.3e}]")
    print()
    
    # Find all TSV files
    tsv_files = sorted(input_path.glob("*.tsv"))
    
    if not tsv_files:
        print(f"Error: No TSV files found in {input_folder}")
        sys.exit(1)
    
    print(f"Found {len(tsv_files)} TSV file(s)")
    print(f"Frequency column: {freq_column}")
    print()
    
    # Load all distributions
    all_distributions = []
    all_values = []
    
    for fpath in tsv_files:
        values = load_distribution(str(fpath), freq_column)
        all_distributions.append(values)
        all_values.extend(values)
        print(f"  Loaded {fpath.name}: {len(values)} samples")
    
    all_values = np.array(all_values)
    
    # Create common visualization grid (log-spaced)
    log_min = np.log(all_values.min())
    log_max = np.log(all_values.max())
    n_grid = 300
    vis_grid = np.logspace(np.log10(all_values.min()), np.log10(all_values.max()), n_grid)
    
    print()
    print("Generating plot...")
    
    # Create figure with log scale
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # ========== TOP PLOT: LINEAR SCALE ==========
    ax = ax1
    ax.set_xscale('log')
    
    # Plot individual distributions
    for values in all_distributions:
        hist, edges = np.histogram(values, bins=100)
        hist = hist / hist.sum()
        bin_centers = (edges[:-1] + edges[1:]) / 2
        ax.plot(bin_centers, hist, color='lightgray', alpha=0.5, linewidth=0.5)
    
    # Plot barycenter
    ax.scatter(barycenter_support, barycenter_weights, 
               color='red', s=50, alpha=0.8, label='Barycenter (free-support)', zorder=5, edgecolors='darkred')
    
    # Connect barycenter points with lines for visibility
    sorted_idx = np.argsort(barycenter_support)
    ax.plot(barycenter_support[sorted_idx], barycenter_weights[sorted_idx], 
            color='red', linewidth=2.5, alpha=0.7, zorder=4)
    
    ax.set_xlabel('pgen (log scale)', fontsize=12)
    ax.set_ylabel('Probability', fontsize=12)
    ax.set_title('Individual Distributions and Free-Support Barycenter', fontsize=14, fontweight='bold')
    
    # Create custom legend
    gray_patch = mpatches.Patch(facecolor='lightgray', alpha=0.5, label='Individual distributions')
    red_patch = mpatches.Patch(facecolor='red', alpha=0.8, label='Barycenter (free-support)')
    ax.legend(handles=[gray_patch, red_patch], loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # ========== BOTTOM PLOT: DISCRETIZED VIEW ==========
    ax = ax2
    ax.set_xscale('log')
    
    # Discretize all distributions onto visualization grid
    for values in all_distributions:
        bin_edges = np.concatenate([[vis_grid[0] / 2], (vis_grid[:-1] + vis_grid[1:]) / 2, [vis_grid[-1] * 2]])
        hist, _ = np.histogram(values, bins=bin_edges)
        hist = hist / hist.sum()
        ax.step(vis_grid, hist, where='mid', color='lightgray', alpha=0.4, linewidth=0.8)
    
    # Discretize barycenter onto visualization grid
    bin_edges = np.concatenate([[vis_grid[0] / 2], (vis_grid[:-1] + vis_grid[1:]) / 2, [vis_grid[-1] * 2]])
    barycenter_binned = np.zeros(len(vis_grid))
    
    for i, x in enumerate(barycenter_support):
        # Find nearest bin
        idx = np.searchsorted(vis_grid, x, side='left')
        if idx >= len(vis_grid):
            idx = len(vis_grid) - 1
        barycenter_binned[idx] += barycenter_weights[i]
    
    ax.step(vis_grid, barycenter_binned, where='mid', 
            color='red', linewidth=3, alpha=0.9, label='Barycenter (discretized)', zorder=5)
    
    ax.set_xlabel('pgen (log scale)', fontsize=12)
    ax.set_ylabel('Probability (discretized)', fontsize=12)
    ax.set_title('Discretized View (visualization grid)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    # Save plot
    output_file = input_path / "barycenter_free_support_plot.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saving plot to: {output_file}")
    
    plt.close()
    
    print("Plot generated successfully!")


if __name__ == "__main__":
    main()
