olga-barycenter-free-support.py -- reads all TSV files in a folder and computes the
Wasserstein barycenter using FREE-SUPPORT method (adaptive support points, no fixed grid).
This method automatically avoids artifacts from extreme outliers and is more robust
than fixed-grid methods for data with heavy tails or extreme values.

Usage:
python3 olga-barycenter-free-support.py <input_folder> [--freq-column <col>] [--weights-column <col>] [--n-support <n>]

Parameters:
- input_folder: folder with TSV files
- --freq-column: column index (0-based) or column name for sample values (default: pgen)
- --weights-column: column index/name for weights or 'off' (default: off)
- --n-support: number of support points in barycenter (default: sqrt(n_samples))

Examples:
python3 olga-barycenter-free-support.py input/test-cloud-Tumeh2014
python3 olga-barycenter-free-support.py input/test-cloud-Tumeh2014 --n-support 50
python3 olga-barycenter-free-support.py input/test-cloud-Tumeh2014 --freq-column pgen --weights-column duplicate_frequency_percent

Output:
- barycenter_free_support.npz: Contains 'barycenter' (weights) and 'support' (positions) arrays

olga-plot-barycenter-free-support.py -- reads all TSV files in a folder and plots them alongside
the FREE-SUPPORT Wasserstein barycenter (adaptive support method). Individual distributions shown
in light gray, barycenter highlighted in red with thicker line. Creates two plots:
1. Scatter plot with support points
2. Discretized histogram view for intuitive comparison

Usage:
python3 olga-plot-barycenter-free-support.py <input_folder> [barycenter_file] [--freq-column <col>]

Parameters:
- input_folder: folder with TSV files
- barycenter_file: path to barycenter NPZ file (default: barycenter_free_support.npz)
- --freq-column: column index/name for sample values (default: pgen)

Examples:
python3 olga-plot-barycenter-free-support.py input/test-cloud-Tumeh2014
python3 olga-plot-barycenter-free-support.py input/test-cloud-Tumeh2014 barycenter_free_support.npz
python3 olga-plot-barycenter-free-support.py input/test-cloud-Tumeh2014 --freq-column pgen

Output: barycenter_free_support_plot.png (high-resolution PNG)

olga-plot-barycenter.py -- reads all TSV files in a folder and plots them alongside
the LP GRID-BASED Wasserstein barycenter. Individual distributions shown in light gray,
barycenter highlighted in red with thicker line.

Usage:
python3 olga-plot-barycenter.py <input_folder> [barycenter_file] [--freq-column <col>] [--weights-column <col>]

Parameters:
- input_folder: folder with TSV files
- barycenter_file: path to barycenter NPZ file (default: barycenter.npz in input_folder)
- --freq-column: column index/name for sample values (default: pgen)
- --weights-column: column index/name for weights or 'off' (default: off)

Examples:
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014 barycenter.npz

## Visualization Comparison

| Feature | olga-plot-barycenter.py | olga-plot-barycenter-free-support.py |
|---------|-----|-----|
| Input barycenter | LP grid-based (.npz) | Free-support (.npz) |
| Plot type | Single line plot | Dual plot (scatter + histogram) |
| Best for | Quick overview | Detailed analysis |
| File name | barycenter_plot.png | barycenter_free_support_plot.png |

## Recommendation Workflow

For robust analysis of TCR distribution clouds:

```bash
# Step 1: Compute free-support barycenter (more robust)
python3 olga-barycenter-free-support.py input/test-cloud-Tumeh2014 --n-support 50

# Step 2: Visualize the result
python3 olga-plot-barycenter-free-support.py input/test-cloud-Tumeh2014

# Step 3: Compare distances between distributions
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 Patient01_Base_tcr_pgen.tsv Patient02_Base_tcr_pgen.tsv
```

## Comparing Barycenter Methods

### olga-barycenter-ot.py (Fixed Grid LP)
- Uses log-spaced grid with fixed number of points
- Fast computation
- **Issue**: Can allocate excess mass to regions with few samples (e.g., extreme outliers)
- **Use when**: You want speed and have confidence in grid coverage

### olga-barycenter-free-support.py (Adaptive Support) ⭐ **Recommended for robust analysis**
- Adaptively places support points where needed
- Automatically avoids artifacts from extreme outliers
- True Wasserstein barycenter with optimized weights
- Slower than fixed-grid but handles extreme values gracefully
- **Use when**: Data may have outliers or extreme values, and robustness is important

### Comparison on TCR Data
With 25 distributions containing values from 1.42e-24 to 3.54e-06:

| Aspect | LP Grid (200 points) | Free-Support (50 points) |
|--------|-----|-----|
| First support point | 1.42e-24 (extreme) | 5.86e-09 (reasonable) |
| Mass in leftmost 10 points | ~20% | ~2% |
| Adapts to outliers | ✗ No | ✓ Yes |
| Computation time | Fast | Moderate (~minutes) |
| Robustness | Lower | Higher |

