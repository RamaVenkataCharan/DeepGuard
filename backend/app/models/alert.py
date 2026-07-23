"""
Alert ORM Model.
Represents alerts generated when customer risk levels cross critical thresholds.
"""
from datetime import datetime
from app.extensions import db

class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True)
    severity = db.Column(db.Enum("info", "warning", "high", "critical", name="alert_severities"), nullable=False, default="warning", index=True)
    status = db.Column(db.Enum("open", "investigating", "resolved", "false_positive", name="alert_statuses"), nullable=False, default="open", index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = db.relationship("Customer", back_populates="alerts")
    prediction = db.relationship("Prediction", back_populates="alerts")
    resolver = db.relationship("User", back_populates="resolved_alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "prediction_id": self.prediction_id,
            "severity": self.severity,
            "status": self.status,
            "title": self.title,
            "message": self.message,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
