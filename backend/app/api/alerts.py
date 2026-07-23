"""
Alert Auditing and Status Management API.
"""
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields
from app.models.alert import Alert
from app.services.alert_service import AlertService
from app.extensions import db

alerts_blp = Blueprint("alerts", "alerts", url_prefix="/api/alerts", description="Alert operations")

class UpdateAlertStatusSchema(Schema):
    status = fields.Str(required=True)
    notes = fields.Str(required=False)

@alerts_blp.route("/")
class ActiveAlertsView(MethodView):
    
    @jwt_required()
    def get(self):
        """Lists active alerts (open or investigating)."""
        severity = fields.Str(required=False)
        return AlertService.get_active_alerts(), 200

@alerts_blp.route("/history")
class AlertHistoryView(MethodView):
    
    @jwt_required()
    def get(self):
        """Retrieves history of all resolved / closed alerts."""
        alerts = Alert.query.filter(Alert.status.in_(["resolved", "false_positive"]))\
            .order_by(Alert.resolved_at.desc()).all()
        return [a.to_dict() for a in alerts], 200

@alerts_blp.route("/<int:alert_id>/status")
class UpdateAlertStatusView(MethodView):
    
    @jwt_required()
    @alerts_blp.arguments(UpdateAlertStatusSchema)
    def put(self, req_data, alert_id):
        """Updates the status of a specific alert (requires Analyst or Admin role)."""
        claims = get_jwt()
        if claims.get("role") not in ["admin", "analyst"]:
            abort(403, message="Insufficient permissions to modify alert statuses.")
            
        user_id = int(get_jwt_identity())
        status = req_data["status"]
        notes = req_data.get("notes")
        
        # Verify valid status
        if status not in ["open", "investigating", "resolved", "false_positive"]:
            abort(400, message="Invalid alert status code.")
            
        alert = AlertService.update_alert_status(alert_id, status, user_id, notes)
        return {
            "message": "Alert status updated successfully.",
            "alert": alert.to_dict()
        }, 200
