# TCR Optimal Transport Analysis

A toolkit for analyzing TCR distributions using Wasserstein Optimal Transport.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install numpy pandas pot matplotlib scikit-learn
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
5. `olga-boxplot-samples-ot-2pb.py` — compare sample distances with boxplot
6. `olga-mds-plot-samples.py` — MDS visualization of samples vs barycenter
7. `olga-simple-ot-mds-plot.py` — simplified MDS visualization (no barycenter)
8. `olga-samples-p2b-pval.py` — statistical significance of sample distances

---

## olga-barycenter-ot.py

Computes the Wasserstein barycenter from all TSV files in a folder.

### Usage

```bash
python3 olga-barycenter-ot.py <input_folder> [options]
```

### Parameters

- `--freq-column <col>` — frequencies column (default: pgen)
- `--weights-column <col>` — weights column or 'off' (default: duplicate_frequency_percent)
- `--n-grid <n>` — number of grid points (default: 200)
- `--barycenter <file>` — output filename for barycenter (default: barycenter.npz)
- `--productive-filter` — filter only productive sequences (if productive column exists)

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
- `--weights-column <col>` — default: duplicate_frequency_percent
- `--output-plot <file>` — output image path (default: barycenter_plot.png in input_folder)
- `--productive-filter` — filter only productive sequences (if productive column exists)

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
- `--weights-column <col>` — default: duplicate_frequency_percent
- `--n-grid <n>` — number of grid points (default: 200)
- `--barycenter <file>` — use barycenter grid (default: barycenter.npz)
- `--pipeline` — output only numbers (for scripts)
- `--statistics-only` — show only statistics (no table)
- `--productive-filter` — filter only productive sequences (if productive column exists)

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
- `--weights-column <col>` — default: duplicate_frequency_percent
- `--barycenter <file>` — path to barycenter (default: barycenter.npz)
- `--all` — process all TSV files
- `--pipeline` — output numbers only
- `--statistics-only` — show statistics only
- `--productive-filter` — filter only productive sequences (if productive column exists)

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

## olga-boxplot-samples-ot-2pb.py

Compares distances from two sample sets to a barycenter using a boxplot.

### Usage

```bash
python3 olga-boxplot-samples-ot-2pb.py <barycenter_folder> <samples> [options]
```

### Parameters

- `barycenter_folder` — folder with TSV files and barycenter.npz
- `samples` — either a folder with samples to map or a text file with one TSV path per line
- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: duplicate_frequency_percent
- `--barycenter <file>` — barycenter file (default: barycenter.npz)
- `--output-plot <file>` — output plot filename (default: ot-distance-boxplot.png)
- `--productive-filter` — filter only productive sequences (if productive column exists)

### Examples

```bash
python3 olga-boxplot-samples-ot-2pb.py input/test-cloud-Tumeh2014 input/new-samples

python3 olga-boxplot-samples-ot-2pb.py input/test-cloud-Tumeh2014 samples_list.txt \
    --weights-column duplicate_frequency_percent --output-plot comparison.png
```

**Output:** Boxplot with light green box (normal sample distances) and orange points (mapped sample distances with labels like 01B, 17P, etc.). If Base/Post is not found, the label is the patient number only.

---

## olga-mds-plot-samples.py

Creates an MDS visualization showing relationships between samples and a barycenter.

### Usage

```bash
python3 olga-mds-plot-samples.py <barycenter_folder> <samples> [options]
```

### Parameters

- `barycenter_folder` — folder with TSV files and barycenter.npz
- `samples` — either a folder with samples to map or a text file with one TSV path per line
- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: duplicate_frequency_percent
- `--barycenter <file>` — barycenter file (default: barycenter.npz)
- `--output-plot <file>` — output plot filename (default: ot-mds-plot.png)
- `--productive-filter` — filter only productive sequences (if productive column exists)

### How it works

1. Loads all samples from barycenter folder and samples folder
2. Computes all pairwise Wasserstein distances
3. Adds barycenter as a central point (distance to itself = 0)
4. Applies MDS algorithm to reduce distances to 2D space
5. Visualizes with light green points for normal samples, orange for mapped samples, and a green star for barycenter

### Examples

```bash
python3 olga-mds-plot-samples.py input/test-cloud-Tumeh2014 input/new-samples

python3 olga-mds-plot-samples.py input/test-cloud-Tumeh2014 samples_list.txt \
    --weights-column duplicate_frequency_percent --output-plot mds_analysis.png
```

**Output:** 2D MDS plot showing spatial relationships. Light green points = normal samples, orange points = mapped samples (labeled like 01B, 17P), 8-pointed green star = barycenter.

---

## olga-simple-ot-mds-plot.py

Creates a simplified MDS visualization of sample distributions without requiring a barycenter reference.

### Usage

```bash
python3 olga-simple-ot-mds-plot.py <samples> [options]
```

### Parameters

- `samples` — either a folder with TSV files or a text file with one TSV path per line
- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: duplicate_frequency_percent
- `--output-plot <file>` — output plot filename (default: ot-simple-mds-plot.png)
- `--productive-filter` — filter only productive sequences (if productive column exists)

### How it works

1. Loads samples from folder or text file list
2. Computes all pairwise Wasserstein distances
3. Applies MDS algorithm to reduce distances to 2D space
4. Visualizes with automatic color-coding by source directory
5. Adds semi-transparent points (α=0.6) to show overlaps

### Examples

