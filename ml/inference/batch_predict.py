"""
Batch Inference Module for DeepGuard.
Runs inference pipelines over multiple customers concurrently.
"""
import logging
from typing import List, Dict
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

from ml.inference.predict import predict_customer_risk, init_inference_assets
from ml.config import DEFAULT_SEQUENCE_LENGTH

def run_batch_inference(
    customers_data: List[Dict],
    sequence_length: int = DEFAULT_SEQUENCE_LENGTH
) -> pd.DataFrame:
    """
    Runs batch predictions for multiple customers.
    
    Args:
        customers_data: List of dicts, each having 'customer_id' and 'consumption' (numpy array or list)
        sequence_length: Input window size for model
        
    Returns:
        pd.DataFrame containing prediction results for all customers.
    """
    logger.info(f"Starting batch prediction for {len(customers_data)} customers...")
    
    # Initialize/load models once before starting loops
    init_inference_assets()
    
    results = []
    for item in customers_data:
        cid = item["customer_id"]
        consumption = np.array(item["consumption"], dtype=np.float32)
        
        try:
            pred = predict_customer_risk(cid, consumption, sequence_length)
            results.append(pred)
        except Exception as e:
            logger.error(f"Failed prediction for customer {cid}: {str(e)}")
            # Append fallback error record
            results.append({
                "customer_id": cid,
                "bilstm_score": 0.0,
                "transformer_score": 0.0,
                "fused_score": 0.0,
                "risk_score": 0,
                "risk_level": "low",
                "error": str(e)
            })
            
    df_results = pd.DataFrame(results)
    logger.info("Batch inference complete.")
    return df_results
