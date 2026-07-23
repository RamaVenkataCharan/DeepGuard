"""
Risk Score Logic for DeepGuard.
Converts model prediction probabilities (0-1) into an actionable Risk Score (0-100)
categorized into risk tiers: Low, Medium, High, and Critical.
"""
import numpy as np

def calculate_risk_score(
    theft_probability: float,
    consumption_stats: dict = None
) -> dict:
    """
    Computes a risk score between 0 and 100 based on model probability
    and optional statistical factors.
    
    Args:
        theft_probability: Raw prediction output from the fusion model (0.0 to 1.0)
        consumption_stats: dict containing metrics like coefficient of variation (cv),
                          zero_fraction, trend_slope, etc.
                          
    Returns:
        dict containing 'risk_score' (int 0-100), 'risk_level' (str)
    """
    # Non-linear probability scaling to align with risk tiers
    # We want critical alerts (prob >= 0.75) to be mapped to 76-100, etc.
    p = float(np.clip(theft_probability, 0.0, 1.0))
    
    if p < 0.25:
        # Scale [0.0, 0.25) to [0, 25]
        score = p * 100
    elif p < 0.50:
        # Scale [0.25, 0.50) to [26, 50]
        score = 26 + (p - 0.25) * 4 * 24
    elif p < 0.75:
        # Scale [0.50, 0.75) to [51, 75]
        score = 51 + (p - 0.50) * 4 * 24
    else:
        # Scale [0.75, 1.0] to [76, 100]
        score = 76 + (p - 0.75) * 4 * 24
        
    score = int(np.clip(score, 0, 100))
    
    # Adjust based on statistical risk signals if provided
    if consumption_stats:
        zero_fraction = consumption_stats.get("zero_fraction", 0.0)
        cv = consumption_stats.get("cv", 0.0) # Coefficient of variation
        trend = consumption_stats.get("trend_slope", 0.0)
        
        # High zero fraction increases risk slightly
        if zero_fraction > 0.3:
            score += 5
            
        # Extreme volatility (cv > 1.5) increases risk slightly
        if cv > 1.5:
            score += 5
            
        # Downward consumption trend for a suspected device increases risk
        if trend < -0.5 and p > 0.4:
            score += 5
            
        score = int(np.clip(score, 0, 100))
        
    # Determine level
    if score <= 25:
        level = "low"
    elif score <= 50:
        level = "medium"
    elif score <= 75:
        level = "high"
    else:
        level = "critical"
        
    return {
        "risk_score": score,
        "risk_level": level,
        "theft_probability": p
    }
