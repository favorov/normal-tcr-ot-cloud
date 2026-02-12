#!/usr/bin/env python3
"""
Calculate Wasserstein distance between two distributions from TSV files.
Uses centralized OT utilities for consistent distance computation.
"""

import sys
import numpy as np
from pathlib import Path
from ot_utils import (
    load_distribution,
    compute_wasserstein_distance,
    discretize_distribution,
    create_common_grid
)


def main():
    """Main function."""
    if len(sys.argv) < 4:
        print("Usage: python olga-p2p-ot.py <input_folder> <file1> <file2> [--freq-column <col>] [--weights-column <col>] [--n-grid <n>]")
        print("\nParameters:")
        print("  input_folder      : Path to folder containing TSV files")
        print("  file1             : Name of first TSV file")
        print("  file2             : Name of second TSV file")
        print("  --freq-column     : Column index (0-based) or column name for frequencies (default: pgen)")
        print("  --weights-column  : Column index (0-based) or column name for weights, or 'off' (default: off)")
        print("  --n-grid          : Number of grid points (default: 200)")
        print("\nExamples:")
        print("  python olga-p2p-ot.py input/test-cloud-Tumeh2014 Patient01_Base_tcr_pgen.tsv Patient02_Base_tcr_pgen.tsv")
        print("  python olga-p2p-ot.py input/test-cloud-Tumeh2014 Patient01_Base_tcr_pgen.tsv Patient02_Base_tcr_pgen.tsv --freq-column pgen --weights-column duplicate_frequency_percent")
        print("  python olga-p2p-ot.py input/test-cloud-Tumeh2014 Patient01_Base_tcr_pgen.tsv Patient02_Base_tcr_pgen.tsv --n-grid 500")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    file1 = sys.argv[2]
    file2 = sys.argv[3]
    freq_column = "pgen"
    weights_column = "off"
    n_grid = 200
    
    # Parse named arguments
    i = 4
    while i < len(sys.argv):
        if sys.argv[i] == "--freq-column" and i + 1 < len(sys.argv):
            freq_column = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--weights-column" and i + 1 < len(sys.argv):
            weights_column = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--n-grid" and i + 1 < len(sys.argv):
            try:
                n_grid = int(sys.argv[i + 1])
            except ValueError:
                print(f"Error: --n-grid must be an integer, got '{sys.argv[i + 1]}'")
                sys.exit(1)
            if n_grid <= 1:
                print("Error: --n-grid must be > 1")
                sys.exit(1)
            i += 2
        else:
            print(f"Error: Unknown argument '{sys.argv[i]}'")
            sys.exit(1)
    
    # Construct full file paths
    filepath1 = Path(input_folder) / file1
    filepath2 = Path(input_folder) / file2
    
    print(f"Loading distributions...")
    print(f"  File 1: {filepath1}")
    print(f"  File 2: {filepath2}")
    print(f"  Frequency column: {freq_column}")
    print(f"  Weights column: {weights_column}")
    print()
    
    try:
        # Load distributions using centralized utility
        values1, weights1 = load_distribution(str(filepath1), freq_column, weights_column)
        values2, weights2 = load_distribution(str(filepath2), freq_column, weights_column)
        
        print(f"  Loaded {len(values1)} samples from file 1")
        print(f"  Loaded {len(values2)} samples from file 2")
        
        # Create common grid using centralized utility
        grid = create_common_grid([values1, values2], n_grid=n_grid, log_space=True)
        
        print(f"  Created log-spaced grid with {n_grid} points")
        print(f"  Range: [{grid.min():.3e}, {grid.max():.3e}]")
        print()
        
        # Discretize both distributions onto the grid
        dist1 = discretize_distribution(values1, weights1, grid)
        dist2 = discretize_distribution(values2, weights2, grid)
        
        # Compute Wasserstein distance using centralized utility
        # This ensures consistent distance computation across all scripts
        wd = compute_wasserstein_distance(
            grid, dist1, 
            grid, dist2,
            metric='log_l1',  # L1 distance in log space (robust for pgen)
            method='emd'      # Exact EMD solver
        )
        
        # Display results
        print("=" * 60)
        print("WASSERSTEIN (OPTIMAL TRANSPORT) DISTANCE")
        print("=" * 60)
        print(f"Distance: {wd:.10e}")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
