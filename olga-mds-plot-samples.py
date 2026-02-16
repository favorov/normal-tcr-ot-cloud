#!/usr/bin/env python3
"""
MDS visualization of sample distributions relative to a barycenter.
Computes all pairwise distances between samples and barycenter,
then visualizes them using Multidimensional Scaling (MDS).
"""

import sys
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
from sklearn.manifold import MDS
from adjustText import adjust_text
from ot_utils import (
    _label_from_filename,
    load_distribution,
    load_barycenter,
    compute_wasserstein_distance,
    discretize_distribution,
    extend_grid_if_needed
)


def _resolve_barycenter_path(barycenter_folder, barycenter_file):
    """Resolve barycenter file path (absolute or relative to folder)."""
    if os.path.isabs(barycenter_file) or barycenter_file.startswith("~"):
        return Path(os.path.expanduser(barycenter_file))
    return barycenter_folder / barycenter_file


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


def _create_8pointed_star_marker():
    """Create an 8-pointed star marker using matplotlib Path."""
    n_points = 8
    # Outer points
    angles_outer = np.linspace(0, 2*np.pi, n_points, endpoint=False)
    # Inner points (between outer points)
    angles_inner = angles_outer + np.pi / n_points
    
    # Create vertices alternating between outer and inner points
    vertices = []
    for i in range(n_points):
        # Outer point
        vertices.append([np.cos(angles_outer[i]), np.sin(angles_outer[i])])
        # Inner point
        vertices.append([0.4 * np.cos(angles_inner[i]), 0.4 * np.sin(angles_inner[i])])
    
    vertices = np.array(vertices)
    # Close the path
    vertices = np.vstack([vertices, vertices[0]])
    
    # Create path codes
    codes = [mpath.Path.MOVETO] + [mpath.Path.LINETO] * (len(vertices) - 2) + [mpath.Path.CLOSEPOLY]
    
    return mpath.Path(vertices, codes)


