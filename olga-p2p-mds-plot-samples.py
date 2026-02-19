#!/usr/bin/env python3
"""
Simplified MDS visualization of sample distributions.
Computes pairwise distances between samples and visualizes them using MDS.
Samples from different directories are color-coded.
"""

import sys
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import MDS
from adjustText import adjust_text
from ot_utils import (
    _label_from_filename,
    load_distribution,
    compute_wasserstein_distance,
    discretize_distribution,
    extend_grid_if_needed
)


def _load_sample_files(samples_path):
    """
    Load sample files from folder or text file.
    
    Parameters
    ----------
    samples_path : Path or str
        Either a folder with TSV files or a text file with one path per line.
        In the text file, each line can optionally include a custom label after the path,
        separated by whitespace: /path/to/file.tsv CustomLabel
        
    Returns
    -------
    files : list of Path
        List of TSV file paths.
    output_folder : Path
        Folder for saving outputs (samples_path if folder, parent if file list).
    custom_labels : dict
        Dictionary mapping file paths to custom labels (empty if folder input or no labels specified).
    """
    samples_path = Path(os.path.expanduser(str(samples_path)))
    custom_labels = {}
    
    if samples_path.is_dir():
        files = sorted(samples_path.glob("*.tsv"))
        output_folder = samples_path
    elif samples_path.is_file():
        files = []
        with open(samples_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Split on whitespace - first part is path, rest (if any) is label
                parts = line.split(None, 1)  # split on first whitespace only
                file_path = Path(os.path.expanduser(parts[0]))
                files.append(file_path)
                if len(parts) > 1:
                    # Custom label provided
                    custom_labels[file_path] = parts[1].strip()
        
        missing = [f for f in files if not f.exists()]
        if missing:
            print(f"Error: The following files from {samples_path} do not exist:")
            for f in missing:
                print(f"  {f}")
            sys.exit(1)
        output_folder = samples_path.parent
    else:
        print(f"Error: Path does not exist: {samples_path}")
        sys.exit(1)
    
    return files, output_folder, custom_labels


def _get_directory_colors(files):
    """
    Assign colors to files based on their parent directory.
    
    Parameters
    ----------
    files : list of Path
        List of sample files
        
    Returns
    -------
    colors : dict
        Dictionary mapping file paths to colors
    dir_to_color : dict
        Dictionary mapping directory paths to colors
    """
    unique_dirs = sorted(set(f.parent for f in files))
    
    # Use highly contrasting colors for different directories
    contrasting_colors = [
        '#e6194b',  # Red
        '#3cb44b',  # Green
        '#ffe119',  # Yellow
        '#4363d8',  # Blue
        '#f58231',  # Orange
        '#911eb4',  # Purple
        '#46f0f0',  # Cyan
        '#f032e6',  # Magenta
        '#bcf60c',  # Lime
        '#fabebe',  # Pink
        '#008080',  # Teal
        '#e6beff',  # Lavender
        '#9a6324',  # Brown
        '#fffac8',  # Beige
        '#800000',  # Maroon
        '#aaffc3',  # Mint
        '#808000',  # Olive
        '#ffd8b1',  # Apricot
        '#000075',  # Navy
        '#808080',  # Grey
    ]
    
    dir_to_color = {}
    for i, directory in enumerate(unique_dirs):
        color_idx = i % len(contrasting_colors)
        dir_to_color[directory] = contrasting_colors[color_idx]
    
    # Map files to colors
    colors = {f: dir_to_color[f.parent] for f in files}
    
    return colors, dir_to_color


def _compute_pairwise_distances(files, freq_column, weights_column, productive_filter):
    """
    Compute pairwise Wasserstein distances between samples.
    
    Parameters
    ----------
    files : list of Path
        List of sample files
    freq_column : str
        Frequency column name/index
    weights_column : str
        Weights column name/index
    productive_filter : bool
        If True, filter only productive sequences
        
    Returns
    -------
    distances : np.ndarray
        (n_files, n_files) distance matrix
    extended_grid : np.ndarray
        Extended grid (if needed)
    """
    n_files = len(files)
    distances = np.zeros((n_files, n_files))
    
    # First pass: load all samples and extend grid if needed
    all_samples = []
    all_values = []
    
    for file_path in files:
        values, weights = load_distribution(
            str(file_path),
            freq_column=freq_column,
            weights_column=weights_column,
            productive_filter=productive_filter
        )
        all_samples.append((values, weights))
        all_values.append(values)
    
    # Create grid from all values
    all_values_concat = np.concatenate(all_values)
    min_val = all_values_concat.min()
    max_val = all_values_concat.max()
    extended_grid = np.linspace(min_val, max_val, 500)
    
    # Compute distances
    for i in range(n_files):
        for j in range(i, n_files):
            values_i, weights_i = all_samples[i]
            values_j, weights_j = all_samples[j]
            
            # Discretize both samples on extended grid
            disc_i = discretize_distribution(values_i, weights_i, extended_grid)
            disc_j = discretize_distribution(values_j, weights_j, extended_grid)
            
            # Compute distance
            distance = compute_wasserstein_distance(
                extended_grid, disc_i,
                extended_grid, disc_j,
                metric="log_l1",
                method="emd"
            )
            distances[i, j] = distance
            distances[j, i] = distance
    
    return distances, extended_grid


def main():
    """Main function."""
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Usage: python olga-simple-ot-mds-plot.py <samples> [options]")
        print("\nParameters:")
        print("  samples               : Either:")
        print("                          - Folder with TSV files")
        print("                          - Text file with one TSV file path per line (with optional labels)")
        print("  --freq-column <col>   : Column index or name for frequencies (default: pgen)")
        print("  --weights-column <col>: Column index or name for weights, or 'off' (default: duplicate_frequency_percent)")
        print("  --output-plot <file>  : Output plot filename (default: ot-simple-mds-plot.png)")
        print("  --productive-filter   : Filter only productive sequences (if productive column exists)")
        print("\nOutput:")
        print("  MDS visualization with points color-coded by source directory")
        print("  Plot saved in samples folder (or parent folder if samples is a file list)")
        print("\nExamples:")
        print("  python olga-simple-ot-mds-plot.py input/samples-folder")
        print("  python olga-simple-ot-mds-plot.py samples_list.txt --output-plot mds.png")
        sys.exit(1 if len(sys.argv) < 2 else 0)

    samples_path = Path(sys.argv[1])

    freq_column = "pgen"
    weights_column = "duplicate_frequency_percent"
    output_plot = "ot-simple-p2p-mds-plot.png"
    productive_filter = False

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--freq-column" and i + 1 < len(sys.argv):
            freq_column = sys.argv[i + 1]
            i += 2
        elif arg == "--weights-column" and i + 1 < len(sys.argv):
            weights_column = sys.argv[i + 1]
            i += 2
        elif arg == "--output-plot" and i + 1 < len(sys.argv):
            output_plot = sys.argv[i + 1]
            i += 2
        elif arg == "--productive-filter":
            productive_filter = True
            i += 1
        else:
            i += 1

    # Get TSV files
    samples_files, output_folder, custom_labels = _load_sample_files(samples_path)

    if not samples_files:
        print(f"Error: No sample TSV files found")
        sys.exit(1)

    print(f"Found {len(samples_files)} sample files")

    # Compute pairwise distances
    print("Computing pairwise distances...")
    distances, extended_grid = _compute_pairwise_distances(
        samples_files, freq_column, weights_column, productive_filter
    )

    # Apply MDS
    print("Computing MDS...")
    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
    mds_coords = mds.fit_transform(distances)

    # Get colors by directory
    colors, dir_to_color = _get_directory_colors(samples_files)

    # Create plot
    fig, ax = plt.subplots(figsize=(14, 12))

    # Plot samples with colors by directory
    texts = []
    for i, file_path in enumerate(samples_files):
        x, y = mds_coords[i, 0], mds_coords[i, 1]
        color = colors[file_path]
        
        ax.scatter(
            x, y,
            c=[color], s=100, alpha=0.6, edgecolors='black', linewidth=1,
            zorder=3
        )
        
        # Add label - use custom if provided, otherwise auto-generate
        label = custom_labels.get(file_path, _label_from_filename(file_path))
        txt = ax.text(
            x, y + 0.05,
            label,
            ha='center', va='bottom',
            fontsize=9, fontweight='bold',
            color='#000000',
            zorder=4
        )
        texts.append(txt)

    # Move labels to avoid overlaps
    adjust_text(
        texts,
        expand_points=(1.2, 1.2),
        expand_text=(1.1, 1.1),
        force_points=0.2,
        force_text=0.3
    )

    # Labels and title
    ax.set_xlabel('MDS Dimension 1', fontsize=12, fontweight='bold')
    ax.set_ylabel('MDS Dimension 2', fontsize=12, fontweight='bold')
    ax.set_title('MDS: Sample Distributions', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')

    # Legend - show directories
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=dir_to_color[d], edgecolor='black', label=str(d))
        for d in sorted(dir_to_color.keys())
    ]
    ax.legend(handles=legend_elements, loc='best', fontsize=10, title='Directory')

    # Determine output path
    if os.path.isabs(output_plot) or os.path.dirname(output_plot):
        output_path = os.path.expanduser(output_plot)
    else:
        output_path = os.path.join(output_folder, output_plot)

    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {output_path}")
    plt.close()


if __name__ == "__main__":
    main()
