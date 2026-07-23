"""
Unit Tests for DeepGuard ML Preprocessing Pipeline.
"""
import pytest
import numpy as np
import pandas as pd
from ml.preprocessing.cleaning import (
    interpolate_missing,
    detect_outliers_iqr,
    detect_outliers_zscore,
    handle_outliers,
    handle_zero_consumption,
    clean_consumption_series
)
from ml.preprocessing.normalization import CustomerScaler
from ml.preprocessing.sequence_builder import create_sequences, split_dataset
from ml.preprocessing.feature_engineering import compute_consumption_stats

def test_interpolate_missing():
    # Sequence with missing value
    seq = np.array([10.0, 12.0, np.nan, 16.0, 18.0])
    res = interpolate_missing(seq, method="linear")
    assert not np.isnan(res).any()
    assert res[2] == 14.0

def test_detect_outliers():
    # Base sequence with one outlier
    seq = np.array([10.0, 11.0, 12.0, 10.5, 95.0, 11.2, 10.8])
    outliers = detect_outliers_iqr(seq, multiplier=1.5)
    assert outliers[4] == True
    assert outliers[0] == False

def test_customer_scaler():
    scaler = CustomerScaler(method="minmax")
    seq = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    
    scaler.fit(1, seq)
    norm = scaler.transform(1, seq)
    
    # Check boundaries
    assert norm[0] == 0.0
    assert norm[-1] == 1.0
    
    # Reverse transform
    rev = scaler.inverse_transform(1, norm)
    assert np.allclose(rev, seq)

def test_sequence_builder():
    seq = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    seqs = create_sequences(seq, sequence_length=4, step=1)
    
    # Check sliding window size and dimensions
    assert seqs.shape == (3, 4, 1)
    assert np.array_equal(seqs[0].ravel(), [1.0, 2.0, 3.0, 4.0])
    assert np.array_equal(seqs[2].ravel(), [3.0, 4.0, 5.0, 6.0])

def test_consumption_stats():
    seq = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    stats = compute_consumption_stats(seq)
    
    assert stats["mean"] == 30.0
    assert stats["median"] == 30.0
    assert stats["range"] == 40.0
