"""
DeepGuard Electricity Theft Risk Scoring Engine
===============================================
Converts raw model probability scores (0.0 - 1.0) into non-linear, threshold-aligned
0-100 Risk Scores for utility field inspection prioritization.

Threshold Alignment Logic:
- Linear 0-100 scaling is naive because probabilities above decision threshold tau* represent high risk.
- Piece-wise non-linear scaling maps p = tau* to Risk Score = 50.
- p in [0, tau*): Risk Score = 50 * (p / tau*)^1.2  (dampens low-level noise)
- p in [tau*, 1.0]: Risk Score = 50 + 50 * ((p - tau*) / (1.0 - tau*))^0.8 (accelerates high-risk alerts)

Categories:
- 0 - 25: Low Risk (Green)
- 26 - 50: Medium Risk (Yellow)
- 51 - 75: High Risk (Orange) -> Triggers Investigation Alert
- 76 - 100: Critical Risk (Red) -> Triggers Immediate Inspection Alert

Author: Senior ML Engineer (DeepGuard Project)
"""

import math
from typing import Dict, Any, Tuple, Optional, List
import numpy as np


def convert_probability_to_risk_score(
    probability: float,
    tau_val: float = 0.48,
    gamma: float = 1.2,
    beta: float = 0.8
) -> int:
    """
    Converts raw sigmoid theft probability (0.0 - 1.0) to threshold-aligned 0-100 Risk Score.

    Args:
        probability (float): Raw probability output from hybrid model.
        tau_val (float): Validation-selected decision threshold.
        gamma (float): Low-probability damping exponent (>= 1.0).
        beta (float): High-probability acceleration exponent (<= 1.0).

    Returns:
        int: Risk Score integer between 0 and 100.
    """
    # Clamp probability to valid range
    p = max(0.0, min(1.0, float(probability)))
    tau = max(0.05, min(0.95, float(tau_val)))

    if p < tau:
        # Non-linear damping for sub-threshold probabilities (0 to 50)
        norm_p = p / tau
        score = 50.0 * (norm_p ** gamma)
    else:
        # Non-linear acceleration for super-threshold probabilities (50 to 100)
        norm_p = (p - tau) / (1.0 - tau + 1e-8)
        score = 50.0 + (50.0 * (norm_p ** beta))

    # Round and clamp to integer 0-100
    risk_score = int(round(max(0.0, min(100.0, score))))
    return risk_score


def get_risk_level_category(risk_score: int) -> Tuple[str, str]:
    """
    Maps 0-100 Risk Score to risk category string and severity color badge.

    Args:
        risk_score (int): Risk Score between 0 and 100.

    Returns:
        Tuple[str, str]: (risk_level, severity_badge)
            e.g. ("low", "info"), ("medium", "warning"), ("high", "high"), ("critical", "critical")
    """
    if risk_score <= 25:
        return "low", "info"
    elif risk_score <= 50:
        return "medium", "warning"
    elif risk_score <= 75:
        return "high", "high"
    else:
        return "critical", "critical"


def generate_risk_explanations(
    probability: float,
    risk_score: int,
    feature_vector: Optional[np.ndarray] = None,
    feature_names: Optional[List[str]] = None
) -> List[str]:
    """
    Generates human-readable actionable explanation strings for utility auditors.

    Feature vector index mapping (if provided):
    [0: mean, 1: std, 2: min, 3: max, 4: skewness, 5: kurtosis, 6: dod_delta, 7: ratio]
    """
    explanations = []

    if risk_score >= 76:
        explanations.append(f"CRITICAL ANOMALY: Model detected {probability:.1%} probability of meter tampering.")
    elif risk_score >= 51:
        explanations.append(f"HIGH RISK: Consumption pattern matches electricity theft signatures ({probability:.1%} prob).")
    elif risk_score >= 26:
        explanations.append(f"MODERATE ANOMALY: Minor variance in load profile detected.")
    else:
        explanations.append("NORMAL PATTERN: Standard residential/commercial load profile.")

    if feature_vector is not None and len(feature_vector) >= 8:
        mean_val = feature_vector[0]
        std_val = feature_vector[1]
        skew_val = feature_vector[4]
        kurt_val = feature_vector[5]
        dod_delta = feature_vector[6]
        wknd_ratio = feature_vector[7]

        if dod_delta > 0.35:
            explanations.append(f"Sharp Day-over-Day consumption volatility detected (Delta: {dod_delta:.2f}).")
        if abs(kurt_val) > 2.0:
            explanations.append(f"Extreme consumption spike/drop tail anomaly (Kurtosis: {kurt_val:.2f}).")
        if skew_val < -1.0:
            explanations.append(f"Sudden sustained reduction in daily consumption (Skewness: {skew_val:.2f}).")
        if wknd_ratio < 0.5 or wknd_ratio > 2.0:
            explanations.append(f"Abnormal weekend vs weekday load ratio ({wknd_ratio:.2f}x).")

    return explanations


def compute_customer_risk_profile(
    probability: float,
    feature_vector: Optional[np.ndarray] = None,
    tau_val: float = 0.48
) -> Dict[str, Any]:
    """
    Complete inference risk assessment helper.

    Returns dictionary payload suitable for database storage and API response.
    """
    risk_score = convert_probability_to_risk_score(probability, tau_val=tau_val)
    risk_level, severity = get_risk_level_category(risk_score)
    explanations = generate_risk_explanations(probability, risk_score, feature_vector)

    return {
        "raw_probability": float(probability),
        "decision_threshold": float(tau_val),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "severity": severity,
        "is_alert_triggered": risk_score >= 51,
        "explanations": explanations
    }


if __name__ == "__main__":
    # Test conversion examples
    test_probs = [0.05, 0.20, 0.48, 0.65, 0.85, 0.98]
    print("=" * 60)
    print("        DEEPGUARD RISK SCORE CONVERSION TEST TABLE         ")
    print("=" * 60)
    print(f"| {'Prob':8s} | {'Tau':6s} | {'Risk Score':10s} | {'Risk Level':10s} | {'Alert?':6s} |")
    print("-" * 60)
    for p in test_probs:
        profile = compute_customer_risk_profile(p, tau_val=0.48)
        print(
            f"| {p:8.2f} | {profile['decision_threshold']:6.2f} | "
            f"{profile['risk_score']:10d} | {profile['risk_level']:10s} | "
            f"{str(profile['is_alert_triggered']):6s} |"
        )
    print("=" * 60)
