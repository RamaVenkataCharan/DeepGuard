"""
Data Cleaning Module

Handles missing value imputation, outlier detection and removal,
and zero-consumption handling for smart meter data.
"""
import logging
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from ml.config import OUTLIER_IQR_MULTIPLIER, OUTLIER_ZSCORE_THRESHOLD

logger = logging.getLogger(__name__)


def interpolate_missing(
    consumption: np.ndarray,
    method: str = "linear",
    max_gap: int = 7,
) -> np.ndarray:
    """
    Interpolate missing (NaN) values in a consumption time series.

    Parameters
    ----------
    consumption : np.ndarray
        1D array of daily consumption values, may contain NaN.
    method : str
        Interpolation method: 'linear', 'ffill', 'cubic'.
    max_gap : int
        Maximum consecutive NaN gap to interpolate; larger gaps are
        filled with the series median.

    Returns
    -------
    np.ndarray
        Cleaned array with no NaN values.
    """
    series = pd.Series(consumption.copy())
    n_missing = series.isna().sum()

    if n_missing == 0:
        return consumption

    if n_missing == len(series):
        logger.warning("Entire series is NaN; returning zeros.")
        return np.zeros_like(consumption)

    # Identify gap lengths
    is_nan = series.isna()
    gap_groups = (is_nan != is_nan.shift()).cumsum()
    gap_lengths = is_nan.groupby(gap_groups).transform("sum")

    # Interpolate small gaps
    small_gap_mask = is_nan & (gap_lengths <= max_gap)
    if small_gap_mask.any():
        if method == "ffill":
            series = series.ffill().bfill()
        else:
            series = series.interpolate(method=method)

    # Fill remaining large gaps with median
    median_val = series.median()
    if np.isnan(median_val):
        median_val = 0.0
    series = series.fillna(median_val)

    logger.debug("Interpolated %d missing values (method=%s)", n_missing, method)
    return series.values.astype(np.float32)


