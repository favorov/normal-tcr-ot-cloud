#!/usr/bin/env python3
"""
Compute p-values for sample distributions relative to a barycenter.
For each sample, compute distance to barycenter and assess significance
using a null hypothesis model fitted to normal samples.
"""

import sys
import os
from pathlib import Path
import numpy as np
from scipy import stats
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
        List of sample file paths.
    output_folder : Path
        Folder to use for output.
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


def _compute_distances_to_barycenter(files, grid, barycenter_weights, freq_column, weights_column, productive_filter):
    """
    Compute distances from multiple samples to barycenter.
    
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
    productive_filter : bool
        Filter only productive sequences
        
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
            weights_column=weights_column,
            productive_filter=productive_filter
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


# ============================================================================
# P-value correction for multiple testing
# ============================================================================

def compute_bonferroni_adjusted_pvalues(pvalues):
    """
    Compute Bonferroni-adjusted p-values for multiple testing correction.
    
    This corrects for multiple testing to control Family-Wise Error Rate (FWER).
    Simple and conservative: each p-value is multiplied by the number of tests.
    
    Parameters
    ----------
    pvalues : np.ndarray or list
        Raw p-values from individual tests
        
    Returns
    -------
    adjusted_pvalues : np.ndarray
        Bonferroni-adjusted p-values (same order as input)
    """
    pvalues = np.asarray(pvalues)
    n = len(pvalues)
    
    # Bonferroni correction: multiply by number of tests
    adjusted = pvalues * n
    
    # Clip to [0, 1]
    adjusted = np.minimum(adjusted, 1.0)
    
    return adjusted


# ============================================================================
# Null Hypothesis Model Interface
# ============================================================================
# This section is carefully encapsulated so that different models can be
# easily substituted. Replace fit_null_hypothesis() and compute_pvalue()
# to test alternative statistical models.
# ============================================================================

def fit_null_hypothesis(distances):
    """
    Fit a null hypothesis model to normal sample distances.
    
    Currently uses: Normal distribution (Gaussian)
    
    Alternative models to try:
    - Beta distribution (if 0 < distances < 1)
    - Gamma distribution (for positive skew)
    - Kernel density estimation (non-parametric)
    - Permutation-based empirical distribution
    
    Parameters
    ----------
    distances : np.ndarray
        1D array of distances from normal samples to barycenter
        
    Returns
    -------
    model : dict
        Model parameters (structure depends on model, but must be usable by compute_pvalue)
    """
    # Current model: Normal distribution
    mean = np.mean(distances)
    std = np.std(distances, ddof=1)  # Use sample std
    
    return {
        'model_type': 'normal',
        'mean': mean,
        'std': std,
        'description': f"Normal(μ={mean:.4f}, σ={std:.4f})"
    }


def compute_pvalue(distance, model):
    """
    Compute p-value for a single distance under the null hypothesis.
    
    The p-value is the probability of observing a distance at least as extreme
    as the given one, under the null hypothesis model.
    
    Parameters
    ----------
    distance : float
        Observed distance from sample to barycenter
    model : dict
        Fitted model (from fit_null_hypothesis)
        
    Returns
    -------
    pvalue : float
        Two-tailed p-value (probability mass in both tails)
    """
    if model['model_type'] == 'normal':
        # Normal distribution: two-tailed test
        # p-value = P(|X| >= |observed|) where X ~ N(μ, σ)
        mean = model['mean']
        std = model['std']
        
        if std == 0:
            # Degenerate case: all distances are identical
            return 1.0 if distance == mean else 0.0
        
        # Standardize
        z_score = (distance - mean) / std
        # Two-tailed p-value
        pvalue = 2 * (1 - stats.norm.cdf(abs(z_score)))
        return pvalue
    
    else:
        raise ValueError(f"Unknown model type: {model['model_type']}")


# ============================================================================
# Main script
# ============================================================================

def main():
    """Main function."""
    if len(sys.argv) < 3 or sys.argv[1] in ["-h", "--help"]:
        print("Usage: python olga-samples-p2b-pval.py <barycenter_folder> <samples_folder> [options]")
        print("\nParameters:")
        print("  barycenter_folder     : Folder containing TSV files and barycenter.npz")
        print("  samples               : Either:")
        print("                          - Folder with TSV files to evaluate")
        print("                          - Text file with one TSV file path per line")
        print("  --freq-column <col>   : Column index or name for frequencies (default: pgen)")
        print("  --weights-column <col>: Column index or name for weights, or 'off' (default: duplicate_frequency_percent)")
        print("  --barycenter <file>   : Barycenter file (default: barycenter.npz)")
        print("  --productive-filter   : Filter only productive sequences (default: off)")
        print("\nOutput:")
        print("  Table with sample names, distances, and p-values")
        print("  Both raw and Bonferroni-adjusted p-values")
        print("  Results sorted by Bonferroni-adjusted p-value (most significant first)")
        print("\nExamples:")
        print("  python olga-samples-p2b-pval.py input/test-cloud-Tumeh2014 input/new-samples")
        print("  python olga-samples-p2b-pval.py input/test-cloud-Tumeh2014 samples_list.txt \\")
        print("    --weights-column duplicate_frequency_percent")
        sys.exit(1 if len(sys.argv) < 3 else 0)

    barycenter_folder = Path(sys.argv[1])
    samples_path = Path(sys.argv[2])

    freq_column = "pgen"
    weights_column = "duplicate_frequency_percent"
    barycenter_file = "barycenter.npz"
    productive_filter = False

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
        elif arg == "--productive-filter":
            productive_filter = True
            i += 1
        else:
            i += 1

    # Load barycenter
    barycenter_path = _resolve_barycenter_path(barycenter_folder, barycenter_file)
    print(f"Loading barycenter from {barycenter_path}")
    grid, barycenter_weights = load_barycenter(str(barycenter_path))

    # Get TSV files
    barycenter_files = sorted(barycenter_folder.glob("*.tsv"))
    samples_files, _, custom_labels = _load_sample_files(samples_path)

    if not barycenter_files:
        print(f"Error: No TSV files found in {barycenter_folder}")
        sys.exit(1)
    if not samples_files:
        print(f"Error: No sample TSV files found")
        sys.exit(1)

    print(f"Found {len(barycenter_files)} barycenter files, {len(samples_files)} sample files")

    # Compute distances for barycenter files (normal samples)
    print("Computing distances for normal samples (barycenter files)...")
    barycenter_distances, extended_grid, extended_barycenter = _compute_distances_to_barycenter(
        barycenter_files, grid, barycenter_weights,
        freq_column, weights_column, productive_filter
    )

    # Fit null hypothesis model
    print("Fitting null hypothesis model...")
    model = fit_null_hypothesis(barycenter_distances)
    print(f"  Model: {model['description']}")
    print()

    # Compute distances and p-values for sample files
    print("Computing distances and p-values for sample files...")
    sample_distances, _, _ = _compute_distances_to_barycenter(
        samples_files, extended_grid, extended_barycenter,
        freq_column, weights_column, productive_filter
    )

    # Compute p-values
    results = []
    for sample_file, distance in zip(samples_files, sample_distances):
        pvalue = compute_pvalue(distance, model)
        # Use custom label if provided, otherwise auto-generate
        label = custom_labels.get(sample_file, _label_from_filename(sample_file))
        results.append({
            'filename': str(sample_file),
            'sample': label,
            'distance': distance,
            'pvalue': pvalue
        })

    # Compute Bonferroni-adjusted p-values
    raw_pvalues = [r['pvalue'] for r in results]
    adjusted_pvalues = compute_bonferroni_adjusted_pvalues(raw_pvalues)
    for r, adj_p in zip(results, adjusted_pvalues):
        r['pvalue_adjusted'] = adj_p

    # Sort by adjusted p-value
    results = sorted(results, key=lambda x: x['pvalue_adjusted'])

    # Print table
    print()
    print("=" * 115)
    print(f"{'Label':<8} {'Filename':<50} {'Distance':>11} {'P-value':>12} {'Bonf. p':>11}")
    print("=" * 115)
    for row in results:
        print(f"{row['sample']:<8} {row['filename']:<50} {row['distance']:>11.6f} {row['pvalue']:>12.6e} {row['pvalue_adjusted']:>11.6e}")
    print("=" * 115)
    print()

    # Print summary statistics
    pvalues_raw = [r['pvalue'] for r in results]
    pvalues_adj = [r['pvalue_adjusted'] for r in results]
    
    print(f"Summary:")
    print(f"  Total samples: {len(results)}")
    print(f"  Number of tests (for Bonferroni correction): {len(results)}")
    print()
    print(f"  Raw p-values:")
    print(f"    Range: [{min(pvalues_raw):.6e}, {max(pvalues_raw):.6e}]")
    print(f"    Significant (p < 0.05): {sum(1 for p in pvalues_raw if p < 0.05)}")
    print(f"    Significant (p < 0.01): {sum(1 for p in pvalues_raw if p < 0.01)}")
    print()
    print(f"  Bonferroni-adjusted p-values (FWER control):")
    print(f"    Range: [{min(pvalues_adj):.6e}, {max(pvalues_adj):.6e}]")
    print(f"    Significant (p_adj < 0.05): {sum(1 for p in pvalues_adj if p < 0.05)}")
    print(f"    Significant (p_adj < 0.01): {sum(1 for p in pvalues_adj if p < 0.01)}")
    print()


if __name__ == "__main__":
    main()