```bash
# From a folder
python3 olga-simple-ot-mds-plot.py input/samples-folder

# From a sample list with custom labels
python3 olga-simple-ot-mds-plot.py input/samples-list.txt \
    --output-plot comparison.png

# With custom column names
python3 olga-simple-ot-mds-plot.py input/samples-folder \
    --freq-column my_frequency \
    --weights-column my_weights
```

### Features

- **Automatic directory coloring:** Points are color-coded by source directory (up to 20 colors)
- **Transparent points:** Semi-transparent fill (α=0.6) with black edges for visibility
- **Custom labels:** Supports custom labels from text file format: `path/file.tsv CustomLabel`
- **Auto-generated labels:** If no custom label, generates from filename (e.g., Patient01_Base → 01Base)
- **Legend:** Shows which color corresponds to which directory
- **Label placement:** Uses adjustText to avoid label overlaps

**Output:** 2D MDS plot with color-coded points (one color per directory) and descriptive labels.

---

## olga-samples-p2b-pval.py

Computes p-values for samples based on their distance to a barycenter.

### Usage

```bash
python3 olga-samples-p2b-pval.py <barycenter_folder> <samples> [options]
```

### Parameters

- `barycenter_folder` — folder with TSV files and barycenter.npz
- `samples` — either a folder with samples to evaluate or a text file with one TSV path per line
- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: duplicate_frequency_percent
- `--barycenter <file>` — barycenter file (default: barycenter.npz)
- `--productive-filter` — filter only productive sequences (if productive column exists)

### How it works

1. Loads all normal samples from barycenter folder
2. Computes distances to barycenter and fits null hypothesis model
3. Currently uses: Normal distribution fitted to normal sample distances
4. For each test sample, computes distance to barycenter
5. Calculates p-value: probability of observing this distance under null hypothesis
6. Displays results sorted by p-value (most significant first)

### Output format

Tabular results with three columns:
- `Sample` — label derived from filename (e.g., 01B or 17P)
- `Distance` — Wasserstein distance to barycenter
- `P-value` — raw two-tailed p-value (before correction)
- `Bonf. p` — Bonferroni-adjusted p-value (for significance assessment)

Summary statistics:
- Raw and adjusted p-value ranges
- Count of significant samples at different thresholds
- Number of tests used for Bonferroni correction

### Examples

```bash
python3 olga-samples-p2b-pval.py input/test-cloud-Tumeh2014 input/new-samples

python3 olga-samples-p2b-pval.py input/test-cloud-Tumeh2014 samples_list.txt \
    --weights-column duplicate_frequency_percent
```

### Notes on the statistical model and multiple testing correction

The current implementation uses a normal distribution fitted to distances from normal samples. This is a **temporary statistical model** that can be easily replaced.

For multiple testing correction, the script uses **Bonferroni adjustment**: each p-value is multiplied by the number of tests. This controls **Family-Wise Error Rate (FWER)** — the probability of making any false discovery. It's conservative but safe for exploratory analyses.

To try alternative models or corrections:
- Different null hypothesis models: Beta, Gamma, Kernel Density Estimation
- Alternative multiple testing corrections: Benjamini-Hochberg (FDR), permutation-based p-values
- More advanced statistical approaches

The model and correction method encapsulation makes it straightforward to test different statistical assumptions.

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

## Custom Sample Labels

When using a text file to specify samples (instead of a folder), you can optionally provide custom labels for each file. This is useful when files from different directories have similar names, or when you want specific labels for publication.

### Format

```text
# Each line: file_path [optional_custom_label]
/path/to/data1/Patient01_Base_tcr_pgen.tsv    P1-Before
/path/to/data2/Patient01_Base_tcr_pgen.tsv    P1-After
/path/to/Patient03_Base_tcr_pgen.tsv          ControlGroup
/path/to/Patient04_Base_tcr_pgen.tsv
# ^ No label specified - will auto-generate: 04B
```

### Behavior

- **With custom label:** Uses the provided label exactly as is
- **Without custom label:** Auto-generates label from filename (e.g., Patient01_Base → 01B, Patient17_Post → 17P)
- **Separator:** Any whitespace (space or tab) between path and label

### Example

```bash
# Create sample list with custom labels
cat > my_samples.txt << EOF
/data/cohort1/Patient01_Base_tcr_pgen.tsv    Cohort1-P1
/data/cohort2/Patient01_Base_tcr_pgen.tsv    Cohort2-P1
/data/special/Patient05_Base_tcr_pgen.tsv    SpecialCase
/data/control/Patient10_Base_tcr_pgen.tsv
EOF

# Use in any visualization/analysis script
python3 olga-boxplot-samples-ot-2pb.py input/test-cloud-Tumeh2014 my_samples.txt
python3 olga-mds-plot-samples.py input/test-cloud-Tumeh2014 my_samples.txt
python3 olga-samples-p2b-pval.py input/test-cloud-Tumeh2014 my_samples.txt
```

**Output:** Labels on plots and in tables will show "Cohort1-P1", "Cohort2-P1", "SpecialCase", and "10B" (auto-generated).

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
- `barycenter_plot.png` — visualization (26×14 inches)
- `distances-boxplot.png` — comparison boxplot (16×12 inches)
- `ot-mds-plot.png` — MDS spatial layout (24×20 inches)

All figures are sized 2x compared to standard plots for improved clarity and reduced label overlap with large sample sets.

---

## Documentation

Full development history: `HISTORY.md` (Русский)  
Technical context and architecture: `CONTEXT.md`  
Archive (earlier versions): `archive/copilot-chat.md`

## License

Research use only.

