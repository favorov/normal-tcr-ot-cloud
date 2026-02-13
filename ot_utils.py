#!/usr/bin/env python3
"""
Common utilities for Optimal Transport operations on TCR distributions.
Provides consistent distance computation across all scripts.
"""
import numpy as np
import pandas as pd
import ot


def _find_column_index(df, column_spec, param_name):
    """
    Find column index by exact name or substring match.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to search in
    column_spec : str or int
        Column specification (name, substring, or index)
    param_name : str
        Parameter name for error messages
        
    Returns
    -------
    int
        Column index
        
    Raises
    ------
    ValueError
        If column cannot be uniquely identified
    """
    if isinstance(column_spec, int):
        if column_spec < 0 or column_spec >= len(df.columns):
            raise ValueError(
                f"Parameter '{param_name}': column index {column_spec} is out of range. "
                f"Available columns: {list(df.columns)}"
            )
        return column_spec
    
    # String specification
    column_spec_str = str(column_spec)
    
    # Try exact match first
    if column_spec_str in df.columns:
        return df.columns.get_loc(column_spec_str)
    
    # Try substring match
    matches = [col for col in df.columns if column_spec_str in col]
    
    if len(matches) == 0:
        raise ValueError(
            f"Parameter '{param_name}': no column found matching '{column_spec_str}'. "
            f"Available columns: {list(df.columns)}"
        )
    elif len(matches) == 1:
        return df.columns.get_loc(matches[0])
    else:
        raise ValueError(
            f"Parameter '{param_name}': ambiguous column specification '{column_spec_str}'. "
            f"Multiple matches found: {matches}. "
            f"Please use a more specific name or exact column name."
        )


def load_distribution(filepath, freq_column="pgen", weights_column="off"):
    """
    Load a TCR distribution from a TSV file.
    
    Parameters
    ----------
    filepath : str
        Path to TSV file
    freq_column : str or int
        Column name, substring of column name, or index for frequency values (e.g., 'pgen').
        If string: tries exact match first, then substring match (must be unique).
    weights_column : str or int
        Column name, substring, or index for weights, or 'off' for uniform weights.
        If string: tries exact match first, then substring match (must be unique).
        
    Returns
    -------
    values : np.ndarray
        Frequency values (e.g., pgen values)
    weights : np.ndarray
        Weights for each value (uniform if weights_column='off')
        
    Raises
    ------
    ValueError
        If column specification is ambiguous or not found
    """
    df = pd.read_csv(filepath, sep='\t')
    
    # Get frequency column
    freq_idx = _find_column_index(df, freq_column, 'freq_column')
    values = df.iloc[:, freq_idx].values
    
    # Filter positive values
    valid_mask = values > 0
    values = values[valid_mask]
    
    # Get weights
    if weights_column == "off":
        weights = np.ones(len(values)) / len(values)
    else:
        weight_idx = _find_column_index(df, weights_column, 'weights_column')
        weights = df.iloc[:, weight_idx].values[valid_mask]
        weights = weights / weights.sum()
    
    return values, weights


def compute_cost_matrix(support1, support2, metric='log_l1'):
    """
    Compute cost matrix between two supports.
    
    Parameters
    ----------
    support1 : np.ndarray
        First support points (e.g., pgen values)
    support2 : np.ndarray
        Second support points
    metric : str
        Distance metric, options:
        - 'log_l1': L1 distance in log space (default, robust for wide ranges)
        - 'l1': L1 distance in original space
        - 'l2': L2 (Euclidean) distance
        
    Returns
    -------
    cost_matrix : np.ndarray
        Cost matrix of shape (len(support1), len(support2))
    """
    if metric == 'log_l1':
        # L1 distance in log space (robust for pgen ranges)
        log_s1 = np.log(support1.reshape(-1, 1))
        log_s2 = np.log(support2.reshape(1, -1))
        return np.abs(log_s1 - log_s2)
    
    elif metric == 'l1':
        # L1 distance in original space
        s1 = support1.reshape(-1, 1)
        s2 = support2.reshape(1, -1)
        return np.abs(s1 - s2)
    
    elif metric == 'l2':
        # L2 (Euclidean) distance
        s1 = support1.reshape(-1, 1)
        s2 = support2.reshape(1, -1)
        return np.sqrt((s1 - s2)**2)
    
    else:
        raise ValueError(f"Unknown metric: {metric}")


def compute_wasserstein_distance(values1, weights1, values2, weights2, 
                                  metric='log_l1', method='emd'):
    """
    Compute Wasserstein distance between two distributions.
    
    This is the core function used across all scripts to ensure
    consistent distance computation.
    
    Parameters
    ----------
    values1 : np.ndarray
        Support points of first distribution (e.g., pgen values)
    weights1 : np.ndarray
        Weights of first distribution (must sum to 1)
    values2 : np.ndarray
        Support points of second distribution
    weights2 : np.ndarray
        Weights of second distribution (must sum to 1)
    metric : str
        Distance metric for cost matrix (default: 'log_l1')
    method : str
        OT solver method:
        - 'emd': Exact EMD solver (default)
        - 'sinkhorn': Entropic regularization (faster, approximate)
        
    Returns
    -------
    distance : float
        Wasserstein distance between the two distributions
    """
    # Ensure weights sum to 1
    weights1 = weights1 / weights1.sum()
    weights2 = weights2 / weights2.sum()
    
    # Compute cost matrix
    cost_matrix = compute_cost_matrix(values1, values2, metric=metric)
    
    # Compute distance
    if method == 'emd':
        distance = ot.emd2(weights1, weights2, cost_matrix)
    elif method == 'sinkhorn':
        distance = ot.sinkhorn2(weights1, weights2, cost_matrix, reg=0.01)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return distance


