#!/usr/bin/env python3
"""
Compare OT distances to barycenter between two groups:
1) Sample files (provided as folder or list)
2) Cloud files used to build barycenter (TSV files in barycenter folder)

Reports descriptive statistics for both groups and a one-sided
Wilcoxon rank-sum (Mann-Whitney U) p-value testing cloud < sample.
"""

import os
import sys
import numpy as np
from pathlib import Path

try:
    from scipy.stats import mannwhitneyu
except ImportError:
    print("Error: scipy is required. Install with: pip install scipy")
    sys.exit(1)

from ot_utils import (
    _label_from_filename,
    load_distribution,
    load_barycenter,
    compute_wasserstein_distance,
    discretize_distribution,
    extend_grid_if_needed,
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
        with open(samples_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                file_path = Path(os.path.expanduser(parts[0]))
                files.append(file_path)
                if len(parts) > 1:
                    custom_labels[file_path] = parts[1].strip()

        missing = [f for f in files if not f.exists()]
        if missing:
            print(f"Error: The following files from {samples_path} do not exist:")
            for missing_file in missing:
                print(f"  {missing_file}")
            sys.exit(1)
    else:
        print(f"Error: Path does not exist: {samples_path}")
        sys.exit(1)

    return files, custom_labels


def _load_cloud_files(barycenter_folder):
    """Load cloud files from barycenter folder (all TSV files)."""
    files = sorted(barycenter_folder.glob("*.tsv"))
    return files


def _compute_distances(
    file_paths,
    grid,
    barycenter_weights,
    freq_column,
    weights_column,
    productive_filter,
    vdj_filter,
    vj_filter,
    custom_labels=None,
):
    """Compute distance-to-barycenter for each file path."""
    if custom_labels is None:
        custom_labels = {}

    results = []
    for file_path in file_paths:
        try:
            values, weights = load_distribution(
                str(file_path),
                freq_column=freq_column,
                weights_column=weights_column,
                productive_filter=productive_filter,
                vdj_filter=vdj_filter,
                vj_filter=vj_filter,
            )

            extended_grid, extended_barycenter = extend_grid_if_needed(
                grid,
                barycenter_weights,
                values.min(),
                values.max(),
            )

            sample_discretized = discretize_distribution(values, weights, extended_grid)

            distance = compute_wasserstein_distance(
                extended_grid,
                sample_discretized,
                extended_grid,
                extended_barycenter,
                metric="log_l1",
                method="emd",
            )

            results.append(
                {
                    "file": file_path.name,
                    "label": custom_labels.get(file_path, _label_from_filename(file_path)),
                    "distance": distance,
                    "n_samples": len(values),
                }
            )
        except ValueError as exc:
            print(f"Error: {exc}")
            sys.exit(1)
        except Exception as exc:
            # Keep processing other files; caller can decide if empty results are fatal.
            print(f"Warning: Error processing {file_path.name}: {exc}")

    return results


def _print_group_table(title, results, statistics_only=False):
    """Print sorted per-file table and descriptive statistics for one group."""
    results = sorted(results, key=lambda x: x["distance"], reverse=True)
    distances = np.array([r["distance"] for r in results])

    print("=" * 100)
    print(title)
    print("=" * 100)

    if not statistics_only:
        print(f"{'Label':<12} {'File':<50} {'Distance':>15} {'Samples':>10}")
        print("-" * 100)
        for r in results:
            print(f"{r['label']:<12} {r['file']:<50} {r['distance']:>15.6e} {r['n_samples']:>10}")

    print("-" * 100)
    print("STATISTICS")
    print("-" * 100)
    print(f"Count:        {len(distances)}")
    print(f"Mean:         {np.mean(distances):.6e}")
    print(f"Median:       {np.median(distances):.6e}")
    print(f"Std:          {np.std(distances):.6e}")
    print(f"Min:          {np.min(distances):.6e} ({results[-1]['file']})")
    print(f"Max:          {np.max(distances):.6e} ({results[0]['file']})")
    print(f"Q1 (25%):     {np.percentile(distances, 25):.6e}")
    print(f"Q3 (75%):     {np.percentile(distances, 75):.6e}")


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python olga-p2p-ot-wilocoxon.py <barycenter_folder> <samples> [options]")
        print("\nParameters:")
        print("  barycenter_folder      : Folder containing cloud TSV files and barycenter.npz")
        print("  samples                : Either folder with TSV files or text file with one TSV path per line")
        print("  --freq-column <col>    : Column index or name for frequencies (default: pgen)")
        print("  --weights-column <col> : Column index or name for weights, or 'off' (default: duplicate_frequency_percent)")
        print("  --barycenter <file>    : Custom barycenter file (default: barycenter.npz)")
        print("  --pipeline             : Output only one-sided p-value (for scripting)")
        print("  --statistics-only      : Show only statistics")
        print("  --productive-filter    : Filter only productive sequences (if productive column exists)")
        print("  --vdj-filter           : Require non-empty v_call/d_call/j_call for existing columns")
        print("  --vj-filter            : Require non-empty v_call/j_call for existing columns")
        print("\nExamples:")
        print("  python olga-p2p-ot-wilocoxon.py input/test-cloud-Tumeh2014 input/new-samples")
        print("  python olga-p2p-ot-wilocoxon.py input/test-cloud-Tumeh2014 input/samples-list-2-formats.txt")
        print("  python olga-p2p-ot-wilocoxon.py input/test-cloud-Tumeh2014 input/new-samples --pipeline")
        sys.exit(1)

    barycenter_folder = Path(sys.argv[1]).expanduser()
    samples_path = Path(sys.argv[2]).expanduser()

    # Defaults (mirrors olga-p2b-ot.py)
    freq_column = "pgen"
    weights_column = "duplicate_frequency_percent"
    barycenter_file = "barycenter.npz"
    pipeline_mode = False
    statistics_only = False
    productive_filter = False
    vdj_filter = False
    vj_filter = False

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

    if not barycenter_folder.exists() or not barycenter_folder.is_dir():
        print(f"Error: Barycenter folder does not exist: {barycenter_folder}")
        sys.exit(1)

    barycenter_path = _resolve_barycenter_path(barycenter_folder, barycenter_file)
    if not barycenter_path.exists():
        if not pipeline_mode:
            print(f"Error: Barycenter file not found: {barycenter_path}")
            print("Please run olga-barycenter-ot.py first to compute the barycenter.")
        sys.exit(1)

    try:
        grid, barycenter_weights = load_barycenter(str(barycenter_path))
    except Exception as exc:
        if not pipeline_mode:
            print(f"Error loading barycenter: {exc}")
        sys.exit(1)

    sample_files, custom_labels = _load_sample_files(samples_path)
    if len(sample_files) == 0:
        print("Error: No sample TSV files found")
        sys.exit(1)

    cloud_files = _load_cloud_files(barycenter_folder)
    if len(cloud_files) == 0:
        print(f"Error: No cloud TSV files found in barycenter folder: {barycenter_folder}")
        sys.exit(1)

    sample_results = _compute_distances(
        sample_files,
        grid,
        barycenter_weights,
        freq_column,
        weights_column,
        productive_filter,
        vdj_filter,
        vj_filter,
        custom_labels=custom_labels,
    )
    if len(sample_results) == 0:
        print("Error: No valid sample results to report")
        sys.exit(1)

    cloud_results = _compute_distances(
        cloud_files,
        grid,
        barycenter_weights,
        freq_column,
        weights_column,
        productive_filter,
        vdj_filter,
        vj_filter,
    )
    if len(cloud_results) == 0:
        print("Error: No valid cloud results to report")
        sys.exit(1)

    sample_distances = np.array([r["distance"] for r in sample_results])
    cloud_distances = np.array([r["distance"] for r in cloud_results])

    # One-sided Wilcoxon rank-sum via Mann-Whitney U:
    # H1 is cloud distances are smaller than sample distances.
    test_result = mannwhitneyu(cloud_distances, sample_distances, alternative="less", method="auto")
    u_stat = float(test_result.statistic)
    p_value = float(test_result.pvalue)

    if pipeline_mode:
        print(f"{p_value:.10e}")
        return

    print(f"Loading barycenter from: {barycenter_path}")
    print(f"  Grid size: {len(grid)}")
    print(f"  Grid range: [{grid.min():.3e}, {grid.max():.3e}]")
    print()
    print(f"Sample files processed: {len(sample_results)}")
    print(f"Cloud files processed:  {len(cloud_results)}")
    print()

    _print_group_table(
        "SAMPLE -> BARYCENTER WASSERSTEIN DISTANCES (sorted by distance, decreasing)",
        sample_results,
        statistics_only=statistics_only,
    )
    print()
    _print_group_table(
        "CLOUD -> BARYCENTER WASSERSTEIN DISTANCES (sorted by distance, decreasing)",
        cloud_results,
        statistics_only=statistics_only,
    )
    print()
    print("=" * 100)
    print("ONE-SIDED WILCOXON RANK-SUM TEST")
    print("=" * 100)
    print("Alternative hypothesis: cloud distances are smaller than sample distances")
    print(f"U statistic:   {u_stat:.6f}")
    print(f"One-sided p:  {p_value:.6e}")
    print("=" * 100)


if __name__ == "__main__":
    main()