def detect_outliers_iqr(
    consumption: np.ndarray,
    multiplier: float = OUTLIER_IQR_MULTIPLIER,
) -> np.ndarray:
    """
    Detect outliers using the Interquartile Range (IQR) method.

    Returns a boolean mask where True = outlier.
    """
    clean = consumption[~np.isnan(consumption)]
    if len(clean) == 0:
        return np.zeros(len(consumption), dtype=bool)

    q1 = np.percentile(clean, 25)
    q3 = np.percentile(clean, 75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    outlier_mask = (consumption < lower) | (consumption > upper)
    # NaN values are not outliers
    outlier_mask = outlier_mask & ~np.isnan(consumption)

    return outlier_mask


def detect_outliers_zscore(
    consumption: np.ndarray,
    threshold: float = OUTLIER_ZSCORE_THRESHOLD,
) -> np.ndarray:
    """
    Detect outliers using z-score thresholding.

    Returns a boolean mask where True = outlier.
    """
    clean = consumption[~np.isnan(consumption)]
    if len(clean) < 3:
        return np.zeros(len(consumption), dtype=bool)

    mean = np.nanmean(consumption)
    std = np.nanstd(consumption)

    if std == 0:
        return np.zeros(len(consumption), dtype=bool)

    z_scores = np.abs((consumption - mean) / std)
    outlier_mask = z_scores > threshold
    outlier_mask = outlier_mask & ~np.isnan(consumption)

    return outlier_mask


def handle_outliers(
    consumption: np.ndarray,
    method: str = "iqr",
    replace_with: str = "median",
) -> Tuple[np.ndarray, int]:
    """
    Detect and replace outliers in a consumption series.

    Parameters
    ----------
    consumption : np.ndarray
        1D consumption array.
    method : str
        Detection method: 'iqr' or 'zscore'.
    replace_with : str
        Replacement strategy: 'median', 'interpolate', or 'clip'.

    Returns
    -------
    Tuple[np.ndarray, int]
        Cleaned array and count of outliers handled.
    """
    result = consumption.copy()

    if method == "iqr":
        outlier_mask = detect_outliers_iqr(result)
    elif method == "zscore":
        outlier_mask = detect_outliers_zscore(result)
    else:
        raise ValueError(f"Unknown outlier method: {method}")

    n_outliers = outlier_mask.sum()

    if n_outliers == 0:
        return result, 0

    if replace_with == "median":
        median_val = np.nanmedian(result[~outlier_mask])
        result[outlier_mask] = median_val
    elif replace_with == "interpolate":
        result[outlier_mask] = np.nan
        result = interpolate_missing(result)
    elif replace_with == "clip":
        clean = result[~outlier_mask & ~np.isnan(result)]
        if len(clean) > 0:
            lower, upper = np.percentile(clean, [2.5, 97.5])
            result = np.clip(result, lower, upper)
    else:
        raise ValueError(f"Unknown replace_with strategy: {replace_with}")

    logger.debug("Handled %d outliers (method=%s, replace=%s)", n_outliers, method, replace_with)
    return result, n_outliers


def handle_zero_consumption(
    consumption: np.ndarray,
    max_consecutive_zeros: int = 3,
) -> np.ndarray:
    """
    Handle suspicious zero-consumption readings.

    Short zero sequences (1-3 days) are likely legitimate (vacation, etc.).
    Longer sequences may indicate meter issues; mark as NaN for interpolation.
    """
    result = consumption.copy()
    is_zero = result == 0

    if not is_zero.any():
        return result

    # Find consecutive zero runs
    groups = (is_zero != is_zero.shift() if isinstance(is_zero, pd.Series)
              else np.concatenate([[True], is_zero[1:] != is_zero[:-1]]))

    run_starts = np.where(groups)[0] if isinstance(groups, np.ndarray) else [0]

    # Simple approach: replace long zero runs with NaN
    in_run = False
    run_start = 0

    for i in range(len(result)):
        if result[i] == 0:
            if not in_run:
                run_start = i
                in_run = True
        else:
            if in_run:
                run_length = i - run_start
                if run_length > max_consecutive_zeros:
                    result[run_start:i] = np.nan
                in_run = False

    # Handle trailing zeros
    if in_run:
        run_length = len(result) - run_start
        if run_length > max_consecutive_zeros:
            result[run_start:] = np.nan

    return result


def clean_consumption_series(
    consumption: np.ndarray,
    outlier_method: str = "iqr",
    interpolation_method: str = "linear",
) -> np.ndarray:
    """
    Full cleaning pipeline for a single customer's consumption series.

    Steps:
    1. Handle suspicious zero runs
    2. Detect and replace outliers
    3. Interpolate missing values

    Parameters
    ----------
    consumption : np.ndarray
        Raw daily consumption readings.
    outlier_method : str
        'iqr' or 'zscore' for outlier detection.
    interpolation_method : str
        'linear', 'ffill', or 'cubic' for NaN interpolation.

    Returns
    -------
    np.ndarray
        Cleaned consumption series with no NaN or outliers.
    """
    result = consumption.astype(np.float32).copy()

    # Step 1: Zero handling
    result = handle_zero_consumption(result)

    # Step 2: Outlier handling
    result, n_outliers = handle_outliers(result, method=outlier_method)

    # Step 3: Interpolation
    result = interpolate_missing(result, method=interpolation_method)

    return result


def clean_dataset(
    df: pd.DataFrame,
    consumption_col: str = "consumption",
    outlier_method: str = "iqr",
    interpolation_method: str = "linear",
) -> pd.DataFrame:
    """
    Clean all consumption series in a dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Must have a column containing np.ndarray consumption arrays.
    consumption_col : str
        Column name containing consumption arrays.

    Returns
    -------
    pd.DataFrame
        Same DataFrame with cleaned consumption arrays.
    """
    df = df.copy()
    cleaned = []

    for idx, row in df.iterrows():
        raw = row[consumption_col]
        clean = clean_consumption_series(
            raw,
            outlier_method=outlier_method,
            interpolation_method=interpolation_method,
        )
        cleaned.append(clean)

    df[consumption_col] = cleaned
    logger.info("Cleaned %d consumption series", len(df))
    return df
