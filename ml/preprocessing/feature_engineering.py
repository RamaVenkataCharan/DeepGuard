"""
Feature Engineering Module

Extracts statistical and weather-correlated features from consumption
data to augment the deep learning model inputs.
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

logger = logging.getLogger(__name__)


def compute_rolling_stats(
    consumption: np.ndarray,
    windows: list = None,
) -> dict:
    """
    Compute rolling statistical features over multiple window sizes.

    Parameters
    ----------
    consumption : np.ndarray
        1D cleaned consumption array.
    windows : list of int
        Rolling window sizes (e.g., [3, 7, 14]).

    Returns
    -------
    dict
        Feature name → np.ndarray of same length as consumption.
    """
    if windows is None:
        windows = [3, 7, 14]

    series = pd.Series(consumption)
    features = {}

    for w in windows:
        rolling = series.rolling(window=w, min_periods=1)
        features[f"rolling_mean_{w}d"] = rolling.mean().values
        features[f"rolling_std_{w}d"] = rolling.std().fillna(0).values
        features[f"rolling_min_{w}d"] = rolling.min().values
        features[f"rolling_max_{w}d"] = rolling.max().values

    return features


def compute_consumption_stats(consumption: np.ndarray) -> dict:
    """
    Compute global statistical features for a customer's consumption series.

    Returns scalar features useful for risk scoring.
    """
    clean = consumption[~np.isnan(consumption)]

    if len(clean) == 0:
        return {
            "mean": 0.0, "std": 0.0, "median": 0.0,
            "skewness": 0.0, "kurtosis": 0.0,
            "cv": 0.0, "iqr": 0.0,
            "zero_fraction": 1.0, "range": 0.0,
            "trend_slope": 0.0,
        }

    q1, q3 = np.percentile(clean, [25, 75])
    mean = np.mean(clean)
    std = np.std(clean)

    # Trend: slope of linear fit
    x = np.arange(len(clean))
    if len(clean) > 1:
        slope, _, _, _, _ = sp_stats.linregress(x, clean)
    else:
        slope = 0.0

    return {
        "mean": float(mean),
        "std": float(std),
        "median": float(np.median(clean)),
        "skewness": float(sp_stats.skew(clean)) if len(clean) > 2 else 0.0,
        "kurtosis": float(sp_stats.kurtosis(clean)) if len(clean) > 3 else 0.0,
        "cv": float(std / mean) if mean > 0 else 0.0,
        "iqr": float(q3 - q1),
        "zero_fraction": float((clean == 0).mean()),
        "range": float(np.max(clean) - np.min(clean)),
        "trend_slope": float(slope),
    }


def compute_change_features(consumption: np.ndarray) -> dict:
    """
    Compute day-over-day and period-over-period change features.

    These are particularly useful for detecting sudden consumption drops
    that may indicate theft.
    """
    if len(consumption) < 2:
        return {
            "daily_change_mean": 0.0,
            "daily_change_std": 0.0,
            "max_daily_drop": 0.0,
            "n_significant_drops": 0,
            "drop_ratio": 0.0,
        }

    daily_change = np.diff(consumption)
    daily_pct_change = np.where(
        consumption[:-1] != 0,
        daily_change / consumption[:-1],
        0.0,
    )

    # Significant drop: consumption drops by >50% in a day
    significant_drops = daily_pct_change < -0.5

    return {
        "daily_change_mean": float(np.mean(daily_change)),
        "daily_change_std": float(np.std(daily_change)),
        "max_daily_drop": float(np.min(daily_change)),
        "max_daily_pct_drop": float(np.min(daily_pct_change)),
        "n_significant_drops": int(significant_drops.sum()),
        "drop_ratio": float(significant_drops.mean()),
    }


def compute_periodicity_features(consumption: np.ndarray) -> dict:
    """
    Extract periodicity features using autocorrelation.

    Theft customers often show disrupted weekly/monthly patterns.
    """
    if len(consumption) < 14:
        return {
            "autocorr_7d": 0.0,
            "autocorr_14d": 0.0,
            "periodicity_strength": 0.0,
        }

    series = pd.Series(consumption)

    autocorr_7 = series.autocorrelation(lag=7) if len(series) > 7 else 0.0
    autocorr_14 = series.autocorrelation(lag=14) if len(series) > 14 else 0.0

    # Handle NaN autocorrelations
    autocorr_7 = 0.0 if np.isnan(autocorr_7) else autocorr_7
    autocorr_14 = 0.0 if np.isnan(autocorr_14) else autocorr_14

    return {
        "autocorr_7d": float(autocorr_7),
        "autocorr_14d": float(autocorr_14),
        "periodicity_strength": float(abs(autocorr_7) + abs(autocorr_14)) / 2,
    }


def compute_weather_features(
    temperature: np.ndarray,
    humidity: np.ndarray,
    consumption: np.ndarray,
) -> dict:
    """
    Compute weather-correlated features.

    High correlation between consumption and temperature is normal
    (heating/cooling). Low correlation may indicate tampered readings.
    """
    features = {}

    # Temperature-consumption correlation
    clean_mask = ~(np.isnan(temperature) | np.isnan(consumption))
    if clean_mask.sum() > 5:
        corr = np.corrcoef(temperature[clean_mask], consumption[clean_mask])[0, 1]
        features["temp_consumption_corr"] = float(corr) if not np.isnan(corr) else 0.0
    else:
        features["temp_consumption_corr"] = 0.0

    # Heating/Cooling Degree Days (base 18°C)
    if len(temperature) > 0:
        clean_temp = temperature[~np.isnan(temperature)]
        features["hdd"] = float(np.sum(np.maximum(18 - clean_temp, 0)))
        features["cdd"] = float(np.sum(np.maximum(clean_temp - 24, 0)))
    else:
        features["hdd"] = 0.0
        features["cdd"] = 0.0

    # Humidity-consumption correlation
    if clean_mask.sum() > 5:
        corr_h = np.corrcoef(humidity[clean_mask], consumption[clean_mask])[0, 1]
        features["humidity_consumption_corr"] = float(corr_h) if not np.isnan(corr_h) else 0.0
    else:
        features["humidity_consumption_corr"] = 0.0

    return features


def engineer_features(
    df: pd.DataFrame,
    consumption_col: str = "consumption",
    weather_data: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Run the full feature engineering pipeline on a dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Must have 'customer_id', 'consumption' (np.ndarray), 'label'.
    weather_data : pd.DataFrame, optional
        Weather data with temperature, humidity columns.

    Returns
    -------
    pd.DataFrame
        Original DataFrame with additional feature columns.
    """
    df = df.copy()

    stat_features = []
    change_features = []

    for _, row in df.iterrows():
        consumption = row[consumption_col]

        stats = compute_consumption_stats(consumption)
        changes = compute_change_features(consumption)

        stat_features.append(stats)
        change_features.append(changes)

    # Add scalar features as columns
    stat_df = pd.DataFrame(stat_features)
    change_df = pd.DataFrame(change_features)

    for col in stat_df.columns:
        df[f"stat_{col}"] = stat_df[col].values
    for col in change_df.columns:
        df[f"change_{col}"] = change_df[col].values

    logger.info(
        "Engineered %d features for %d customers",
        len(stat_df.columns) + len(change_df.columns),
        len(df),
    )

    return df
