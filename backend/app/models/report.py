"""
Report ORM Model.
Tracks compiled analytical export reports (PDF / CSV format).
"""
from datetime import datetime
from app.extensions import db

class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    generated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = db.Column(db.Enum("theft_summary", "risk_assessment", "alert_digest", "customer_report", "custom", name="report_types"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    format = db.Column(db.Enum("pdf", "csv", name="report_formats"), nullable=False, default="pdf")
    file_path = db.Column(db.String(500), nullable=True)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    parameters = db.Column(db.JSON, nullable=True)
    status = db.Column(db.Enum("pending", "generating", "completed", "failed", name="report_statuses"), nullable=False, default="pending", index=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    creator = db.relationship("User", back_populates="generated_reports")

    def to_dict(self):
        return {
            "id": self.id,
            "generated_by": self.generated_by,
            "report_type": self.report_type,
            "title": self.title,
            "format": self.format,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "parameters": self.parameters,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
