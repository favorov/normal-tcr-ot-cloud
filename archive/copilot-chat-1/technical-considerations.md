# Technical Considerations for TCR OT Barycenter

## Problem: Left-Tail Artifact in OT Barycenter

### Observation
When computing Wasserstein barycenter with `ot.lp.barycenter()`, there is significant mass concentration in the left tail (grid[0-5]) despite very few actual samples there (~1 sample out of 1834 total).

### Root Cause Analysis

**Data Characteristics:**
- 25 TSV files with ~75 samples each (1834 total)
- pgen range: 1.42e-24 to 3.54e-06 (18 orders of magnitude)
- Patient10 has ONE extreme outlier: 1.42e-24 (99.99% of other data is > 1e-10)

**Grid Construction (percentile-based):**
- Grid built between 1st-99th percentiles: [2.506e-17, 1.381e-06]
- Patient10's extreme value (1.42e-24) falls OUTSIDE the grid's left boundary
- Patient10's entire distribution gets binned to grid[0] with probability 1.0

**LP Solver Behavior:**
- LP solver minimizes: sum of Wasserstein distances from barycenter to each input distribution
- To minimize distance to Patient10 (which has all mass at grid[0]), the solver allocates mass to grid[0] in the barycenter
- Result: grid[0] gets ~5.4% probability despite only 1 sample (1/1834 = 0.05%)
- This is 93x higher than the actual sample proportion

**Comparison of Methods:**

| Method | grid[0] prob | First 5 bins | Behavior |
|--------|-------------|------------|----------|
| OT LP Barycenter | 5.4% | ~20% | Minimizes transport distance (mass goes to outlier source) |
| Sinkhorn (entropy reg) | 5.0% | 25% | Approximates uniform distribution (ignores sample frequency) |
| Simple Average | 0.24% | 0.5% | Preserves true sample proportions |

### Why Percentile-Based Grid?

**Problem with min-max grid:**
- If grid spans [1.42e-24, 3.54e-06], the left edge is completely wasted on a single outlier value
- Even Sinkhorn produces uniform distribution, not frequency-weighted

**Solution with percentile-based grid:**
- Grid spans [1st percentile, 99th percentile] = [2.51e-17, 1.38e-06]
- Outlier (1.42e-24) bins into grid[0] same as with min-max, but grid is now concentrated on realistic data range
- Result: Reduced artifact from 5.4% to ~0.46% in grid[0]

**This is not filtering:**
- All original data is preserved
- Outlier is still included (binned into nearest grid point)
- No samples are removed or downweighted
- The issue is purely in discretization grid construction, not in the optimization

### Mathematical Perspective

OT barycenter solves:
```
min_μ ∑ᵢ W(μ, μᵢ)
```

Where:
- μ is the barycenter distribution
- W is the Wasserstein distance
- μᵢ are input distributions

With a sparse grid and one distribution concentrated at an isolated grid point, the solver MUST allocate mass proportional to transport cost, not sample frequency.

### Recommendation for Future Work

Consider whether OT barycenter is the right tool:

1. **OT Barycenter (current)**: Minimizes transport distance
   - Useful when you want a distribution that is "close" in Wasserstein metric
   - Not ideal for summary statistics

2. **Simple Average**: Averages probabilities across distributions
   - Preserves true sample proportions
   - Only 1 line of code: `barycenter = distributions_matrix.mean(axis=0)`
   - More intuitive for "representative distribution"

3. **Weighted Average**: If files have different sample sizes
   - `barycenter = np.average(distributions_matrix, axis=0, weights=sizes)`

### Code References

- **Grid discretization:** olga-barycenter-ot.py lines 73-87
- **Barycenter computation:** olga-barycenter-ot.py line 96
- **Test script:** test-free-support-barycenter.py (tested various barycenter methods)

### Testing

Created debug scripts to investigate:
- `debug-left-tail.py`: Confirmed 1 sample at 1.42e-22 in Patient10, barycenter has 20% mass there
- `debug-barycenter-methods.py`: Compared LP vs Sinkhorn vs simple average
- `debug-outlier-issue.py`: Analyzed distribution matrix sparsity (49% zeros), showed LP allocates 93x more mass than average
