#!/usr/bin/env python3
"""
Build a null distribution of OT distances to barycenter.

Workflow:
1) Ensure a reference barycenter exists (compute it if missing).
2) Add distances from all cloud samples to that reference barycenter.
3) Run bootstrap iterations:
   - Build a bootstrap barycenter from resampled cloud samples.
   - Sample a share of bootstrap samples and compute their distances
     to the bootstrap barycenter.
   - Append those distances to the null distribution.
4) Save the null distribution as a plain text file.
"""

import os
import argparse
import time
from pathlib import Path

import numpy as np

from ot_utils import (
    load_distribution,
    load_barycenter,
    compute_wasserstein_distance,
    discretize_distribution,
    compute_lp_barycenter,
    compute_lp_barycenter_on_grid,
    extend_grid_if_needed,
)


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Build p2b OT null distribution using cloud samples and bootstrap barycenters.",
    )
    parser.add_argument("input_folder", help="Folder with cloud TSV files and optional barycenter file")
    parser.add_argument("--freq-column", default="pgen", dest="freq_column")
    parser.add_argument(
        "--weights-column",
        default="duplicate_frequency_percent",
        dest="weights_column",
    )
    parser.add_argument("--n-grid", type=int, default=200, dest="n_grid")
    parser.add_argument("--barycenter", default="barycenter.npz", dest="barycenter_file")
    parser.add_argument("--bootstrap-n", type=int, default=5000, dest="bootstrap_n")
    parser.add_argument(
        "--share-samples-to-null",
        type=float,
        default=0.1,
        dest="share_samples_to_null",
        help="Share of bootstrap samples used for null distances per iteration",
    )
    parser.add_argument(
        "--return-when-sample-samples",
        action="store_true",
        dest="return_when_sample_samples",
        help="Sample bootstrap subset with replacement (default: without replacement)",
    )
    parser.add_argument("--output-null", default="p2b-ot-null.txt", dest="output_null")
    parser.add_argument("--seed", type=int, default=42, dest="seed")
    parser.add_argument("--productive-filter", action="store_true", dest="productive_filter")
    parser.add_argument("--vdj-filter", action="store_true", dest="vdj_filter")
    parser.add_argument("--vj-filter", action="store_true", dest="vj_filter")
    args = parser.parse_args()

    if args.n_grid <= 1:
        parser.error("--n-grid must be > 1")
    if args.bootstrap_n < 0:
        parser.error("--bootstrap-n must be >= 0")
    if args.share_samples_to_null <= 0 or args.share_samples_to_null > 1:
        parser.error("--share-samples-to-null must be in (0, 1]")

    return args


def _resolve_path(folder, filename):
    """Resolve path as absolute/home-expanded or relative to folder."""
    if os.path.isabs(filename) or filename.startswith("~"):
        return Path(os.path.expanduser(filename))
    return folder / filename


def _load_cloud_distributions(args, input_folder):
    """Load cloud sample files and return immutable arrays for reuse."""
    cloud_files = sorted(input_folder.glob("*.tsv"))
    if not cloud_files:
        raise ValueError(f"No TSV files found in {input_folder}")

    values_list = []
    weights_list = []
    for file_path in cloud_files:
        values, weights = load_distribution(
            str(file_path),
            freq_column=args.freq_column,
            weights_column=args.weights_column,
            productive_filter=args.productive_filter,
            vdj_filter=args.vdj_filter,
            vj_filter=args.vj_filter,
        )
        values_list.append(values)
        weights_list.append(weights)

    return cloud_files, values_list, weights_list


def _get_reference_barycenter(barycenter_path, values_list, weights_list, n_grid):
    """Load existing reference barycenter or compute/save if missing."""
    if barycenter_path.exists():
        print(f"Using existing barycenter: {barycenter_path}")
        return load_barycenter(str(barycenter_path))

    print(f"Barycenter not found, computing: {barycenter_path}")
    t0 = time.perf_counter()
    grid, barycenter = compute_lp_barycenter(values_list, weights_list, n_grid=n_grid)
    elapsed = time.perf_counter() - t0
    barycenter_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(barycenter_path, grid=grid, barycenter=barycenter)
    print("Reference barycenter computed and saved.")
    print(f"Reference barycenter computation time: {elapsed:.2f} s")
    return grid, barycenter


def _distance_to_barycenter(values, weights, grid, barycenter):
    """Compute p2b OT distance for one distribution."""
    extended_grid, extended_barycenter = extend_grid_if_needed(
        grid,
        barycenter,
        values.min(),
        values.max(),
    )
    sample_discretized = discretize_distribution(values, weights, extended_grid)
    return compute_wasserstein_distance(
        extended_grid,
        sample_discretized,
        extended_grid,
        extended_barycenter,
        metric="log_l1",
        method="emd",
    )


