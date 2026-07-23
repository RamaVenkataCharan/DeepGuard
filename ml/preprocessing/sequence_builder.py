"""
Sequence Builder Module

Generates fixed-length sliding-window sequences from daily consumption
data for input to the Bi-LSTM + Transformer model. Handles train/val/test
splitting with stratification to preserve class balance.
"""
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.model_selection import train_test_split

from ml.config import (
    DEFAULT_SEQUENCE_LENGTH,
    RANDOM_SEED,
    SLIDING_WINDOW_STEP,
    TEST_SIZE,
    VALIDATION_SIZE,
)

logger = logging.getLogger(__name__)


def create_sequences(
    consumption: np.ndarray,
    sequence_length: int = DEFAULT_SEQUENCE_LENGTH,
    step: int = SLIDING_WINDOW_STEP,
) -> np.ndarray:
    """
    Create sliding window sequences from a single consumption series.

    Parameters
    ----------
    consumption : np.ndarray
        1D array of daily consumption values (already cleaned & normalized).
    sequence_length : int
        Number of timesteps per sequence.
    step : int
        Sliding window step size.

    Returns
    -------
    np.ndarray
        Shape (n_sequences, sequence_length, 1).
    """
    if len(consumption) < sequence_length:
        # Pad with zeros if series is shorter than window
        padded = np.zeros(sequence_length, dtype=np.float32)
        padded[-len(consumption):] = consumption
        return padded.reshape(1, sequence_length, 1)

    sequences = []
    for i in range(0, len(consumption) - sequence_length + 1, step):
        seq = consumption[i:i + sequence_length]
        sequences.append(seq)

    if len(sequences) == 0:
        return np.zeros((1, sequence_length, 1), dtype=np.float32)

    result = np.array(sequences, dtype=np.float32)
    return result.reshape(-1, sequence_length, 1)


def create_sequences_with_features(
    consumption: np.ndarray,
    features: Optional[np.ndarray] = None,
    sequence_length: int = DEFAULT_SEQUENCE_LENGTH,
    step: int = SLIDING_WINDOW_STEP,
) -> np.ndarray:
    """
    Create sliding window sequences with additional feature channels.

    Parameters
    ----------
    consumption : np.ndarray
        1D consumption array.
    features : np.ndarray, optional
        Additional features array of shape (n_days, n_features).
        Will be concatenated with consumption channel.
    sequence_length : int
        Window size.
    step : int
        Step size.

    Returns
    -------
    np.ndarray
        Shape (n_sequences, sequence_length, 1 + n_features).
    """
    if features is None:
        return create_sequences(consumption, sequence_length, step)

    n_days = len(consumption)
    n_features = features.shape[1] if features.ndim > 1 else 1

    if features.ndim == 1:
        features = features.reshape(-1, 1)

    # Combine consumption with features
    combined = np.column_stack([consumption.reshape(-1, 1), features[:n_days]])

    if n_days < sequence_length:
        padded = np.zeros((sequence_length, combined.shape[1]), dtype=np.float32)
        padded[-n_days:] = combined
        return padded.reshape(1, sequence_length, -1)

    sequences = []
    for i in range(0, n_days - sequence_length + 1, step):
        seq = combined[i:i + sequence_length]
        sequences.append(seq)

    if len(sequences) == 0:
        return np.zeros((1, sequence_length, combined.shape[1]), dtype=np.float32)

    return np.array(sequences, dtype=np.float32)


def build_dataset(
    df,
    sequence_length: int = DEFAULT_SEQUENCE_LENGTH,
    step: int = SLIDING_WINDOW_STEP,
    consumption_col: str = "consumption",
    label_col: str = "label",
    features_col: Optional[str] = None,
    aggregate: str = "last",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build a complete sequence dataset from the cleaned DataFrame.

    For each customer, generate multiple sequences via sliding window.
    Each sequence inherits the customer's theft label.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned and normalized dataset.
    sequence_length : int
        Window size.
    step : int
        Step size.
    aggregate : str
        How to handle multiple sequences per customer:
        'last' uses only the last sequence, 'all' uses all sequences.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray]
        X (sequences), y (labels), customer_ids
    """
    all_sequences = []
    all_labels = []
    all_customer_ids = []

    for _, row in df.iterrows():
        consumption = row[consumption_col]
        label = row[label_col]
        cid = row.get("customer_id", 0)

        features = row.get(features_col) if features_col and features_col in row.index else None

        if features is not None:
            seqs = create_sequences_with_features(
                consumption, features, sequence_length, step
            )
        else:
            seqs = create_sequences(consumption, sequence_length, step)

        if aggregate == "last":
            # Use only the most recent sequence
            all_sequences.append(seqs[-1:])
            all_labels.extend([label])
            all_customer_ids.extend([cid])
        else:
            # Use all sequences
            all_sequences.append(seqs)
            all_labels.extend([label] * len(seqs))
            all_customer_ids.extend([cid] * len(seqs))

    X = np.concatenate(all_sequences, axis=0)
    y = np.array(all_labels, dtype=np.int32)
    customer_ids = np.array(all_customer_ids)

    logger.info(
        "Built dataset: X=%s, y=%s (%.1f%% positive)",
        X.shape, y.shape, 100 * y.mean(),
    )

    return X, y, customer_ids


def split_dataset(
    X: np.ndarray,
    y: np.ndarray,
    customer_ids: Optional[np.ndarray] = None,
    test_size: float = TEST_SIZE,
    val_size: float = VALIDATION_SIZE,
    random_seed: int = RANDOM_SEED,
    stratify: bool = True,
) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """
    Split dataset into train/validation/test sets with stratification.

    Parameters
    ----------
    X : np.ndarray
        Input sequences.
    y : np.ndarray
        Labels.
    customer_ids : np.ndarray, optional
        Customer IDs (for potential group-based splitting).
    test_size : float
        Fraction for test set.
    val_size : float
        Fraction for validation set (from remaining after test).
    stratify : bool
        Whether to stratify by label.

    Returns
    -------
    Dict with keys 'train', 'val', 'test', each containing (X, y) tuples.
    """
    stratify_y = y if stratify else None

    # First split: train+val vs test
    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_seed,
        stratify=stratify_y,
    )

    # Second split: train vs val
    val_fraction = val_size / (1 - test_size)
    stratify_tv = y_trainval if stratify else None

    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval, y_trainval, test_size=val_fraction,
        random_state=random_seed, stratify=stratify_tv,
    )

    result = {
        "train": (X_train, y_train),
        "val": (X_val, y_val),
        "test": (X_test, y_test),
    }

    logger.info(
        "Split sizes — train: %d, val: %d, test: %d",
        len(y_train), len(y_val), len(y_test),
    )
    for name, (_, labels) in result.items():
        logger.info(
            "  %s: %.1f%% positive", name, 100 * labels.mean() if len(labels) > 0 else 0,
        )

    return result
