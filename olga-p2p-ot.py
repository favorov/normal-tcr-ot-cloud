#!/usr/bin/env python3
"""
Calculate Wasserstein distances between TCR distributions.
Supports two-file comparison and all-pairs comparison from a file list.
"""

import sys
import numpy as np
from pathlib import Path
from itertools import combinations
from ot_utils import (
    load_distribution,
    compute_wasserstein_distance,
    discretize_distribution,
    create_common_grid
)


def compute_distance_single_pair(file1, file2, freq_column, weights_column, n_grid, productive_filter=False, vdj_filter=False):
    """Compute distance between two specific files."""
    filepath1 = Path(file1)
    filepath2 = Path(file2)
    
    values1, weights1 = load_distribution(str(filepath1), freq_column, weights_column, productive_filter, vdj_filter)
    values2, weights2 = load_distribution(str(filepath2), freq_column, weights_column, productive_filter, vdj_filter)
    
    grid = create_common_grid([values1, values2], n_grid=n_grid, log_space=True)
    
    dist1 = discretize_distribution(values1, weights1, grid)
    dist2 = discretize_distribution(values2, weights2, grid)
    
    distance = compute_wasserstein_distance(
        grid, dist1,
        grid, dist2,
        metric='log_l1',
        method='emd'
    )
    
    return distance, file1, file2, len(values1), len(values2)


def load_files_from_list(list_file):
    """Load TSV file paths from a list file using first token of each non-empty line."""
    list_path = Path(list_file)
    if not list_path.exists():
        raise FileNotFoundError(f"File list not found: {list_file}")

    entries = []
    with open(list_path, 'r', encoding='utf-8') as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            first_token = line.split()[0]
            file_path = Path(first_token).expanduser()
            if not file_path.is_absolute():
                file_path = list_path.parent / file_path

            if not file_path.exists():
                raise FileNotFoundError(
                    f"Listed file not found at line {line_number}: {first_token}"
                )

            entries.append((first_token, str(file_path)))

    if len(entries) < 2:
        raise ValueError("Need at least 2 files in list for pairwise comparison")

    return entries


def compute_distance_all_pairs(file_list, freq_column="pgen", weights_column="duplicate_frequency_percent", n_grid=200, productive_filter=False, vdj_filter=False):
    """Compute distances for all pairs from file list (upper triangle of distance matrix)."""
    file_entries = load_files_from_list(file_list)

    # Pre-load all distributions
    distributions = []
    for label, file_path in file_entries:
        values, weights = load_distribution(
            file_path,
            freq_column=freq_column,
            weights_column=weights_column,
            productive_filter=productive_filter,
            vdj_filter=vdj_filter
        )
        distributions.append((label, values, weights))

    all_values = [values for _, values, _ in distributions]
    grid = create_common_grid(all_values, n_grid=n_grid, log_space=True)

    results = []

    # Compute upper triangle (i < j)
    for left_index, right_index in combinations(range(len(distributions)), 2):
        file1, values1, weights1 = distributions[left_index]
        file2, values2, weights2 = distributions[right_index]

        dist1 = discretize_distribution(values1, weights1, grid)
        dist2 = discretize_distribution(values2, weights2, grid)

        distance = compute_wasserstein_distance(
            grid, dist1,
            grid, dist2,
            metric='log_l1',
            method='emd'
        )

        results.append((file1, file2, distance))

    return results


def print_results_normal(results, title="PAIRWISE WASSERSTEIN DISTANCES", statistics_only=False):
    """Print results in normal mode with table and statistics."""
    print("=" * 100)
    print(title)
    print("=" * 100)
    
    distances = []
    if not statistics_only:
        print(f"{'File 1':<45} {'File 2':<45} {'Distance':>8}")
        print("-" * 100)
        for file1, file2, distance in results:
            print(f"{file1:<45} {file2:<45} {distance:>8.6e}")
            distances.append(distance)
    else:
        # Statistics only: just collect distances
        distances = [distance for _, _, distance in results]
    
    print("=" * 100)
    print("STATISTICS")
    print("=" * 100)
    distances = np.array(distances)
    print(f"Count:        {len(distances)}")
    print(f"Mean:         {np.mean(distances):.6e}")
    print(f"Median:       {np.median(distances):.6e}")
    print(f"Std:          {np.std(distances):.6e}")
    print(f"Min:          {np.min(distances):.6e} ({results[np.argmin(distances)][0]} ↔ {results[np.argmin(distances)][1]})")
    print(f"Max:          {np.max(distances):.6e} ({results[np.argmax(distances)][0]} ↔ {results[np.argmax(distances)][1]})")
    print(f"Q1 (25%):     {np.percentile(distances, 25):.6e}")
    print(f"Q3 (75%):     {np.percentile(distances, 75):.6e}")
    print("=" * 100)


def print_results_pipeline(results):
    """Print results in pipeline mode - only distances (upper triangle order)."""
    for file1, file2, distance in results:
        print(f"{distance:.10e}")


