#!/usr/bin/env python3
"""
Calculate Wasserstein distance from a distribution to the barycenter.
Computes distances from sample distributions to a barycenter.
"""

import sys
import os
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


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python olga-p2b-ot.py <barycenter_folder> <samples> [options]")
        print("\nParameters:")
        print("  barycenter_folder    : Folder containing TSV files and barycenter.npz")
        print("  samples              : Either folder with TSV files or text file with one TSV path per line")
        print("  --freq-column <col>  : Column index or name for frequencies (default: pgen)")
        print("  --weights-column <col> : Column index or name for weights, or 'off' (default: duplicate_frequency_percent)")
        print("  --barycenter <file>  : Custom barycenter file (default: barycenter.npz)")
        print("  --pipeline           : Output only distance value(s) (for use in scripts/pipelines)")
        print("  --statistics-only    : Show only statistics")
        print("  --productive-filter  : Filter only productive sequences (if productive column exists)")
        print("  --vdj-filter         : Require non-empty v_call/d_call/j_call for existing columns")
        print("  --vj-filter          : Require non-empty v_call/j_call for existing columns")
        print("\nExamples:")
        print("  # Samples from folder")
        print("  python olga-p2b-ot.py input/test-cloud-Tumeh2014 input/new-samples")
        print()
        print("  # Samples from list file")
        print("  python olga-p2b-ot.py input/test-cloud-Tumeh2014 input/samples-list-2-formats.txt")
        print()
        print("  # Custom barycenter")
        print("  python olga-p2b-ot.py input/test-cloud-Tumeh2014 input/new-samples --barycenter my_barycenter.npz")
        print()
        print("  # Pipeline mode (only distance output)")
        print("  python olga-p2b-ot.py input/test-cloud-Tumeh2014 input/new-samples --pipeline")
        sys.exit(1)

    barycenter_folder = Path(sys.argv[1])
    samples_path = Path(sys.argv[2])
    
    # Defaults
    freq_column = "pgen"
    weights_column = "duplicate_frequency_percent"
    barycenter_file = "barycenter.npz"
    pipeline_mode = False
    statistics_only = False
    productive_filter = False
    vdj_filter = False
    vj_filter = False
    
    # Parse arguments
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
        elif arg == "--pipeline":
            pipeline_mode = True
            i += 1
        elif arg == "--statistics-only":
            statistics_only = True
            i += 1
        elif arg == "--productive-filter":
            productive_filter = True
            i += 1
        elif arg == "--vdj-filter":
            vdj_filter = True
            i += 1
        elif arg == "--vj-filter":
            vj_filter = True
            i += 1
        else:
            print(f"Error: Unknown argument or invalid format '{arg}'")
            sys.exit(1)

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
