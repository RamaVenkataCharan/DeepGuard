"""
Customer ORM Model.
Represents a customer consumer monitored for electricity theft.
"""
from datetime import datetime
from app.extensions import db

class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=True)
    region = db.Column(db.String(100), nullable=False, index=True)
    city = db.Column(db.String(100), nullable=True)
    account_status = db.Column(db.Enum("active", "suspended", "closed", name="customer_statuses"), nullable=False, default="active")
    connection_type = db.Column(db.Enum("residential", "commercial", "industrial", name="connection_types"), nullable=False, default="residential")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    meters = db.relationship("Meter", back_populates="customer", cascade="all, delete-orphan")
    readings = db.relationship("MeterReading", back_populates="customer", cascade="all, delete-orphan", lazy="dynamic")
    predictions = db.relationship("Prediction", back_populates="customer", cascade="all, delete-orphan", lazy="dynamic")
    alerts = db.relationship("Alert", back_populates="customer", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "customer_code": self.customer_code,
            "name": self.name,
            "address": self.address,
            "region": self.region,
            "city": self.city,
            "account_status": self.account_status,
            "connection_type": self.connection_type,
            "created_at": self.created_at.isoformat()
        }

class Meter(db.Model):
    __tablename__ = "meters"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    meter_number = db.Column(db.String(50), unique=True, nullable=False)
    meter_type = db.Column(db.Enum("smart", "digital", "analog", name="meter_types"), nullable=False, default="smart")
    install_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = db.relationship("Customer", back_populates="meters")
    readings = db.relationship("MeterReading", back_populates="meter", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "meter_number": self.meter_number,
            "meter_type": self.meter_type,
            "install_date": self.install_date.isoformat() if self.install_date else None,
            "is_active": self.is_active
        }