def _collect_reference_null(values_list, weights_list, ref_grid, ref_barycenter):
    """Collect all cloud -> reference barycenter distances."""
    return [
        _distance_to_barycenter(values, weights, ref_grid, ref_barycenter)
        for values, weights in zip(values_list, weights_list)
    ]


def _collect_bootstrap_null(
    values_list,
    weights_list,
    fixed_grid,
    bootstrap_n,
    share_samples_to_null,
    return_when_sample_samples,
    rng,
):
    """Collect null distances from bootstrap barycenters.

    Bootstrap is applied only to the sample index list. Input distributions
    themselves are fixed and reused unchanged on every iteration.
    """
    n_samples = len(values_list)
    all_idx = np.arange(n_samples)
    subset_size = max(1, int(np.ceil(share_samples_to_null * n_samples)))
    distances = []
    barycenter_time_total = 0.0

    for iteration in range(bootstrap_n):
        # 1) Bootstrap sample list by indices (with replacement).
        bootstrap_idx = rng.choice(all_idx, size=n_samples, replace=True)

        # 2) Compute bootstrap barycenter weights on the fixed precomputed grid.
        boot_values = [values_list[i] for i in bootstrap_idx]
        boot_weights = [weights_list[i] for i in bootstrap_idx]
        t0 = time.perf_counter()
        boot_barycenter = compute_lp_barycenter_on_grid(
            fixed_grid,
            boot_values,
            boot_weights,
        )
        elapsed = time.perf_counter() - t0
        barycenter_time_total += elapsed

        # 3) Select a share of bootstrap-list positions.
        subset_pos = rng.choice(
            np.arange(n_samples),
            size=subset_size,
            replace=return_when_sample_samples,
        )

        # 4) Compute distances for original unchanged distributions referenced by indices.
        for pos in subset_pos:
            original_idx = bootstrap_idx[pos]
            dist = _distance_to_barycenter(
                values_list[original_idx],
                weights_list[original_idx],
                fixed_grid,
                boot_barycenter,
            )
            distances.append(dist)

        if (iteration + 1) % 1 == 0 or iteration == 0 or (iteration + 1) == bootstrap_n:
            avg_time = barycenter_time_total / (iteration + 1)
            print(
                f"Bootstrap {iteration + 1}/{bootstrap_n}: "
                f"added {len(distances)} distances; "
                f"last barycenter {elapsed:.2f} s; avg {avg_time:.2f} s"
            )

    return distances


def main():
    args = parse_args()
    input_folder = Path(args.input_folder).expanduser()

    if not input_folder.exists() or not input_folder.is_dir():
        print(f"Error: input folder does not exist: {input_folder}")
        raise SystemExit(1)

    barycenter_path = _resolve_path(input_folder, args.barycenter_file)
    output_path = _resolve_path(input_folder, args.output_null)

    print(f"Loading cloud samples from: {input_folder}")
    cloud_files, values_list, weights_list = _load_cloud_distributions(args, input_folder)
    print(f"Loaded {len(cloud_files)} cloud sample distribution(s)")

    ref_grid, ref_bary = _get_reference_barycenter(
        barycenter_path,
        values_list,
        weights_list,
        n_grid=args.n_grid,
    )

    null_distances = _collect_reference_null(values_list, weights_list, ref_grid, ref_bary)
    print(f"Initial null size (cloud -> reference barycenter): {len(null_distances)}")

    rng = np.random.default_rng(args.seed)
    if args.bootstrap_n > 0:
        extra = _collect_bootstrap_null(
            values_list=values_list,
            weights_list=weights_list,
            fixed_grid=ref_grid,
            bootstrap_n=args.bootstrap_n,
            share_samples_to_null=args.share_samples_to_null,
            return_when_sample_samples=args.return_when_sample_samples,
            rng=rng,
        )
        null_distances.extend(extra)

    null_array = np.array(null_distances, dtype=float)
    null_array.sort()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(output_path, null_array, fmt="%.10e")

    print("-")
    print(f"Saved null distribution to: {output_path}")
    print(f"Count:  {len(null_array)}")
    print(f"Mean:   {np.mean(null_array):.6e}")
    print(f"Median: {np.median(null_array):.6e}")
    print(f"Std:    {np.std(null_array):.6e}")
    print(f"Min:    {np.min(null_array):.6e}")
    print(f"Max:    {np.max(null_array):.6e}")


if __name__ == "__main__":
    main()