def _compute_pairwise_distances(files, grid, barycenter_weights, freq_column, weights_column):
    """
    Compute pairwise Wasserstein distances between samples.
    
    Parameters
    ----------
    files : list of Path
        List of sample files
    grid : np.ndarray
        Grid for discretization
    barycenter_weights : np.ndarray
        Barycenter weights
    freq_column : str
        Frequency column name/index
    weights_column : str
        Weights column name/index
        
    Returns
    -------
    distances : np.ndarray
        (n_files, n_files) distance matrix
    extended_grid : np.ndarray
        Extended grid (if needed)
    extended_barycenter : np.ndarray
        Extended barycenter weights
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
            weights_column=weights_column
        )
        all_samples.append((values, weights))
        all_values.append(values)
    
    # Extend grid to cover all samples
    extended_grid, extended_barycenter = extend_grid_if_needed(
        grid, barycenter_weights,
        np.concatenate(all_values).min(),
        np.concatenate(all_values).max()
    )
    
    # Compute distances
    for i in range(n_files):
        for j in range(n_files):
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
    
    return distances, extended_grid, extended_barycenter


def _compute_distances_to_barycenter(files, grid, barycenter_weights, freq_column, weights_column):
    """
    Compute distances from samples to barycenter.
    
    Parameters
    ----------
    files : list of Path
        List of sample files
    grid : np.ndarray
        Barycenter grid
    barycenter_weights : np.ndarray
        Barycenter weights
    freq_column : str
        Frequency column name/index
    weights_column : str
        Weights column name/index
        
    Returns
    -------
    distances : np.ndarray
        1D array of distances to barycenter
    extended_grid : np.ndarray
        Extended grid
    extended_barycenter : np.ndarray
        Extended barycenter
    """
    # Load all samples first to determine grid extension
    all_samples = []
    all_values = []
    
    for file_path in files:
        values, weights = load_distribution(
            str(file_path),
            freq_column=freq_column,
            weights_column=weights_column
        )
        all_samples.append((values, weights))
        all_values.append(values)
    
    # Extend grid
    extended_grid, extended_barycenter = extend_grid_if_needed(
        grid, barycenter_weights,
        np.concatenate(all_values).min(),
        np.concatenate(all_values).max()
    )
    
    # Compute distances to barycenter
    distances = []
    for values, weights in all_samples:
        sample_discretized = discretize_distribution(values, weights, extended_grid)
        distance = compute_wasserstein_distance(
            extended_grid, sample_discretized,
            extended_grid, extended_barycenter,
            metric="log_l1",
            method="emd"
        )
        distances.append(distance)
    
    return np.array(distances), extended_grid, extended_barycenter


def main():
    """Main function."""
    if len(sys.argv) < 3 or sys.argv[1] in ["-h", "--help"]:
        print("Usage: python olga-mds-plot-samples.py <barycenter_folder> <samples> [options]")
        print("\nParameters:")
        print("  barycenter_folder     : Folder containing TSV files and barycenter.npz")
        print("  samples               : Either:")
        print("                          - Folder with TSV files to map")
        print("                          - Text file with one TSV file path per line")
        print("  --freq-column <col>   : Column index or name for frequencies (default: pgen)")
        print("  --weights-column <col>: Column index or name for weights, or 'off' (default: off)")
        print("  --barycenter <file>   : Barycenter file (default: barycenter.npz)")
        print("  --output-plot <file>  : Output plot filename (default: ot-mds-plot.png)")
        print("\nOutput:")
        print("  MDS visualization with light green (normal samples + barycenter) and orange (mapped samples)")
        print("  Plot saved in samples folder (or parent folder if samples is a file list)")
        print("\nExamples:")
        print("  python olga-mds-plot-samples.py input/test-cloud-Tumeh2014 input/new-samples")
        print("  python olga-mds-plot-samples.py input/test-cloud-Tumeh2014 samples_list.txt \\")
        print("    --weights-column duplicate_frequency_percent --output-plot mds_comparison.png")
        sys.exit(1 if len(sys.argv) < 3 else 0)

    barycenter_folder = Path(sys.argv[1])
    samples_path = Path(sys.argv[2])

    freq_column = "pgen"
    weights_column = "off"
    barycenter_file = "barycenter.npz"
    output_plot = "ot-mds-plot.png"

    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--freq-column" and i + 1 < len(sys.argv):
            freq_column = sys.argv[i + 1]
            i += 2
        elif arg == "--weights-column" and i + 1 < len(sys.argv):
            weights_column = sys.argv[i + 1]
            i += 2
        elif arg == "--barycenter" and i + 1 < len(sys.argv):
            barycenter_file = sys.argv[i + 1]
            i += 2
        elif arg == "--output-plot" and i + 1 < len(sys.argv):
            output_plot = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # Load barycenter
    barycenter_path = _resolve_barycenter_path(barycenter_folder, barycenter_file)
    print(f"Loading barycenter from {barycenter_path}")
    grid, barycenter_weights = load_barycenter(str(barycenter_path))

    # Get TSV files
    barycenter_files = sorted(barycenter_folder.glob("*.tsv"))
    samples_files, output_folder, custom_labels = _load_sample_files(samples_path)

    if not barycenter_files:
        print(f"Error: No TSV files found in {barycenter_folder}")
        sys.exit(1)
    if not samples_files:
        print(f"Error: No sample TSV files found")
        sys.exit(1)

    print(f"Found {len(barycenter_files)} barycenter files, {len(samples_files)} sample files")

    # Combine all files for distance computation
    all_files = barycenter_files + samples_files
    all_distances, extended_grid, extended_barycenter = _compute_pairwise_distances(
        all_files, grid, barycenter_weights,
        freq_column, weights_column
    )

    # Add barycenter as a point (distance 0 to itself)
    n_barycenter = len(barycenter_files)
    n_samples = len(samples_files)
    n_total = n_barycenter + n_samples + 1  # +1 for barycenter center point

    # Create full distance matrix including barycenter
    full_distances = np.zeros((n_total, n_total))
    full_distances[:n_barycenter + n_samples, :n_barycenter + n_samples] = all_distances

    # Distances to barycenter center point
    barycenter_dists, _, _ = _compute_distances_to_barycenter(
        all_files, extended_grid, extended_barycenter,
        freq_column, weights_column
    )
    full_distances[n_barycenter + n_samples, :n_barycenter + n_samples] = barycenter_dists
    full_distances[:n_barycenter + n_samples, n_barycenter + n_samples] = barycenter_dists

    # Apply MDS
    print("Computing MDS...")
    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
    mds_coords = mds.fit_transform(full_distances)

    # Create plot
    fig, ax = plt.subplots(figsize=(24, 20))

    # Plot barycenter files (light green #90EE90)
    for i in range(n_barycenter):
        ax.scatter(
            mds_coords[i, 0], mds_coords[i, 1],
            c='#90EE90', s=80, alpha=0.7, edgecolors='#0B5D1E', linewidth=1.5,
            zorder=2
        )

    # Plot samples (orange #F28E2B with labels)
    texts = []
    for i in range(n_samples):
        file_idx = n_barycenter + i
        x, y = mds_coords[file_idx, 0], mds_coords[file_idx, 1]
        ax.scatter(
            x, y,
            c='#F28E2B', s=100, alpha=0.8, edgecolors='black', linewidth=1.5,
            zorder=3
        )
        # Add label - use custom if provided, otherwise auto-generate
        label = custom_labels.get(samples_files[i], _label_from_filename(samples_files[i]))
        txt = ax.text(
            x, y + 0.04,
            label,
            ha='center', va='bottom',
            fontsize=9, fontweight='bold',
            color='#000000',
            zorder=4
        )
        texts.append(txt)

    # Move labels only (no arrows/boxes) to avoid overlaps
    adjust_text(
        texts,
        expand_points=(1.2, 1.2),
        expand_text=(1.1, 1.1),
        force_points=0.2,
        force_text=0.3
    )

    # Plot barycenter center (light green with 8-pointed star)
    barycenter_idx = n_barycenter + n_samples
    star_marker = _create_8pointed_star_marker()
    ax.scatter(
        mds_coords[barycenter_idx, 0], mds_coords[barycenter_idx, 1],
        c='#90EE90', s=600, alpha=0.9, marker=star_marker,
        edgecolors='#0B5D1E', linewidth=2.5,
        zorder=5
    )

    # Labels and title
    ax.set_xlabel('MDS Dimension 1', fontsize=12, fontweight='bold')
    ax.set_ylabel('MDS Dimension 2', fontsize=12, fontweight='bold')
    ax.set_title('MDS: Sample Distributions vs Barycenter', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#90EE90', edgecolor='#0B5D1E', label='Normal samples', linewidth=1.5),
        Patch(facecolor='#F28E2B', edgecolor='black', label='Mapped samples', linewidth=1.5),
    ]
    ax.legend(handles=legend_elements, loc='best', fontsize=11)

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
