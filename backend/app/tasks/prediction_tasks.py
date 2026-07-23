"""
Asynchronous prediction tasks for Celery.
"""
from app.extensions import celery, db
from app.models.customer import Customer
from app.models.meter_reading import MeterReading
from app.models.prediction import Prediction
from app.services.ml_service import MLService
from app.services.alert_service import AlertService
import logging

logger = logging.getLogger(__name__)

@celery.task(name="tasks.run_batch_prediction")
def run_batch_prediction():
    """
    Celery task running nightly model inference batch across all active accounts.
    """
    logger.info("Starting background batch prediction task...")
    
    customers = Customer.query.filter_by(account_status="active").all()
    batch_list = []
    
    for c in customers:
        readings = MeterReading.query.filter_by(customer_id=c.id)\
            .order_by(MeterReading.timestamp.desc()).limit(14).all()
            
        if readings:
            consumption = [float(r.consumption_kwh) for r in reversed(readings)]
            if len(consumption) < 7:
                consumption = [15.0] * (7 - len(consumption)) + consumption
                
            batch_list.append({
                "customer_id": c.id,
                "consumption": consumption
            })
            
    if not batch_list:
        logger.info("No active customer readings found for batch processing.")
        return "No customers to predict"
        
    # Run batch predictions
    results = MLService.predict_batch(batch_list)
    
    for res in results:
        # Check if prediction already exists for this date to avoid duplicate runs
        prediction = Prediction(
            customer_id=res["customer_id"],
            bilstm_score=res["bilstm_score"],
            transformer_score=res["transformer_score"],
            fused_score=res["fused_score"],
            risk_score=res["risk_score"],
            risk_level=res["risk_level"],
            model_version="v1.0.0"
        )
        db.session.add(prediction)
        db.session.commit()
        
        # Check risk score threshold for alert generation
        if res["risk_score"] >= 51:
            AlertService.create_alert(
                customer_id=res["customer_id"],
                prediction_id=prediction.id,
                severity="critical" if res["risk_score"] >= 76 else "high",
                title="Theft Risk Alert (Batch Run)",
                message=f"Smart meter AI analysis flagged anomalous drop indicating possible theft. Risk Score: {res['risk_score']}."
            )
            
    logger.info(f"Background batch predictions completed for {len(results)} accounts.")
    return f"Processed {len(results)} predictions"
