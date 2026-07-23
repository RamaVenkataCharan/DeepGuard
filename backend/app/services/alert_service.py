"""
Alert Lifecycle Management Service.
Handles creating, updating, and auditing alerts.
"""
from datetime import datetime
from app.extensions import db
from app.models.alert import Alert
from app.models.prediction import Prediction
from app.models.customer import Customer

class AlertService:
    """
    Manages operational alert records and response status workflow.
    """
    
    @staticmethod
    def create_alert(customer_id: int, prediction_id: int, severity: str, title: str, message: str) -> Alert:
        """
        Creates a new alert record.
        """
        alert = Alert(
            customer_id=customer_id,
            prediction_id=prediction_id,
            severity=severity,
            status="open",
            title=title,
            message=message
        )
        db.session.add(alert)
        db.session.commit()
        return alert

    @staticmethod
    def update_alert_status(alert_id: int, status: str, user_id: int, notes: str = None) -> Alert:
        """
        Updates alert status, tracks who resolved it, and logs resolution timestamps.
        """
        alert = Alert.query.get_or_404(alert_id)
        alert.status = status
        alert.notes = notes
        
        if status in ["resolved", "false_positive"]:
            alert.resolved_by = user_id
            alert.resolved_at = datetime.utcnow()
            
        db.session.commit()
        return alert

    @staticmethod
    def get_active_alerts(severity: str = None, limit: int = 100) -> list:
        """
        Queries open and investigating alerts.
        """
        query = Alert.query.filter(Alert.status.in_(["open", "investigating"]))
        
        if severity:
            query = query.filter_by(severity=severity)
            
        alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
        return [a.to_dict() for a in alerts]
ClassInstance = AlertService()