def main():
    """Main function."""
    # Determine help condition more flexibly
    if len(sys.argv) < 2 or (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        print("Usage: python olga-p2p-ot.py [file1.tsv] [file2.tsv] [options]")
        print("\nModes:")
        print("  Two files:        python olga-p2p-ot.py <file1.tsv> <file2.tsv>")
        print("                    → Distance between two specific files")
        print()
        print("  All-pairs:        python olga-p2p-ot.py <files_list.txt> --all")
        print("                    → All pairwise distances (upper triangle) from file list")
        print("                    → In list file, only first token per line is used as filename")
        print()
        print("Parameters:")
        print("  --freq-column <col>    : Column index or name for frequencies (default: pgen)")
        print("  --weights-column <col> : Column index or name for weights, or 'off' (default: duplicate_frequency_percent)")
        print("  --n-grid <n>           : Number of grid points (default: 200)")
        print("  --all                  : Enable all-pairs mode from file list")
        print("  --pipeline             : Output only distances, one per line (for scripting)")
        print("  --statistics-only      : Enable all-pairs mode and show only statistics")
        print("  --productive-filter    : Filter only productive sequences (if productive column exists)")
        print("  --vdj-filter           : Require non-empty v_call/d_call/j_call for existing columns")
        print()
        print("Examples:")
        print("  python olga-p2p-ot.py input/test-cloud-Tumeh2014/Patient01.tsv input/test-cloud-Tumeh2014/Patient02.tsv")
        print("  python olga-p2p-ot.py input/samples-list-2-formats.txt --all")
        print("  python olga-p2p-ot.py input/samples-list-2-formats.txt --all --statistics-only")
        print("  python olga-p2p-ot.py input/samples-list-2-formats.txt --all --pipeline")
        sys.exit(1 if len(sys.argv) < 2 else 0)
    
    freq_column = "pgen"
    weights_column = "duplicate_frequency_percent"
    n_grid = 200
    pipeline_mode = False
    all_mode = False
    statistics_only = False
    productive_filter = False
    vdj_filter = False
    positional_args = []
    
    # Parse arguments
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == "--freq-column" and i + 1 < len(sys.argv):
            freq_column = sys.argv[i + 1]
            i += 2
        elif arg == "--weights-column" and i + 1 < len(sys.argv):
            weights_column = sys.argv[i + 1]
            i += 2
        elif arg == "--n-grid" and i + 1 < len(sys.argv):
            try:
                n_grid = int(sys.argv[i + 1])
                if n_grid <= 1:
                    print("Error: --n-grid must be > 1")
                    sys.exit(1)
            except ValueError:
                print(f"Error: --n-grid must be an integer")
                sys.exit(1)
            i += 2
        elif arg == "--pipeline":
            pipeline_mode = True
            i += 1
        elif arg == "--all":
            all_mode = True
            i += 1
        elif arg == "--statistics-only":
            statistics_only = True
            all_mode = True
            i += 1
        elif arg == "--productive-filter":
            productive_filter = True
            i += 1
        elif arg == "--vdj-filter":
            vdj_filter = True
            i += 1
        elif arg.startswith("--"):
            print(f"Error: Unknown argument '{arg}'")
            sys.exit(1)
        else:
            positional_args.append(arg)
            i += 1
    
    try:
        # Determine mode and compute
        if all_mode:
            if len(positional_args) != 1:
                print("Error: All-pairs mode requires exactly one file list argument")
                print("       Example: python olga-p2p-ot.py input/samples-list.txt --all")
                sys.exit(1)

            files_list = positional_args[0]
            if not pipeline_mode:
                print(f"Computing all-pairs distances from file list: {files_list}")
                print()
            results = compute_distance_all_pairs(files_list, freq_column, weights_column, n_grid, productive_filter, vdj_filter)
            if not pipeline_mode:
                if statistics_only:
                    print_results_normal(results, "ALL PAIRWISE WASSERSTEIN DISTANCES - STATISTICS", statistics_only=True)
                else:
                    print_results_normal(results, "ALL PAIRWISE WASSERSTEIN DISTANCES")
            else:
                print_results_pipeline(results)
        else:
            # Single pair mode
            if len(positional_args) != 2:
                print("Error: Single-pair mode requires exactly two TSV files")
                print("       Example: python olga-p2p-ot.py file1.tsv file2.tsv")
                sys.exit(1)

            file1, file2 = positional_args
            if not file1.endswith('.tsv') or not file2.endswith('.tsv'):
                print("Error: Single-pair mode requires two .tsv files")
                sys.exit(1)
            
            if not pipeline_mode:
                print(f"Computing distance between:")
                print(f"  File 1: {file1}")
                print(f"  File 2: {file2}")
                print()
            
            distance, f1, f2, n_rows1, n_rows2 = compute_distance_single_pair(
                file1, file2,
                freq_column, weights_column, n_grid,
                productive_filter,
                vdj_filter
            )
            
            if pipeline_mode:
                print(f"{distance:.10e}")
            else:
                print("=" * 60)
                print("WASSERSTEIN DISTANCE")
                print("=" * 60)
                print(f"{file1} ↔ {file2}")
                print("Rows after filtering:")
                print(f"  {file1}: {n_rows1}")
                print(f"  {file2}: {n_rows2}")
                print(f"Distance: {distance:.10e}")
                print("=" * 60)
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
