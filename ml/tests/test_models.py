"""
Unit Tests for DeepGuard ML Model Components.
"""
import pytest
import numpy as np
from ml.models.bilstm_model import build_bilstm_branch
from ml.models.transformer_model import build_transformer_branch
from ml.models.fusion_model import build_fusion_model
from ml.models.risk_score import calculate_risk_score

def test_bilstm_branch_shape():
    input_shape = (14, 1)
    model = build_bilstm_branch(input_shape)
    
    # Verify input and output dimensions
    assert model.input_shape == (None, 14, 1)
    assert model.output_shape == (None, 64)

def test_transformer_branch_shape():
    input_shape = (14, 1)
    model = build_transformer_branch(input_shape)
    
    # Verify input and output dimensions
    assert model.input_shape == (None, 14, 1)
    assert model.output_shape == (None, 64)

def test_fusion_model_shape():
    input_shape = (14, 1)
    model = build_fusion_model(input_shape)
    
    # Verify complete model dimensions
    assert model.input_shape == (None, 14, 1)
    assert model.output_shape == (None, 1)

def test_risk_score_mapping():
    # Low probability mapping
    low_res = calculate_risk_score(0.10)
    assert low_res["risk_score"] <= 25
    assert low_res["risk_level"] == "low"
    
    # Critical probability mapping
    critical_res = calculate_risk_score(0.85)
    assert critical_res["risk_score"] >= 76
    assert critical_res["risk_level"] == "critical"
    
    # Volatility / statistical adjustments
    stats = {"zero_fraction": 0.45, "cv": 2.0}
    adjusted_res = calculate_risk_score(0.55, stats)
    baseline_res = calculate_risk_score(0.55)
    
    assert adjusted_res["risk_score"] > baseline_res["risk_score"]
