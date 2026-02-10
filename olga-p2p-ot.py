#!/usr/bin/env python3
"""
Calculate Wasserstein distance between two distributions from TSV files.
"""

import sys
import pandas as pd
from scipy.stats import wasserstein_distance


def is_no_weights(value):
    """Check if the weights column should be disabled."""
    if isinstance(value, str):
        return value.lower() in ["no", "off", "none", "disabled"]
    return False


def get_column_index(df, column_param):
    """
    Get column index from either a number or column name.
    
    Parameters:
    -----------
    df : DataFrame
        The pandas DataFrame
    column_param : str or int
        Either a column index (string representation of number) or column name
    
    Returns:
    --------
    int: Column index
    """
    # Try to interpret as a number first
    try:
        col_idx = int(column_param)
        if 0 <= col_idx < len(df.columns):
            return col_idx
    except (ValueError, TypeError):
        pass
    
    # Try to find by column name
    if column_param in df.columns:
        return df.columns.get_loc(column_param)
    
    # If not found, raise an error
    raise ValueError(f"Column '{column_param}' not found. Available columns: {list(df.columns)}")


def load_and_prepare_distribution(filepath, freq_column, weights_column):
    """
    Load TSV file and extract sample values and their weights.
    
    Parameters:
    -----------
    filepath : str
        Path to the TSV file
    freq_column : str or int
        Column index or name for sample values (pgen probabilities)
    weights_column : str or int
        Column index or name for weights, or "NO"/"off" to disable weights
    
    Returns:
    --------
    tuple: (sample_values, weights)
        sample_values: The pgen probabilities to compare
        weights: The weights for each sample (or None for uniform weighting)
    """
    df = pd.read_csv(filepath, sep='\t')
    
    # Get sample values (pgen column)
    freq_idx = get_column_index(df, freq_column)
    sample_values = df.iloc[:, freq_idx].values.astype(float)
    
    # Check if we should use weights
    use_weights = not is_no_weights(weights_column)
    
    if use_weights:
        try:
            weights_idx = get_column_index(df, weights_column)
            weights = df.iloc[:, weights_idx].values.astype(float)
        except (ValueError, IndexError) as e:
            print(f"Warning: {e}. Using uniform weights (all 1.0).")
            weights = None
    else:
        weights = None
    
    return sample_values, weights


def main():
    """Main function."""
    if len(sys.argv) < 5:
        print("Usage: python olga-p2p-ot.py <input_folder> <file1> <file2> <freq_column> <weights_column>")
        print("\nParameters:")
        print("  input_folder    : Path to folder containing TSV files")
        print("  file1           : Name of first TSV file")
        print("  file2           : Name of second TSV file")
        print("  freq_column     : Column index (0-based) or column name for frequencies")
        print("  weights_column  : Column index (0-based) or column name for weights,")
        print("                    or 'NO'/'off' to disable weights")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    file1 = sys.argv[2]
    file2 = sys.argv[3]
    freq_column = sys.argv[4]  # Keep as string, get_column_index handles both int and str
    weights_column = sys.argv[5]
    
    # Construct full file paths
    filepath1 = f"{input_folder}/{file1}"
    filepath2 = f"{input_folder}/{file2}"
    
    print(f"Loading distributions...")
    print(f"  File 1: {filepath1}")
    print(f"  File 2: {filepath2}")
    print(f"  Frequency column: {freq_column}")
    print(f"  Weights column: {weights_column}")
    print()
    
    try:
        # Load data from both files
        values1, weights1 = load_and_prepare_distribution(filepath1, freq_column, weights_column)
        values2, weights2 = load_and_prepare_distribution(filepath2, freq_column, weights_column)
        
        # Calculate Wasserstein distance between the two weighted distributions
        wd = wasserstein_distance(values1, values2, u_weights=weights1, v_weights=weights2)
        
        # Display results
        print("=" * 60)
        print("WASSERSTEIN (OPTIMAL TRANSPORT) DISTANCE")
        print("=" * 60)
        print(f"Distance: {wd:.10f}")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
