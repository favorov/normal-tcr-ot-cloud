#!/usr/bin/env python3
"""
Calculate Wasserstein distance from a distribution to the barycenter.
Computes distances from sample distributions to a barycenter.
"""

import sys
import os
import argparse
import numpy as np
from pathlib import Path
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
    """Load sample files from folder or text file list."""
    samples_path = Path(os.path.expanduser(str(samples_path)))
    custom_labels = {}

    if samples_path.is_dir():
        files = sorted(samples_path.glob("*.tsv"))
    elif samples_path.is_file():
        files = []
        with open(samples_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(None, 1)
                file_path = Path(os.path.expanduser(parts[0]))
                files.append(file_path)
                if len(parts) > 1:
                    custom_labels[file_path] = parts[1].strip()

        missing = [f for f in files if not f.exists()]
        if missing:
            print(f"Error: The following files from {samples_path} do not exist:")
            for f in missing:
                print(f"  {f}")
            sys.exit(1)
    else:
        print(f"Error: Path does not exist: {samples_path}")
        sys.exit(1)

    return files, custom_labels


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Compute Wasserstein distances from sample distributions to a barycenter.",
    )
    parser.add_argument("barycenter_folder", help="Folder containing TSV files and barycenter.npz")
    parser.add_argument(
        "samples",
        help="Either folder with TSV files or text file with one TSV path per line",
    )
    parser.add_argument("--freq-column", default="pgen", dest="freq_column")
    parser.add_argument(
        "--weights-column",
        default="duplicate_frequency_percent",
        dest="weights_column",
    )
    parser.add_argument("--barycenter", default="barycenter.npz", dest="barycenter_file")
    parser.add_argument("--pipeline", action="store_true", dest="pipeline_mode")
    parser.add_argument("--statistics-only", action="store_true", dest="statistics_only")
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
    pipeline_mode = args.pipeline_mode
    statistics_only = args.statistics_only
    productive_filter = args.productive_filter
    vdj_filter = args.vdj_filter
    vj_filter = args.vj_filter

    # Load barycenter
    barycenter_path = _resolve_barycenter_path(barycenter_folder, barycenter_file)
    if not barycenter_path.exists():
        if not pipeline_mode:
            print(f"Error: Barycenter file not found: {barycenter_path}")
            print(f"Please run olga-barycenter-ot.py first to compute the barycenter.")
        sys.exit(1)
    
    if not pipeline_mode:
        print(f"Loading barycenter from: {barycenter_path}")
    try:
        grid, barycenter_weights = load_barycenter(str(barycenter_path))
        if not pipeline_mode:
            print(f"  Grid size: {len(grid)}")
            print(f"  Grid range: [{grid.min():.3e}, {grid.max():.3e}]")
            print()
    except Exception as e:
        if not pipeline_mode:
            print(f"Error loading barycenter: {e}")
        sys.exit(1)

    # Get files to process
    files_to_process, custom_labels = _load_sample_files(samples_path)
    if len(files_to_process) == 0:
        print("Error: No sample TSV files found")
        sys.exit(1)

    if not pipeline_mode:
        print(f"Processing {len(files_to_process)} sample file(s)")
        print()

    # Process files
    results = []

    for file_path in files_to_process:
        try:
            # Load distribution
            values, weights = load_distribution(
                str(file_path),
                freq_column=freq_column,
                weights_column=weights_column,
                productive_filter=productive_filter,
                vdj_filter=vdj_filter,
                vj_filter=vj_filter
            )
            
            # Extend grid if new data falls outside barycenter range
            extended_grid, extended_barycenter = extend_grid_if_needed(
                grid, barycenter_weights,
                values.min(), values.max()
            )
            
            # Discretize sample to extended grid for fair comparison
            sample_discretized = discretize_distribution(values, weights, extended_grid)
            
            # Compute distance to barycenter
            distance = compute_wasserstein_distance(
                extended_grid, sample_discretized,
                extended_grid, extended_barycenter,
                metric='log_l1',
                method='emd'
            )
            
            results.append({
                'file': file_path.name,
                'label': custom_labels.get(file_path, _label_from_filename(file_path)),
                'distance': distance,
                'n_samples': len(values)
            })

        except ValueError as e:
            # Parameter/validation errors should always be shown
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            if not pipeline_mode:
                print(f"Error processing {file_path.name}: {e}")
            continue

    if len(results) == 0:
        print("Error: No valid results to report")
        sys.exit(1)

    # Display results
    if pipeline_mode:
        results.sort(key=lambda x: x['distance'], reverse=True)
        for r in results:
            print(f"{r['distance']:.10e}")
    else:
        # Sort by distance
        results.sort(key=lambda x: x['distance'], reverse=True)

        print("=" * 80)
        print("WASSERSTEIN DISTANCES TO BARYCENTER (sorted by distance, decreasing)")
        print("=" * 80)

        if not statistics_only:
            print(f"{'Label':<10} {'File':<45} {'Distance':>15} {'Samples':>10}")
            print("-" * 80)
            for r in results:
                print(f"{r['label']:<10} {r['file']:<45} {r['distance']:>15.6e} {r['n_samples']:>10}")

        print("=" * 80)
        print("STATISTICS")
        print("=" * 80)

        distances = np.array([r['distance'] for r in results])
        print(f"Count:        {len(distances)}")
        print(f"Mean:         {np.mean(distances):.6e}")
        print(f"Median:       {np.median(distances):.6e}")
        print(f"Std:          {np.std(distances):.6e}")
        print(f"Min:          {np.min(distances):.6e} ({results[-1]['file']})")
        print(f"Max:          {np.max(distances):.6e} ({results[0]['file']})")
        print(f"Q1 (25%):     {np.percentile(distances, 25):.6e}")
        print(f"Q3 (75%):     {np.percentile(distances, 75):.6e}")
        print("=" * 80)


if __name__ == "__main__":
    main()
