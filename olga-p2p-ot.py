#!/usr/bin/env python3
"""
Calculate Wasserstein distances between TCR distributions.
Supports single pair, one-to-all, and all-pairs comparisons.
"""

import sys
import os
import numpy as np
from pathlib import Path
from itertools import combinations
from ot_utils import (
    load_distribution,
    compute_wasserstein_distance,
    discretize_distribution,
    create_common_grid,
    load_barycenter,
    extend_grid_if_needed
)


def compute_distance_single_pair(input_folder, file1, file2, freq_column, weights_column, n_grid, use_barycenter_grid=False, barycenter_file="barycenter.npz"):
    """Compute distance between two specific files."""
    filepath1 = Path(input_folder) / file1
    filepath2 = Path(input_folder) / file2
    
    values1, weights1 = load_distribution(str(filepath1), freq_column, weights_column)
    values2, weights2 = load_distribution(str(filepath2), freq_column, weights_column)
    
    # Use barycenter grid if available for consistent comparison
    if use_barycenter_grid:
        # Determine barycenter path
        if os.path.isabs(barycenter_file) or barycenter_file.startswith('~'):
            barycenter_path = Path(os.path.expanduser(barycenter_file))
        else:
            barycenter_path = Path(input_folder) / barycenter_file
        
        if barycenter_path.exists():
            grid, _ = load_barycenter(str(barycenter_path))
            # Extend grid if data falls outside barycenter range
            all_values = np.concatenate([values1, values2])
            grid, _ = extend_grid_if_needed(
                grid, np.zeros(len(grid)),
                all_values.min(), all_values.max()
            )
        else:
            grid = create_common_grid([values1, values2], n_grid=n_grid, log_space=True)
    else:
        grid = create_common_grid([values1, values2], n_grid=n_grid, log_space=True)
    
    dist1 = discretize_distribution(values1, weights1, grid)
    dist2 = discretize_distribution(values2, weights2, grid)
    
    distance = compute_wasserstein_distance(
        grid, dist1,
        grid, dist2,
        metric='log_l1',
        method='emd'
    )
    
    return distance, file1, file2


def compute_distance_one_to_all(input_folder, ref_file, freq_column, weights_column, n_grid, use_barycenter_grid=False, barycenter_file="barycenter.npz"):
    """Compute distances from one file to all others."""
    input_path = Path(input_folder)
    all_files = sorted(input_path.glob("*.tsv"))
    
    if not any(f.name == ref_file for f in all_files):
        raise FileNotFoundError(f"Reference file not found: {ref_file}")
    
    # Load reference file once
    ref_path = input_path / ref_file
    ref_values, ref_weights = load_distribution(str(ref_path), freq_column, weights_column)
    
    # Determine grid
    if use_barycenter_grid:
        # Determine barycenter path
        if os.path.isabs(barycenter_file) or barycenter_file.startswith('~'):
            barycenter_path = Path(os.path.expanduser(barycenter_file))
        else:
            barycenter_path = input_path / barycenter_file
        
        if barycenter_path.exists():
            grid, _ = load_barycenter(str(barycenter_path))
            # Load all values to determine range for grid extension
            all_values = [ref_values] + [load_distribution(str(f), freq_column, weights_column)[0] for f in all_files if f.name != ref_file]
            all_values_combined = np.concatenate(all_values)
            # Extend grid if data falls outside barycenter range
            grid, _ = extend_grid_if_needed(
                grid, np.zeros(len(grid)),
                all_values_combined.min(), all_values_combined.max()
            )
        else:
            # Create grid from reference and all other files
            all_values = [ref_values] + [load_distribution(str(f), freq_column, weights_column)[0] for f in all_files if f.name != ref_file]
            grid = create_common_grid(all_values, n_grid=n_grid, log_space=True)
    else:
        # Create common grid from reference and all others
        all_values = [ref_values] + [load_distribution(str(f), freq_column, weights_column)[0] for f in all_files if f.name != ref_file]
        grid = create_common_grid(all_values, n_grid=n_grid, log_space=True)
    
    results = []
    
    for other_file in all_files:
        if other_file.name == ref_file:
            continue
        
        other_path = input_path / other_file.name
        other_values, other_weights = load_distribution(str(other_path), freq_column, weights_column)
        
        dist_ref = discretize_distribution(ref_values, ref_weights, grid)
        dist_other = discretize_distribution(other_values, other_weights, grid)
        
        distance = compute_wasserstein_distance(
            grid, dist_ref,
            grid, dist_other,
            metric='log_l1',
            method='emd'
        )
        
        results.append((ref_file, other_file.name, distance))
    
    return results


