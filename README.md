# TCR Optimal Transport Analysis

A toolkit for analyzing TCR distributions using Wasserstein Optimal Transport.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install numpy pandas pot matplotlib
```

## Architecture

**Core module:** `ot_utils.py` — shared utilities for all scripts
- Single metric: log_l1 (for data spanning 18 orders of magnitude)
- Automatic grid extension for out-of-sample data
- Smart column finding (exact match → substring match)

**Scripts:**
1. `olga-barycenter-ot.py` — compute Wasserstein barycenter
2. `olga-plot-barycenter.py` — visualize barycenter
3. `olga-p2p-ot.py` — pairwise distances between distributions
4. `olga-p2b-ot.py` — distances from distributions to barycenter
5. `olga-map-samples-p2b.py` — map samples to barycenter with visualization

---

## olga-barycenter-ot.py

Computes the Wasserstein barycenter from all TSV files in a folder.

### Usage

```bash
python3 olga-barycenter-ot.py <input_folder> [options]
```

### Parameters

- `--freq-column <col>` — frequencies column (default: pgen)
- `--weights-column <col>` — weights column or 'off' (default: off)
- `--n-grid <n>` — number of grid points (default: 200)
- `--barycenter <file>` — output filename for barycenter (default: barycenter.npz)

### Examples

```bash
# Basic usage
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014

# With weights
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent

# Custom grid size
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 --n-grid 500

# Save to custom file
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 --barycenter my_barycenter.npz
```

**Output:** Creates a file with barycenter grid points and weights (default: `input_folder/barycenter.npz`).

---

## olga-plot-barycenter.py

Creates a visualization of the barycenter with individual distributions.

### Usage

```bash
python3 olga-plot-barycenter.py <input_folder> [options]
```

### Parameters

- `--barycenter <file>` — path to barycenter (default: barycenter.npz in input_folder)
- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: off
- `--output <file>` — output image path (default: input_folder/barycenter_plot.png)

### Examples

```bash
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent

# With custom barycenter
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014 \
    --barycenter ~/data/my_barycenter.npz
```

**Output:** PNG image with barycenter and all individual distributions.

---

## olga-p2p-ot.py

Computes Wasserstein distances between distributions.

### Three modes of operation

**1. Single pair — distance between two files**
```bash
python3 olga-p2p-ot.py <input_folder> <file1.tsv> <file2.tsv>
```

**2. One-to-all — from one file to all others**
```bash
python3 olga-p2p-ot.py <input_folder> <file1.tsv> --all
```

**3. All-pairs — all pairwise distances (upper triangle)**
```bash
python3 olga-p2p-ot.py <input_folder> --all
```

### Parameters

- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: off
- `--n-grid <n>` — number of grid points (default: 200)
- `--barycenter <file>` — use barycenter grid (default: barycenter.npz)
- `--pipeline` — output only numbers (for scripts)
- `--statistics-only` — show only statistics (no table)

### Examples

```bash
# Single pair
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 \
    Patient01_Base_tcr_pgen.tsv Patient02_Base_tcr_pgen.tsv

# One-to-all with weights
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 \
    Patient01_Base_tcr_pgen.tsv --all \
    --weights-column duplicate_frequency_percent

# All-pairs with barycenter grid (for consistency with p2b)
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 \
    --all --barycenter barycenter.npz --statistics-only

# Pipeline mode (numbers only)
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 \
    Patient01_Base_tcr_pgen.tsv Patient02_Base_tcr_pgen.tsv --pipeline
```

**Output:**
- Normal: table + statistics
- `--pipeline`: numbers only (one per line)
- `--statistics-only`: Count, Mean, Median, Std, Min, Max, Q1, Q3

---

## olga-p2b-ot.py

Computes Wasserstein distances from distributions to the barycenter.

### Usage

```bash
# Single file
python3 olga-p2b-ot.py <input_folder> <file.tsv> [options]

# Batch mode (all files)
python3 olga-p2b-ot.py <input_folder> [--all] [options]
```

### Parameters

- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: off
- `--barycenter <file>` — path to barycenter (default: barycenter.npz)
- `--all` — process all TSV files
- `--pipeline` — output numbers only
- `--statistics-only` — show statistics only

### Examples

```bash
# Single file
python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 \
    Patient01_Base_tcr_pgen.tsv

# Batch mode with weights
python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent --statistics-only

# Pipeline mode
python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 \
    Patient01_Base_tcr_pgen.tsv --pipeline
