"""
SGCC Smart Meter Dataset Loader

Loads the State Grid Corporation of China (SGCC) electricity theft detection
dataset. Expected format: each row is a customer with columns:
  - FLAG: binary label (0 = normal, 1 = theft)
  - Remaining columns: daily consumption readings (kWh)

Also includes a synthetic data generator for development/testing.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def load_sgcc_dataset(
    filepath: Optional[str] = None,
    max_customers: Optional[int] = None,
) -> pd.DataFrame:
    """
    Load the SGCC dataset from a CSV file.

    Parameters
    ----------
    filepath : str, optional
        Path to the SGCC CSV file. If None, uses config default.
    max_customers : int, optional
        Limit the number of customers loaded (for debugging).

    Returns
    -------
    pd.DataFrame
        Columns: customer_id (int), label (int 0/1), consumption (np.ndarray)
    """
    if filepath is None:
        from ml.config import DATA_RAW_DIR, SGCC_FILENAME
        filepath = DATA_RAW_DIR / SGCC_FILENAME

    filepath = Path(filepath)
    if not filepath.exists():
        logger.warning(
            "SGCC dataset not found at %s. Generating synthetic data.", filepath
        )
        return generate_synthetic_sgcc(n_customers=1000, n_days=1035, seed=42)

    logger.info("Loading SGCC dataset from %s", filepath)
    df = pd.read_csv(filepath)

    if max_customers:
        df = df.head(max_customers)

    # Expect FLAG column as the label, rest are daily readings
    if "FLAG" in df.columns:
        labels = df["FLAG"].values.astype(int)
        consumption_cols = [c for c in df.columns if c != "FLAG"]
    else:
        # Assume first column is label
        labels = df.iloc[:, 0].values.astype(int)
        consumption_cols = df.columns[1:]

    consumption = df[consumption_cols].values.astype(np.float32)

    result = pd.DataFrame({
        "customer_id": np.arange(len(labels)),
        "label": labels,
        "consumption": [consumption[i] for i in range(len(labels))],
    })

    logger.info(
        "Loaded %d customers: %d normal, %d theft (%.1f%% theft rate)",
        len(result),
        (labels == 0).sum(),
        (labels == 1).sum(),
        100 * (labels == 1).mean(),
    )

    return result


def generate_synthetic_sgcc(
    n_customers: int = 1000,
    n_days: int = 1035,
    theft_ratio: float = 0.1,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic data mimicking the SGCC dataset structure.

    Normal customers: consistent daily consumption with natural variance.
    Theft customers: periodic drops to near-zero or abnormal patterns.

    Parameters
    ----------
    n_customers : int
        Number of customers to generate.
    n_days : int
        Number of daily consumption readings per customer.
    theft_ratio : float
        Fraction of customers labeled as theft.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Same structure as load_sgcc_dataset output.
    """
    rng = np.random.RandomState(seed)
    n_theft = int(n_customers * theft_ratio)
    n_normal = n_customers - n_theft
    labels = np.array([0] * n_normal + [1] * n_theft)

    consumptions = []

    # --- Normal customers ---
    for _ in range(n_normal):
        base = rng.uniform(10, 50)
        # Weekly seasonality
        weekly = 2 * np.sin(2 * np.pi * np.arange(n_days) / 7)
        # Yearly seasonality (more consumption in summer/winter)
        yearly = 5 * np.sin(2 * np.pi * np.arange(n_days) / 365)
        noise = rng.normal(0, base * 0.1, n_days)
        series = base + weekly + yearly + noise
        series = np.clip(series, 0, None)
        # Random missing values (~2% of days)
        missing_mask = rng.random(n_days) < 0.02
        series[missing_mask] = np.nan
        consumptions.append(series.astype(np.float32))

    # --- Theft customers ---
    for _ in range(n_theft):
        base = rng.uniform(15, 60)
        weekly = 2 * np.sin(2 * np.pi * np.arange(n_days) / 7)
        yearly = 5 * np.sin(2 * np.pi * np.arange(n_days) / 365)
        noise = rng.normal(0, base * 0.1, n_days)
        series = base + weekly + yearly + noise
        series = np.clip(series, 0, None)

        # Theft patterns: random periods of reduced consumption
        pattern = rng.choice(["periodic_drop", "gradual_decrease", "sudden_zero"])

        if pattern == "periodic_drop":
            # Random weeks where consumption drops to 10-30% of normal
            n_theft_periods = rng.randint(3, 10)
            for _ in range(n_theft_periods):
                start = rng.randint(0, n_days - 30)
                duration = rng.randint(3, 14)
                end = min(start + duration, n_days)
                series[start:end] *= rng.uniform(0.1, 0.3)

        elif pattern == "gradual_decrease":
            # Slow decrease over time
            theft_start = rng.randint(n_days // 4, n_days // 2)
            decay = np.linspace(1.0, rng.uniform(0.15, 0.4), n_days - theft_start)
            series[theft_start:] *= decay

        elif pattern == "sudden_zero":
            # Sudden drops to near-zero
            n_drops = rng.randint(5, 20)
            for _ in range(n_drops):
                start = rng.randint(0, n_days - 7)
                duration = rng.randint(1, 5)
                end = min(start + duration, n_days)
                series[start:end] = rng.uniform(0, 2, end - start)

        # Also add some missing values
        missing_mask = rng.random(n_days) < 0.03
        series[missing_mask] = np.nan
        consumptions.append(series.astype(np.float32))

    # Shuffle
    perm = rng.permutation(n_customers)
    labels = labels[perm]
    consumptions = [consumptions[i] for i in perm]

    result = pd.DataFrame({
        "customer_id": np.arange(n_customers),
        "label": labels,
        "consumption": consumptions,
    })

    logger.info(
        "Generated synthetic SGCC data: %d customers (%d theft, %.1f%%)",
        n_customers,
        n_theft,
        100 * theft_ratio,
    )

    return result


def save_synthetic_to_csv(
    output_path: str,
    n_customers: int = 1000,
    n_days: int = 1035,
    theft_ratio: float = 0.1,
    seed: int = 42,
) -> str:
    """
    Generate and save synthetic SGCC data as a CSV file for external use.

    The CSV format matches the real SGCC dataset:
    - First column: FLAG (0/1)
    - Remaining columns: daily consumption values
    """
    df = generate_synthetic_sgcc(n_customers, n_days, theft_ratio, seed)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to SGCC CSV format
    consumption_matrix = np.vstack(df["consumption"].values)
    day_cols = [f"day_{i}" for i in range(consumption_matrix.shape[1])]
    csv_df = pd.DataFrame(consumption_matrix, columns=day_cols)
    csv_df.insert(0, "FLAG", df["label"].values)

    csv_df.to_csv(output_path, index=False)
    logger.info("Saved synthetic data to %s", output_path)

    return str(output_path)
