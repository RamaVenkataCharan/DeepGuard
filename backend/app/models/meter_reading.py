"""
MeterReading ORM Model.
Represents daily consumption readings for customer meters (time-series).
"""
from datetime import datetime
from app.extensions import db

class MeterReading(db.Model):
    __tablename__ = "meter_readings"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    meter_id = db.Column(db.Integer, db.ForeignKey("meters.id", ondelete="CASCADE"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    consumption_kwh = db.Column(db.Numeric(12, 4), nullable=False)
    voltage = db.Column(db.Numeric(8, 2), nullable=True)
    current_amps = db.Column(db.Numeric(8, 2), nullable=True)
    power_factor = db.Column(db.Numeric(5, 4), nullable=True)
    quality_flag = db.Column(db.Enum("valid", "estimated", "missing", "suspect", name="quality_flags"), nullable=False, default="valid")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    customer = db.relationship("Customer", back_populates="readings")
    meter = db.relationship("Meter", back_populates="readings")

    # Add composite indexes via table_args
    __table_args__ = (
        db.Index("idx_readings_customer_ts", "customer_id", "timestamp"),
        db.Index("idx_readings_meter_ts", "meter_id", "timestamp"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "meter_id": self.meter_id,
            "customer_id": self.customer_id,
            "timestamp": self.timestamp.isoformat(),
            "consumption_kwh": float(self.consumption_kwh),
            "voltage": float(self.voltage) if self.voltage else None,
            "current_amps": float(self.current_amps) if self.current_amps else None,
            "power_factor": float(self.power_factor) if self.power_factor else None,
            "quality_flag": self.quality_flag
        }
