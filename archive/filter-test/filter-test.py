#!/usr/bin/env python3
"""
Compare two TSV files after optional filtering and export set differences by first-column key.

Outputs:
- <prefix>direct-difference.tsv  : rows present in file1 but absent in file2 (by first column)
- <prefix>reverse-difference.tsv : rows present in file2 but absent in file1 (by first column)
"""

import argparse
from pathlib import Path
import sys
import pandas as pd


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Filter two TSV files and write direct/reverse set differences by first-column key."
    )
    parser.add_argument("file1", help="First TSV file")
    parser.add_argument("file2", help="Second TSV file")
    parser.add_argument(
        "--productive-filter",
        action="store_true",
        help="Filter only productive rows (if productive column exists)",
    )
    parser.add_argument(
        "--vdj-filter",
        action="store_true",
        help="Require non-empty v_call/d_call/j_call for columns that exist",
    )
    parser.add_argument(
        "--vj-filter",
        action="store_true",
        help="Require non-empty v_call/j_call for columns that exist",
    )
    parser.add_argument(
        "--result-prefix",
        default="",
        help="Prefix for output filenames (default: empty)",
    )
    return parser.parse_args()


def _apply_productive_filter(df: pd.DataFrame) -> pd.DataFrame:
    if "productive" not in df.columns:
        return df

    col = df["productive"]
    if pd.api.types.is_bool_dtype(col):
        mask = col == True
    else:
        normalized = col.astype(str).str.strip().str.lower()
        mask = normalized.isin({"true", "1", "t", "yes", "y"})

    return df[mask].copy()


def _apply_vdj_filter(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df
    for vdj_col in ("v_call", "d_call", "j_call"):
        if vdj_col in filtered.columns:
            mask = filtered[vdj_col].notna() & (filtered[vdj_col].astype(str).str.strip() != "")
            filtered = filtered[mask].copy()
    return filtered


def _apply_vj_filter(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df
    for vj_col in ("v_call", "j_call"):
        if vj_col in filtered.columns:
            mask = filtered[vj_col].notna() & (filtered[vj_col].astype(str).str.strip() != "")
            filtered = filtered[mask].copy()
    return filtered


def _load_and_filter(path: Path, productive_filter: bool, vdj_filter: bool, vj_filter: bool) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t")
    print(f"[filter] {path}: loaded rows = {len(df)}")

    if productive_filter:
        before = len(df)
        has_productive = "productive" in df.columns
        df = _apply_productive_filter(df)
        after = len(df)
        if has_productive:
            print(f"[filter] {path}: --productive-filter applied ({before} -> {after})")
        else:
            print(f"[filter] {path}: --productive-filter skipped (column 'productive' not found, rows = {after})")

    if vdj_filter:
        before = len(df)
        checked_cols = [col for col in ("v_call", "d_call", "j_call") if col in df.columns]
        df = _apply_vdj_filter(df)
        after = len(df)
        if checked_cols:
            print(f"[filter] {path}: --vdj-filter applied on {checked_cols} ({before} -> {after})")
        else:
            print(f"[filter] {path}: --vdj-filter skipped (no v_call/d_call/j_call columns, rows = {after})")

    if vj_filter:
        before = len(df)
        checked_cols = [col for col in ("v_call", "j_call") if col in df.columns]
        df = _apply_vj_filter(df)
        after = len(df)
        if checked_cols:
            print(f"[filter] {path}: --vj-filter applied on {checked_cols} ({before} -> {after})")
        else:
            print(f"[filter] {path}: --vj-filter skipped (no v_call/j_call columns, rows = {after})")

    print(f"[filter] {path}: final rows = {len(df)}")

    return df


def main():
    args = _parse_args()

    file1 = Path(args.file1)
    file2 = Path(args.file2)

    if not file1.exists():
        print(f"Error: file not found: {file1}")
        sys.exit(1)
    if not file2.exists():
        print(f"Error: file not found: {file2}")
        sys.exit(1)

    try:
        df1 = _load_and_filter(file1, args.productive_filter, args.vdj_filter, args.vj_filter)
        df2 = _load_and_filter(file2, args.productive_filter, args.vdj_filter, args.vj_filter)
    except Exception as exc:
        print(f"Error while reading/filtering files: {exc}")
        sys.exit(1)

    if len(df1.columns) == 0:
        print(f"Error: no columns in file: {file1}")
        sys.exit(1)
    if len(df2.columns) == 0:
        print(f"Error: no columns in file: {file2}")
        sys.exit(1)

    key1 = df1.columns[0]
    key2 = df2.columns[0]

    keys1 = set(df1[key1].astype(str))
    keys2 = set(df2[key2].astype(str))

    direct_df = df1[~df1[key1].astype(str).isin(keys2)].copy()
    reverse_df = df2[~df2[key2].astype(str).isin(keys1)].copy()

    out_direct = Path(f"{args.result_prefix}direct-difference.tsv")
    out_reverse = Path(f"{args.result_prefix}reverse-difference.tsv")

    direct_df.to_csv(out_direct, sep="\t", index=False)
    reverse_df.to_csv(out_reverse, sep="\t", index=False)

    print(f"File 1: {file1}")
    print(f"  Rows after filtering: {len(df1)}")
    print(f"  Key column: {key1}")
    print(f"File 2: {file2}")
    print(f"  Rows after filtering: {len(df2)}")
    print(f"  Key column: {key2}")
    print()
    print(f"Direct difference rows (file1 - file2): {len(direct_df)}")
    print(f"Reverse difference rows (file2 - file1): {len(reverse_df)}")
    print()
    print(f"Saved: {out_direct}")
    print(f"Saved: {out_reverse}")


if __name__ == "__main__":
    main()