def discretize_distribution(values, weights, grid):
    """
    Discretize a distribution onto a fixed grid.
    
    Parameters
    ----------
    values : np.ndarray
        Support points of the distribution
    weights : np.ndarray
        Weights at each support point
    grid : np.ndarray
        Grid points for discretization
        
    Returns
    -------
    discretized_weights : np.ndarray
        Weights on the grid (same length as grid)
    """
    # Create bins centered around grid points
    # Extend grid boundaries
    bin_edges = np.concatenate([
        [grid[0] / 2],
        (grid[:-1] + grid[1:]) / 2,
        [grid[-1] * 2]
    ])
    
    # Assign each value to nearest bin
    discretized = np.zeros(len(grid))
    for val, weight in zip(values, weights):
        bin_idx = np.searchsorted(bin_edges, val) - 1
        bin_idx = np.clip(bin_idx, 0, len(grid) - 1)
        discretized[bin_idx] += weight
    
    # Normalize
    if discretized.sum() > 0:
        discretized = discretized / discretized.sum()
    
    return discretized


def create_common_grid(values_list, n_grid=200, log_space=True):
    """
    Create a common grid covering all distributions.
    
    Parameters
    ----------
    values_list : list of np.ndarray
        List of value arrays from multiple distributions
    n_grid : int
        Number of grid points
    log_space : bool
        If True, use log-spaced grid (recommended for pgen)
        
    Returns
    -------
    grid : np.ndarray
        Grid points
    """
    # Find global range
    all_values = np.concatenate(values_list)
    vmin, vmax = all_values.min(), all_values.max()
    
    if log_space:
        grid = np.logspace(np.log10(vmin), np.log10(vmax), n_grid)
    else:
        grid = np.linspace(vmin, vmax, n_grid)
    
    return grid


def load_barycenter(filepath):
    """
    Load a precomputed barycenter from .npz file.
    
    Parameters
    ----------
    filepath : str
        Path to barycenter .npz file
        
    Returns
    -------
    grid : np.ndarray
        Support points (grid)
    barycenter : np.ndarray
        Weights at each support point
    """
    data = np.load(filepath)
    grid = data['grid']
    barycenter = data['barycenter']
    return grid, barycenter


def extend_grid_if_needed(grid, weights, new_data_min, new_data_max):
    """
    Extend grid and weights if new data falls outside the current grid range.
    Maintains logarithmic spacing and preserves original grid points exactly.
    New points are added with zero weight.
    
    This is useful when computing distance from a distribution to a barycenter
    that was computed without that distribution, and the new distribution
    extends beyond the original grid range.
    
    Parameters
    ----------
    grid : np.ndarray
        Current grid points (log-spaced)
    weights : np.ndarray
        Current barycenter weights
    new_data_min : float
        Minimum value in new data
    new_data_max : float
        Maximum value in new data
        
    Returns
    -------
    extended_grid : np.ndarray
        Extended grid (or original if no extension needed)
    extended_weights : np.ndarray
        Extended weights (with zeros in new regions)
    """
    # Check if extension is needed
    needs_lower = new_data_min < grid[0]
    needs_upper = new_data_max > grid[-1]
    
    if not needs_lower and not needs_upper:
        return grid, weights
    
    # Calculate the log-spacing step from original grid
    log_grid = np.log(grid)
    log_step = np.mean(np.diff(log_grid))
    
    # Extend below if needed
    lower_grid = []
    lower_weights = []
    if needs_lower:
        log_min = np.log(new_data_min)
        log_first = log_grid[0]
        n_below = int(np.ceil((log_first - log_min) / log_step))
        lower_grid = np.exp(np.arange(log_first - n_below * log_step, log_first, log_step))
        lower_weights = np.zeros(len(lower_grid))
    
    # Extend above if needed
    upper_grid = []
    upper_weights = []
    if needs_upper:
        log_max = np.log(new_data_max)
        log_last = log_grid[-1]
        n_above = int(np.ceil((log_max - log_last) / log_step))
        upper_grid = np.exp(np.arange(log_last + log_step, log_last + (n_above + 1) * log_step, log_step))
        upper_weights = np.zeros(len(upper_grid))
    
    # Combine all parts
    extended_grid = np.concatenate([lower_grid, grid, upper_grid])
    extended_weights = np.concatenate([lower_weights, weights, upper_weights])
    
    return extended_grid, extended_weights
