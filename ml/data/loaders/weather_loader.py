"""
Weather Data Loader

Loads and merges weather data with consumption data for
weather-aware anomaly detection features.
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def load_weather_data(
    filepath: Optional[str] = None,
    region: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load weather data from CSV.

    Expected columns: date, region, temperature, humidity, wind_speed,
                      pressure, condition

    Parameters
    ----------
    filepath : str, optional
        Path to weather CSV. If None, generates synthetic data.
    region : str, optional
        Filter by region name.

    Returns
    -------
    pd.DataFrame
        Weather data with datetime index.
    """
    if filepath is None:
        from ml.config import DATA_RAW_DIR, WEATHER_FILENAME
        filepath = DATA_RAW_DIR / WEATHER_FILENAME

    filepath = Path(filepath)
    if not filepath.exists():
        logger.warning(
            "Weather data not found at %s. Generating synthetic weather.",
            filepath,
        )
        return generate_synthetic_weather(n_days=1035, seed=42)

    logger.info("Loading weather data from %s", filepath)
    df = pd.read_csv(filepath, parse_dates=["date"])

    if region:
        df = df[df["region"] == region].copy()

    df = df.sort_values("date").reset_index(drop=True)
    return df


def generate_synthetic_weather(
    n_days: int = 1035,
    seed: int = 42,
    start_date: str = "2021-01-01",
) -> pd.DataFrame:
    """
    Generate synthetic weather data with realistic seasonal patterns.

    Simulates a North Indian climate with hot summers, mild winters,
    and a monsoon season.
    """
    rng = np.random.RandomState(seed)
    dates = pd.date_range(start=start_date, periods=n_days, freq="D")

    # Day of year for seasonal patterns
    doy = dates.dayofyear.values.astype(float)

    # Temperature: peaks in June (~45°C), lowest in January (~8°C)
    temp_base = 25 + 15 * np.sin(2 * np.pi * (doy - 100) / 365)
    temp_noise = rng.normal(0, 3, n_days)
    temperature = temp_base + temp_noise

    # Humidity: high during monsoon (Jul-Sep), low in winter
    humidity_base = 50 + 25 * np.sin(2 * np.pi * (doy - 180) / 365)
    humidity_noise = rng.normal(0, 8, n_days)
    humidity = np.clip(humidity_base + humidity_noise, 10, 98)

    # Wind speed
    wind_base = 3 + 2 * np.sin(2 * np.pi * (doy - 90) / 365)
    wind_noise = rng.exponential(1.5, n_days)
    wind_speed = wind_base + wind_noise

    # Pressure
    pressure = 1013 + rng.normal(0, 5, n_days)

    # Weather condition based on humidity and temperature
    conditions = []
    for h, t in zip(humidity, temperature):
        if h > 75:
            conditions.append(rng.choice(["Rain", "Thunderstorm"], p=[0.7, 0.3]))
        elif h > 55:
            conditions.append(rng.choice(["Cloudy", "Haze", "Drizzle"], p=[0.5, 0.3, 0.2]))
        elif t > 40:
            conditions.append(rng.choice(["Clear", "Haze"], p=[0.6, 0.4]))
        else:
            conditions.append(rng.choice(["Clear", "Partly Cloudy", "Fog"], p=[0.5, 0.35, 0.15]))

    df = pd.DataFrame({
        "date": dates,
        "region": "default",
        "temperature": np.round(temperature, 1),
        "humidity": np.round(humidity, 1),
        "wind_speed": np.round(wind_speed, 1),
        "pressure": np.round(pressure, 1),
        "condition": conditions,
    })

    logger.info("Generated %d days of synthetic weather data", n_days)
    return df


def merge_weather_with_consumption(
    consumption_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    date_col: str = "date",
) -> pd.DataFrame:
    """
    Merge weather data with consumption data on date.

    Parameters
    ----------
    consumption_df : pd.DataFrame
        Must have a date/timestamp column.
    weather_df : pd.DataFrame
        Weather data with 'date' column.
    date_col : str
        Name of the date column in consumption_df.

    Returns
    -------
    pd.DataFrame
        Merged DataFrame with weather features.
    """
    consumption_df = consumption_df.copy()
    weather_df = weather_df.copy()

    # Normalize date columns
    if date_col in consumption_df.columns:
        consumption_df[date_col] = pd.to_datetime(consumption_df[date_col]).dt.date
    weather_df["date"] = pd.to_datetime(weather_df["date"]).dt.date

    merged = consumption_df.merge(
        weather_df[["date", "temperature", "humidity", "wind_speed", "condition"]],
        left_on=date_col,
        right_on="date",
        how="left",
    )

    # Fill missing weather data with forward fill then backward fill
    weather_cols = ["temperature", "humidity", "wind_speed"]
    merged[weather_cols] = merged[weather_cols].ffill().bfill()

    logger.info("Merged weather data: %d rows", len(merged))
    return merged
