"""
Machine Learning Integration Service.
Acts as a bridge between the Flask app and the ML inference pipeline.
"""
import sys
import logging
from pathlib import Path
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# Add workspace root to Python path to ensure 'ml' package can be imported
sys.path.append(str(Path(__file__).resolve().parents[3]))

try:
    from ml.inference.predict import predict_customer_risk
    from ml.inference.batch_predict import run_batch_inference
    ML_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import ML package: {str(e)}")
    ML_AVAILABLE = False

class MLService:
    """
    Handles calling ML inference on raw customer consumption data.
    """
    
    @staticmethod
    def predict_customer(customer_id: int, consumption_readings: list) -> dict:
        """
        Runs inference on raw consumption array.
        """
        if not ML_AVAILABLE:
            logger.warning("ML components not available. Returning default low risk prediction.")
            return {
                "customer_id": customer_id,
                "bilstm_score": 0.05,
                "transformer_score": 0.05,
                "fused_score": 0.05,
                "risk_score": 5,
                "risk_level": "low",
                "consumption_stats": {}
            }
            
        # Call inference module
        raw_arr = np.array(consumption_readings, dtype=np.float32)
        return predict_customer_risk(customer_id, raw_arr)

    @staticmethod
    def predict_batch(batch_list: list) -> list:
        """
        Runs batch predictions.
        
        Args:
            batch_list: list of dicts, each with 'customer_id' and 'consumption' (list of readings)
        """
        if not ML_AVAILABLE:
            return [{
                "customer_id": item["customer_id"],
                "bilstm_score": 0.0,
                "transformer_score": 0.0,
                "fused_score": 0.0,
                "risk_score": 0,
                "risk_level": "low"
            } for item in batch_list]
            
        results_df = run_batch_inference(batch_list)
        return results_df.to_dict(orient="records")
ClassInstance = MLService()
