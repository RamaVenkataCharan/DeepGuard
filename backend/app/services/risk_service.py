"""
Risk Assessment Service.
Aggregates risk score data and exposes methods for auditing and analysis.
"""
from datetime import datetime
from app.extensions import db
from app.models.prediction import Prediction
from app.models.customer import Customer

class RiskService:
    """
    Manages customer risk level tracking and retrieval of prediction histories.
    """
    
    @staticmethod
    def get_customer_risk_history(customer_id: int, limit: int = 10) -> list:
        """
        Retrieves prediction history for a customer.
        """
        predictions = Prediction.query.filter_by(customer_id=customer_id)\
            .order_by(Prediction.predicted_at.desc())\
            .limit(limit).all()
        return [p.to_dict() for p in predictions]

    @staticmethod
    def get_high_risk_customers(threshold: int = 50, limit: int = 50) -> list:
        """
        Retrieves customers exceeding a specific risk score threshold.
        """
        # Join predictions and customers to get detailed data
        latest_predictions = db.session.query(
            Prediction, Customer
        ).join(Customer, Prediction.customer_id == Customer.id)\
         .filter(Prediction.risk_score >= threshold)\
         .order_by(Prediction.risk_score.desc())\
         .limit(limit).all()
         
        results = []
        for pred, cust in latest_predictions:
            results.append({
                "customer": cust.to_dict(),
                "prediction": pred.to_dict()
            })
        return results
ClassInstance = RiskService()
