# TCR OT Barycenter Analysis Workflow

## Quick Start

This project provides tools for analyzing TCR pgen distributions using Wasserstein optimal transport (OT) and computing their barycenters.

### Option A: Free-Support Barycenter (RECOMMENDED)

**Best for robust, outlier-resistant analysis:**

```bash
# Step 1: Compute the barycenter
python3 olga-barycenter-free-support.py input/test-cloud-Tumeh2014 --n-support 50

# Step 2: Visualize the barycenter
python3 olga-plot-barycenter-free-support.py input/test-cloud-Tumeh2014

# Output: barycenter_free_support.npz, barycenter_free_support_plot.png
```

**Why this method?**
- ✅ Adaptive support points (no fixed grid)
- ✅ Robust to extreme outliers
- ✅ Theoretically optimal (minimizes Wasserstein distance)
- ✅ Nearly uniform weight distribution


### Option B: LP Grid-Based Barycenter

**For comparison or when speed is critical:**

```bash
# Step 1: Compute the barycenter
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 --n-grid 200

# Step 2: Visualize the barycenter
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014

# Output: barycenter.npz, barycenter_plot.png
```

**Characteristics:**
- ⚡ Very fast computation
- 📊 Fixed discretization grid
- ⚠️ Can allocate excess mass to rare regions (artifact with extreme outliers)


### Compare Both Methods

```bash
python3 compare-barycenter-methods.py input/test-cloud-Tumeh2014

# Output: barycenter_comparison.png with detailed side-by-side comparison
```


## Computing P2P Distances

Compare pairwise Wasserstein distances between any two distributions:

```bash
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014/Patient01_Base_tcr_pgen.tsv \
                        input/test-cloud-Tumeh2014/Patient02_Base_tcr_pgen.tsv
```

Output: Wasserstein distance, visualizations, and statistical summary.


## Method Comparison

| Aspect | LP Grid-Based | Free-Support |
|--------|--------------|--------------|
| **Speed** | ~1 second | ~30 seconds |
| **Flexibility** | Fixed grid (200 points) | Adaptive (default √n_samples) |
| **First support point** | 2.506e-17 | 5.865e-09 |
| **Handling outliers** | ❌ Sensitive | ✅ Robust |
| **Weight distribution** | Variable | Nearly uniform (~2.0%) |
| **Theoretical optimality** | Heuristic | Provably optimal |

**Recommendation:** Use **FREE-SUPPORT** for production analysis.


## Input Data Format

Each TSV file should contain TCR clone frequencies:
```
pgen	count	...
1.42e-24	5	...
3.54e-06	2	...
```

The tool looks for a `pgen` column by default. Use `--freq-column` to specify a different column.


## Parameters

### olga-barycenter-free-support.py
- `--n-support N` : Number of support points (default: √#samples)
- `--freq-column COL` : Column name or index for frequencies

### olga-barycenter-ot.py
- `--n-grid N` : Number of grid points (default: 200)
- `--freq-column COL` : Column name or index for frequencies

### olga-plot-* scripts
- `--freq-column COL` : Column name or index for frequencies
- Custom barycenter file paths (relative paths like `~/` supported)


## Output Files

### From Free-Support Pipeline
- `barycenter_free_support.npz` - Numpy archive with:
  - `support`: Array of support point coordinates
  - `barycenter`: Array of weights at each support point
  
- `barycenter_free_support_plot.png` - Dual-panel visualization:
  - Top: Individual distributions + barycenter support points
  - Bottom: Discretized histogram view

### From LP Grid Pipeline
- `barycenter.npz` - Numpy archive with:
  - `grid`: Array of grid point coordinates
  - `barycenter`: Array of probabilities at each grid point
  
- `barycenter_plot.png` - Visualization with all distributions

### Comparison
- `barycenter_comparison.png` - Side-by-side analysis of both methods


## Understanding the Plots

### Dual-Panel Visualization (Free-Support)
1. **Top panel:**
   - Vertical lines with log-scale x-axis (pgen values)
   - Red dots: Barycenter support points (optimized locations)
   - Light gray background: Individual patient distributions
   
2. **Bottom panel:**
   - Binned histogram showing "expected frequency" 
   - Easier to interpret for users unfamiliar with OT

### Comparison Plot
- **Top-left:** LP grid barycenter (blue)
- **Top-right:** Free-support barycenter (red)
- **Middle-left:** Cumulative mass comparison
- **Middle-right:** Mass in leftmost N points (shows tail artifact)
- **Bottom:** Statistics table


## Troubleshooting

**Q: "barycenter.npz not found"**
- Run the corresponding barycenter computation script first

**Q: Free-support is slow**
- Reduce `--n-support` parameter (default is √n_samples)
- LP grid-based is faster if speed is critical

**Q: Missing fonts warning**
- This is just a matplotlib warning, output PNG is still generated

**Q: Wrong column being read**
- Specify column explicitly: `--freq-column 0` (for first column)


## Citation

This workflow implements Wasserstein optimal transport methods from:

- Python Optimal Transport (POT): Flamary et al., Journal of Machine Learning Research 2021
- Barycenter algorithms: Agueh & Carlier (2011), Cuturi & Doucet (2014)


## Contact

For issues or feature requests, review the scripts and README.md.
