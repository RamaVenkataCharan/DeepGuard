"""
Normalization Module

Per-customer scaling using Min-Max or Z-Score normalization.
Persists scalers for inference-time consistency.
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import joblib
import numpy as np

from ml.config import ARTIFACTS_DIR, NORMALIZATION_METHOD, SCALER_FILENAME

logger = logging.getLogger(__name__)


class CustomerScaler:
    """
    Per-customer normalization that stores min/max or mean/std
    for each customer, enabling consistent scaling at inference time.
    """

    def __init__(self, method: str = NORMALIZATION_METHOD):
        """
        Parameters
        ----------
        method : str
            'minmax' for Min-Max [0, 1] scaling or 'zscore' for
            standardization (zero mean, unit variance).
        """
        if method not in ("minmax", "zscore"):
            raise ValueError(f"Unsupported method: {method}. Use 'minmax' or 'zscore'.")
        self.method = method
        self.params: Dict[int, dict] = {}
        self._is_fitted = False

    def fit(self, customer_id: int, values: np.ndarray) -> None:
        """Compute scaling parameters for a single customer."""
        clean = values[~np.isnan(values)]
        if len(clean) == 0:
            self.params[customer_id] = {"min": 0.0, "max": 1.0, "mean": 0.0, "std": 1.0}
            return

        self.params[customer_id] = {
            "min": float(np.min(clean)),
            "max": float(np.max(clean)),
            "mean": float(np.mean(clean)),
            "std": float(np.std(clean)) if np.std(clean) > 0 else 1.0,
        }
        self._is_fitted = True

    def transform(self, customer_id: int, values: np.ndarray) -> np.ndarray:
        """Scale values using stored parameters."""
        if customer_id not in self.params:
            logger.warning(
                "Customer %d not fitted; using global fallback normalization.",
                customer_id,
            )
            return self._fallback_transform(values)

        p = self.params[customer_id]
        result = values.astype(np.float32).copy()

        if self.method == "minmax":
            range_val = p["max"] - p["min"]
            if range_val == 0:
                return np.zeros_like(result)
            result = (result - p["min"]) / range_val
            result = np.clip(result, 0, 1)
        else:  # zscore
            result = (result - p["mean"]) / p["std"]

        return result

    def inverse_transform(self, customer_id: int, values: np.ndarray) -> np.ndarray:
        """Reverse the scaling transformation."""
        if customer_id not in self.params:
            return values

        p = self.params[customer_id]
        result = values.astype(np.float32).copy()

        if self.method == "minmax":
            range_val = p["max"] - p["min"]
            result = result * range_val + p["min"]
        else:
            result = result * p["std"] + p["mean"]

        return result

    def fit_transform(self, customer_id: int, values: np.ndarray) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(customer_id, values)
        return self.transform(customer_id, values)

    def _fallback_transform(self, values: np.ndarray) -> np.ndarray:
        """Global normalization when customer-specific params unavailable."""
        clean = values[~np.isnan(values)]
        if len(clean) == 0:
            return np.zeros_like(values)

        if self.method == "minmax":
            vmin, vmax = np.min(clean), np.max(clean)
            if vmax - vmin == 0:
                return np.zeros_like(values)
            return (values - vmin) / (vmax - vmin)
        else:
            mean, std = np.mean(clean), np.std(clean)
            if std == 0:
                return np.zeros_like(values)
            return (values - mean) / std

    def save(self, filepath: Optional[str] = None) -> str:
        """Persist scaler to disk."""
        if filepath is None:
            filepath = str(ARTIFACTS_DIR / SCALER_FILENAME)

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "method": self.method,
            "params": self.params,
        }, filepath)
        logger.info("Saved scaler to %s (%d customers)", filepath, len(self.params))
        return filepath

    @classmethod
    def load(cls, filepath: Optional[str] = None) -> "CustomerScaler":
        """Load a persisted scaler."""
        if filepath is None:
            filepath = str(ARTIFACTS_DIR / SCALER_FILENAME)

        data = joblib.load(filepath)
        scaler = cls(method=data["method"])
        scaler.params = data["params"]
        scaler._is_fitted = True
        logger.info("Loaded scaler from %s (%d customers)", filepath, len(scaler.params))
        return scaler

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted and len(self.params) > 0


def normalize_dataset(
    df,
    consumption_col: str = "consumption",
    customer_id_col: str = "customer_id",
    method: str = NORMALIZATION_METHOD,
    scaler: Optional[CustomerScaler] = None,
    fit: bool = True,
) -> Tuple:
    """
    Normalize all consumption series in a dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Must have customer_id and consumption columns.
    method : str
        'minmax' or 'zscore'.
    scaler : CustomerScaler, optional
        Pre-fitted scaler. If None and fit=True, creates a new one.
    fit : bool
        If True, fit the scaler on the data. If False, use existing.

    Returns
    -------
    Tuple[pd.DataFrame, CustomerScaler]
        Normalized DataFrame and the fitted scaler.
    """
    df = df.copy()

    if scaler is None:
        scaler = CustomerScaler(method=method)

    normalized = []
    for _, row in df.iterrows():
        cid = row[customer_id_col]
        consumption = row[consumption_col]

        if fit:
            norm = scaler.fit_transform(cid, consumption)
        else:
            norm = scaler.transform(cid, consumption)

        normalized.append(norm)

    df[consumption_col] = normalized
    logger.info("Normalized %d customers (method=%s)", len(df), method)

    return df, scaler