```

**Output:**
- Single file: distance + detailed info
- Batch mode: table sorted by distance + statistics
- `--pipeline`: numbers only
- `--statistics-only`: statistics only

---

## olga-map-samples-p2b.py

Maps sample distributions to a barycenter and creates a comparison visualization.

### Usage

```bash
python3 olga-map-samples-p2b.py <barycenter_folder> <samples_folder> [options]
```

### Parameters

- `barycenter_folder` — folder with TSV files and barycenter.npz
- `samples_folder` — folder with samples to map
- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: off
- `--barycenter <file>` — barycenter file (default: barycenter.npz)

### Examples

```bash
python3 olga-map-samples-p2b.py input/test-cloud-Tumeh2014 input/new-samples

python3 olga-map-samples-p2b.py input/test-cloud-Tumeh2014 input/new-samples \
    --weights-column duplicate_frequency_percent
```

**Output:** `distances-boxplot.png` — boxplot of normal sample distances (light green) with mapped sample distances (orange points with labels).

---

## Smart Column Finding

All scripts support flexible column specification:

**1. Exact name:**
```bash
--freq-column pgen
--weights-column duplicate_frequency_percent
```

**2. Substring (if unique):**
```bash
--weights-column duplicate_frequency_p   # finds duplicate_frequency_percent
--weights-column frequency_percent       # finds duplicate_frequency_percent
--weights-column count                   # finds duplicate_count
```

**3. Column index:**
```bash
--freq-column 22       # column 22 (pgen)
--weights-column 18    # column 18
```

**Diagnostics:**
```bash
# Ambiguous substring
--weights-column duplicate
# Error: ambiguous column specification 'duplicate'
#        Multiple matches: ['duplicate_count', 'duplicate_frequency_percent']

# Non-existent column
--freq-column xyz
# Error: no column found matching 'xyz'
#        Available columns: [...]
```

---

## Typical Workflows

### 1. Compute barycenter and analyze

```bash
# Step 1: Compute barycenter
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent

# Step 2: Visualize
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent

# Step 3: Distances to barycenter
python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent --statistics-only
```

### 2. Pairwise comparisons

```bash
# All pairs with consistent grid
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 \
    --all --barycenter barycenter.npz \
    --weights-column duplicate_frequency_percent --statistics-only
```

### 3. Leave-one-out validation

```bash
# For each patient:
# 1. Compute barycenter without them
# 2. Compute distance from them to barycenter

for patient in Patient{01..25}_Base_tcr_pgen.tsv; do
    echo "Processing $patient"
    # Compute barycenter without this patient
    python3 olga-barycenter-ot.py input/cohort --exclude $patient
    # Compute distance
    python3 olga-p2b-ot.py input/cohort $patient --pipeline
done
```

### 4. Shell scripting with pipeline mode

```bash
#!/bin/bash
# Find patient closest to barycenter

min_dist=999999
closest=""

for file in input/test-cloud-Tumeh2014/*.tsv; do
    dist=$(python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 \
        $(basename $file) --pipeline)
    if (( $(echo "$dist < $min_dist" | bc -l) )); then
        min_dist=$dist
        closest=$(basename $file)
    fi
done

echo "Closest to barycenter: $closest (distance: $min_dist)"
```

---

## Technical Details

### Metric

**log_l1 metric in logarithmic space:**
```
cost(x₁, x₂) = |log(x₁) - log(x₂)|
```

**Why log_l1 instead of L1?**
- pgen data: [1.42e-24, 3.54e-06] (18 orders of magnitude!)
- L1 in original space: difference between 1e-24 and 1e-23 ≈ 0 (suppressed)
- log_l1: all orders of magnitude treated fairly

### Automatic Grid Extension

If data falls outside barycenter grid bounds:
- Grid is automatically extended
- Logarithmic spacing is preserved
- Original points stay in place
- New points get zero weight

This allows comparing any distribution with the barycenter, even if it didn't participate in barycenter computation.

### Data Structure

**Input TSV files:** 23 columns, including:
- `pgen` (col 22) — generation probability
- `duplicate_count` (col 17) — number of duplicates
- `duplicate_frequency_percent` (col 18) — frequency percentage

**Output files:**
- `barycenter.npz` — NumPy archive with grid and weights
- `barycenter_plot.png` — visualization
- `distances-boxplot.png` — comparison boxplot

---

## Documentation

Full development history: `archive/copilot-chat.md`  
Technical architecture: `.copilot-context.md`

## License

Research use only.

