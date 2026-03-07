#!/usr/bin/env python3
"""
Map sample distributions to a barycenter and plot distances.
Creates a boxplot of distances for normal samples and overlays mapped samples.
"""

import sys
import os
import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
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
    if os.path.isabs(barycenter_file) or barycenter_file.startswith("~"):
        return Path(os.path.expanduser(barycenter_file))
    return barycenter_folder / barycenter_file


def _load_sample_files(samples_path):
    """
    Load sample files from either a folder or a text file with file paths.
    
    Parameters
    ----------
    samples_path : Path
        Either a folder containing TSV files, or a text file with one file path per line.
        In the text file, each line can optionally include a custom label after the path,
        separated by whitespace: /path/to/file.tsv CustomLabel
        
    Returns
    -------
    files : list of Path
        List of sample file paths
    output_folder : Path
        Folder to use for output (samples_path if folder, parent dir if file list)
    custom_labels : dict
        Dictionary mapping file paths to custom labels (empty if folder input or no labels specified)
    """
    custom_labels = {}
    
    if samples_path.is_dir():
        # samples_path is a folder - get all TSV files
        files = sorted(samples_path.glob("*.tsv"))
        output_folder = samples_path
    elif samples_path.is_file():
        # samples_path is a file - read list of files (and optional labels)
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
        
        # Verify all files exist
        missing = [f for f in files if not f.exists()]
        if missing:
            print(f"Error: The following files from list do not exist:")
            for f in missing:
                print(f"  {f}")
            sys.exit(1)
        output_folder = samples_path.parent
    else:
        print(f"Error: samples path does not exist: {samples_path}")
        sys.exit(1)
    
    return files, output_folder, custom_labels


def _compute_distances_to_barycenter(files, grid, barycenter_weights, freq_column, weights_column, productive_filter, vdj_filter, vj_filter):
    distances = []
    for file_path in files:
        values, weights = load_distribution(
            str(file_path),
            freq_column=freq_column,
            weights_column=weights_column,
            productive_filter=productive_filter,
            vdj_filter=vdj_filter,
            vj_filter=vj_filter
        )
        extended_grid, extended_barycenter = extend_grid_if_needed(
            grid, barycenter_weights,
            values.min(), values.max()
        )
        sample_discretized = discretize_distribution(values, weights, extended_grid)
        distance = compute_wasserstein_distance(
            extended_grid, sample_discretized,
            extended_grid, extended_barycenter,
            metric="log_l1",
            method="emd"
        )
        distances.append(distance)
    return np.array(distances)


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Map sample distributions to a barycenter and plot distances.",
    )
    parser.add_argument("barycenter_folder", help="Folder containing TSV files and barycenter.npz")
    parser.add_argument(
        "samples",
        help="Either folder with TSV files to map or text file with one TSV path per line",
    )
    parser.add_argument("--freq-column", default="pgen", dest="freq_column")
    parser.add_argument(
        "--weights-column",
        default="duplicate_frequency_percent",
        dest="weights_column",
    )
    parser.add_argument("--barycenter", default="barycenter.npz", dest="barycenter_file")
    parser.add_argument(
        "--output-plot",
        default="ot-distance-boxplot.png",
        dest="output_plot",
    )
    parser.add_argument("--productive-filter", action="store_true", dest="productive_filter")
    parser.add_argument("--vdj-filter", action="store_true", dest="vdj_filter")
    parser.add_argument("--vj-filter", action="store_true", dest="vj_filter")
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()
    barycenter_folder = Path(args.barycenter_folder)
    samples_path = Path(args.samples)
    freq_column = args.freq_column
    weights_column = args.weights_column
    barycenter_file = args.barycenter_file
    output_plot = args.output_plot
    productive_filter = args.productive_filter
    vdj_filter = args.vdj_filter
    vj_filter = args.vj_filter

    try:
        barycenter_path = _resolve_barycenter_path(barycenter_folder, barycenter_file)
        if not barycenter_path.exists():
            print(f"Error: Barycenter file not found: {barycenter_path}")
            sys.exit(1)

        grid, barycenter_weights = load_barycenter(str(barycenter_path))

        normal_files = sorted(barycenter_folder.glob("*.tsv"))
        mapped_files, output_folder, custom_labels = _load_sample_files(samples_path)

        if len(normal_files) == 0:
            print(f"Error: No TSV files found in {barycenter_folder}")
            sys.exit(1)
        if len(mapped_files) == 0:
            print(f"Error: No TSV files found for samples")
            sys.exit(1)

        normal_distances = _compute_distances_to_barycenter(
            normal_files,
            grid,
            barycenter_weights,
            freq_column,
            weights_column,
            productive_filter,
            vdj_filter,
            vj_filter
        )
        mapped_distances = _compute_distances_to_barycenter(
            mapped_files,
            grid,
            barycenter_weights,
            freq_column,
            weights_column,
            productive_filter,
            vdj_filter,
            vj_filter
        )

        fig, ax = plt.subplots(figsize=(16, 12))

        boxprops = dict(facecolor="#90EE90", color="#0B5D1E")
        medianprops = dict(color="#000000", linewidth=1.5)
        whiskerprops = dict(color="#0B5D1E")
        capprops = dict(color="#0B5D1E")

        ax.boxplot(
            normal_distances,
            positions=[1],
            widths=0.4,
            patch_artist=True,
            boxprops=boxprops,
            medianprops=medianprops,
            whiskerprops=whiskerprops,
            capprops=capprops
        )

        rng = np.random.default_rng(0)
        jitter = rng.normal(0.0, 0.08, size=len(mapped_distances))
        ax.scatter(
            1 + jitter,
            mapped_distances,
            color="#F28E2B",
            edgecolor="#5C3D00",
            linewidth=0.5,
            s=35,
            zorder=3
        )

        texts = []
        for file_path, distance, offset in zip(mapped_files, mapped_distances, jitter):
            # Use custom label if provided, otherwise auto-generate
            label = custom_labels.get(file_path, _label_from_filename(file_path))
            txt = ax.text(
                1 + offset,
                distance + 0.025,
                label,
                fontsize=8,
                color="#000000",
                ha="center",
                va="bottom",
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

        ax.set_xlim(0.5, 1.5)
        ax.set_xticks([1])
        ax.set_xticklabels(["Normal vs Mapped"])
        ax.set_ylabel("Wasserstein distance to barycenter")
        ax.set_title("Distances to barycenter")
        ax.grid(axis="y", alpha=0.25)

        # Determine output path: if output_plot has directory component, use it; otherwise save in output_folder
        if os.path.isabs(output_plot) or os.path.dirname(output_plot):
            output_path = Path(os.path.expanduser(output_plot))
        else:
            output_path = output_folder / output_plot
        
        fig.tight_layout()
        fig.savefig(output_path, dpi=150)
        plt.close(fig)

        print(f"Saved plot to: {output_path}")

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
