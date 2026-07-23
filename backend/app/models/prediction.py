"""
Prediction ORM Model.
Stores model predictions for theft probability and mapped risk levels.
"""
from datetime import datetime
from app.extensions import db

class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    bilstm_score = db.Column(db.Numeric(8, 6), nullable=False)
    transformer_score = db.Column(db.Numeric(8, 6), nullable=False)
    fused_score = db.Column(db.Numeric(8, 6), nullable=False)
    risk_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.Enum("low", "medium", "high", "critical", name="risk_levels"), nullable=False)
    model_version = db.Column(db.String(20), nullable=False, default="v1.0.0")
    sequence_start = db.Column(db.DateTime, nullable=True)
    sequence_end = db.Column(db.DateTime, nullable=True)
    predicted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    customer = db.relationship("Customer", back_populates="predictions")
    alerts = db.relationship("Alert", back_populates="prediction")

    __table_args__ = (
        db.Index("idx_predictions_customer_at", "customer_id", "predicted_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "bilstm_score": float(self.bilstm_score),
            "transformer_score": float(self.transformer_score),
            "fused_score": float(self.fused_score),
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "model_version": self.model_version,
            "sequence_start": self.sequence_start.isoformat() if self.sequence_start else None,
            "sequence_end": self.sequence_end.isoformat() if self.sequence_end else None,
            "predicted_at": self.predicted_at.isoformat()
        }