def compute_distance_all_pairs(input_folder, freq_column, weights_column, n_grid, use_barycenter_grid=False, barycenter_file="barycenter.npz"):
    """Compute distances for all pairs (upper triangle of distance matrix)."""
    input_path = Path(input_folder)
    all_files = sorted(input_path.glob("*.tsv"))
    all_files = [f.name for f in all_files]
    
    if len(all_files) < 2:
        raise ValueError("Need at least 2 TSV files for pairwise comparison")
    
    # Pre-load all distributions
    distributions = {}
    for file in all_files:
        values, weights = load_distribution(
            str(input_path / file),
            freq_column=freq_column,
            weights_column=weights_column
        )
        distributions[file] = (values, weights)
    
    # Determine grid
    if use_barycenter_grid:
        # Determine barycenter path
        if os.path.isabs(barycenter_file) or barycenter_file.startswith('~'):
            barycenter_path = Path(os.path.expanduser(barycenter_file))
        else:
            barycenter_path = input_path / barycenter_file
        
        if barycenter_path.exists():
            grid, _ = load_barycenter(str(barycenter_path))
            # Find global range from all distributions
            all_values = [v for v, w in distributions.values()]
            all_values_combined = np.concatenate(all_values)
            # Extend grid if data falls outside barycenter range
            grid, _ = extend_grid_if_needed(
                grid, np.zeros(len(grid)),
                all_values_combined.min(), all_values_combined.max()
            )
        else:
            all_values = [v for v, w in distributions.values()]
            grid = create_common_grid(all_values, n_grid=n_grid, log_space=True)
    else:
        all_values = [v for v, w in distributions.values()]
        grid = create_common_grid(all_values, n_grid=n_grid, log_space=True)
    
    results = []
    
    # Compute upper triangle (i < j)
    for file1, file2 in combinations(all_files, 2):
        values1, weights1 = distributions[file1]
        values2, weights2 = distributions[file2]
        
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
        print("Usage: python olga-p2p-ot.py <input_folder> [file1] [file2] [options]")
        print("\nModes:")
        print("  Two files:        python olga-p2p-ot.py <folder> <file1.tsv> <file2.tsv>")
        print("                    → Distance between two specific files")
        print()
        print("  One-to-all:       python olga-p2p-ot.py <folder> <file.tsv> --all")
        print("                    → Distances from one file to all others")
        print()
        print("  All-pairs:        python olga-p2p-ot.py <folder> --all")
        print("                    → All pairwise distances (upper triangle)")
        print()
        print("Parameters:")
        print("  --freq-column <col>    : Column index or name for frequencies (default: pgen)")
        print("  --weights-column <col> : Column index or name for weights, or 'off' (default: off)")
        print("  --n-grid <n>           : Number of grid points (default: 200)")
        print("  --all                  : Enable batch mode (one-to-all or all-pairs)")
        print("  --pipeline             : Output only distances, one per line (for scripting)")
        print("  --statistics-only      : Enable batch mode and show only statistics")
        print("  --barycenter <file>    : Use barycenter grid from file for consistent comparison with p2b (default: barycenter.npz)")
        print()
        print("Examples:")
        print("  python olga-p2p-ot.py input/test-cloud-Tumeh2014 Patient01.tsv Patient02.tsv")
        print("  python olga-p2p-ot.py input/test-cloud-Tumeh2014 Patient01.tsv --all")
        print("  python olga-p2p-ot.py input/test-cloud-Tumeh2014 --all")
        print("  python olga-p2p-ot.py input/test-cloud-Tumeh2014 --all --pipeline")
        sys.exit(1 if len(sys.argv) < 2 else 0)
    
    input_folder = sys.argv[1]
    freq_column = "pgen"
    weights_column = "off"
    n_grid = 200
    pipeline_mode = False
    all_mode = False
    statistics_only = False
    use_barycenter_grid = False
    barycenter_file = "barycenter.npz"
    file1 = None
    file2 = None
    
    # Parse arguments
    i = 2
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
        elif arg == "--barycenter":
            if i + 1 < len(sys.argv):
                barycenter_file = sys.argv[i + 1]
                use_barycenter_grid = True
                i += 2
            else:
                print("Error: --barycenter requires a filename argument")
                sys.exit(1)
        elif arg.endswith('.tsv') and file1 is None:
            file1 = arg
            i += 1
        elif arg.endswith('.tsv') and file2 is None:
            file2 = arg
            i += 1
        else:
            print(f"Error: Unknown argument '{arg}'")
            sys.exit(1)
    
    try:
        # Determine mode and compute
        if all_mode:
            if file1 is not None:
                # One-to-all mode
                if not pipeline_mode:
                    print(f"Loading reference file: {file1}")
                    print()
                results = compute_distance_one_to_all(input_folder, file1, freq_column, weights_column, n_grid, use_barycenter_grid, barycenter_file)
                if not pipeline_mode:
                    if statistics_only:
                        print_results_normal(results, f"STATISTICS FROM {file1} TO ALL OTHERS", statistics_only=True)
                    else:
                        print_results_normal(results, f"DISTANCES FROM {file1} TO ALL OTHERS")
                else:
                    print_results_pipeline(results)
            else:
                # All-pairs mode
                if not pipeline_mode:
                    print(f"Computing all-pairs distances...")
                    print()
                results = compute_distance_all_pairs(input_folder, freq_column, weights_column, n_grid, use_barycenter_grid, barycenter_file)
                if not pipeline_mode:
                    if statistics_only:
                        print_results_normal(results, "ALL PAIRWISE WASSERSTEIN DISTANCES - STATISTICS", statistics_only=True)
                    else:
                        print_results_normal(results, "ALL PAIRWISE WASSERSTEIN DISTANCES")
                else:
                    print_results_pipeline(results)
        else:
            # Single pair mode
            if file1 is None or file2 is None:
                print("Error: Two files required for single comparison, or use --all for batch mode")
                sys.exit(1)
            
            if not pipeline_mode:
                print(f"Computing distance between:")
                print(f"  File 1: {file1}")
                print(f"  File 2: {file2}")
                print()
            
            distance, f1, f2 = compute_distance_single_pair(
                input_folder, file1, file2,
                freq_column, weights_column, n_grid, use_barycenter_grid, barycenter_file
            )
            
            if pipeline_mode:
                print(f"{distance:.10e}")
            else:
                print("=" * 60)
                print("WASSERSTEIN DISTANCE")
                print("=" * 60)
                print(f"{file1} ↔ {file2}")
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
