#!/usr/bin/env python3
"""
Calculate Wasserstein distance from a distribution to the barycenter.
Can compute for a single file or all files in batch mode.
"""

import sys
import numpy as np
from pathlib import Path
from ot_utils import (
    load_distribution,
    load_barycenter,
    compute_wasserstein_distance,
    discretize_distribution,
    extend_grid_if_needed
)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python olga-p2b-ot.py <input_folder> [file.tsv] [options]")
        print("\nParameters:")
        print("  input_folder         : Path to folder containing TSV files and barycenter.npz")
        print("  file.tsv             : (Optional) Specific TSV file to compare. If omitted, processes all .tsv files")
        print("  --freq-column <col>  : Column index or name for frequencies (default: pgen)")
        print("  --weights-column <col> : Column index or name for weights, or 'off' (default: off)")
        print("  --barycenter <file>  : Custom barycenter file (default: barycenter.npz)")
        print("  --all                : Explicitly process all files (same as providing no file)")
        print("  --pipeline           : Output only distance value(s) (for use in scripts/pipelines)")
        print("  --statistics-only    : Enable batch mode and show only statistics")
        print("\nExamples:")
        print("  # Single file")
        print("  python olga-p2b-ot.py input/test-cloud-Tumeh2014 Patient01_Base_tcr_pgen.tsv")
        print()
        print("  # All files (batch mode)")
        print("  python olga-p2b-ot.py input/test-cloud-Tumeh2014")
        print("  python olga-p2b-ot.py input/test-cloud-Tumeh2014 --all")
        print()
        print("  # Custom barycenter")
        print("  python olga-p2b-ot.py input/test-cloud-Tumeh2014 Patient01_Base_tcr_pgen.tsv --barycenter my_barycenter.npz")
        print()
        print("  # Pipeline mode (only distance output)")
        print("  python olga-p2b-ot.py input/test-cloud-Tumeh2014 Patient01_Base_tcr_pgen.tsv --pipeline")
        sys.exit(1)
    
    input_folder = Path(sys.argv[1])
    
    # Defaults
    freq_column = "pgen"
    weights_column = "off"
    barycenter_file = "barycenter.npz"
    single_file = None
    batch_mode = False
    pipeline_mode = False
    statistics_only = False
    
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
        elif arg == "--barycenter" and i + 1 < len(sys.argv):
            barycenter_file = sys.argv[i + 1]
            i += 2
        elif arg == "--all":
            batch_mode = True
            i += 1
        elif arg == "--pipeline":
            pipeline_mode = True
            i += 1
        elif arg == "--statistics-only":
            statistics_only = True
            batch_mode = True
            i += 1
        elif arg.endswith('.tsv') and single_file is None:
            single_file = arg
            i += 1
        else:
            print(f"Error: Unknown argument or invalid format '{arg}'")
            sys.exit(1)
    
    # Determine mode
    if single_file is None:
        batch_mode = True
    
    # Load barycenter
    barycenter_path = input_folder / barycenter_file
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
    if batch_mode:
        files_to_process = sorted(input_folder.glob("*.tsv"))
        if len(files_to_process) == 0:
            if not pipeline_mode:
                print(f"Error: No TSV files found in {input_folder}")
            sys.exit(1)
        if not pipeline_mode:
            print(f"Batch mode: Processing {len(files_to_process)} file(s)")
            print()
    else:
        file_path = input_folder / single_file
        if not file_path.exists():
            if not pipeline_mode:
                print(f"Error: File not found: {file_path}")
            sys.exit(1)
        files_to_process = [file_path]
        if not pipeline_mode:
            print(f"Single file mode")
            print()
    
    # Process files
    results = []
    
    for file_path in files_to_process:
        try:
            # Load distribution
            values, weights = load_distribution(
                str(file_path),
                freq_column=freq_column,
                weights_column=weights_column
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
                'distance': distance,
                'n_samples': len(values)
            })
            
            if not batch_mode and not pipeline_mode:
                # Single file: detailed output
                print(f"File: {file_path.name}")
                print(f"  Samples: {len(values)}")
                print(f"  Value range: [{values.min():.3e}, {values.max():.3e}]")
                print()
        
        except Exception as e:
            if not pipeline_mode:
                print(f"Error processing {file_path.name}: {e}")
            if not batch_mode:
                sys.exit(1)
            continue
    
    # Display results
    if pipeline_mode:
        # Pipeline mode: output only distance values
        if batch_mode:
            # Batch: one distance per line
            results.sort(key=lambda x: x['distance'])
            for r in results:
                print(f"{r['distance']:.10e}")
        else:
            # Single file: just the distance
            print(f"{results[0]['distance']:.10e}")
    elif batch_mode:
        # Sort by distance
        results.sort(key=lambda x: x['distance'])
        
        print("=" * 80)
        print("WASSERSTEIN DISTANCES TO BARYCENTER (sorted by distance)")
        print("=" * 80)
        
        if not statistics_only:
            print(f"{'File':<45} {'Distance':>15} {'Samples':>10}")
            print("-" * 80)
            for r in results:
                print(f"{r['file']:<45} {r['distance']:>15.6e} {r['n_samples']:>10}")
        
        print("=" * 80)
        print("STATISTICS")
        print("=" * 80)
        
        distances = np.array([r['distance'] for r in results])
        print(f"Count:        {len(distances)}")
        print(f"Mean:         {np.mean(distances):.6e}")
        print(f"Median:       {np.median(distances):.6e}")
        print(f"Std:          {np.std(distances):.6e}")
        print(f"Min:          {np.min(distances):.6e} ({results[0]['file']})")
        print(f"Max:          {np.max(distances):.6e} ({results[-1]['file']})")
        print(f"Q1 (25%):     {np.percentile(distances, 25):.6e}")
        print(f"Q3 (75%):     {np.percentile(distances, 75):.6e}")
        print("=" * 80)
    else:
        # Single file
        print("=" * 60)
        print("WASSERSTEIN DISTANCE TO BARYCENTER")
        print("=" * 60)
        print(f"Distance: {results[0]['distance']:.10e}")
        print("=" * 60)


if __name__ == "__main__":
    main()
