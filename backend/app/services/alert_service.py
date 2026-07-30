"""
Alert Lifecycle Management Service.
Handles creating, updating, and auditing alerts.
Includes deduplication logic, metadata tags, and strict lifecycle transitions.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.extensions import db
from app.models.alert import Alert
from app.models.customer import Customer

# Define severity rankings for threshold comparison
SEVERITY_RANKS = {
    "info": 1,
    "warning": 2,
    "high": 3,
    "critical": 4
}

class AlertService:
    """
    Manages operational alert records and response status workflow.
    """
    
    @staticmethod
    def process_prediction_for_alert(
        customer_id: int,
        prediction_id: Optional[int],
        risk_profile: Dict[str, Any],
        data_source: str,
        alert_min_severity: str = "high",
        dedup_days: int = 7
    ) -> Dict[str, Any]:
        """
        Processes a customer prediction risk profile and creates an Alert if thresholds are met.
        Includes de-duplication checks to prevent duplicate alerts for the same customer.
        """
        VALID_DATA_SOURCES = ["synthetic_demo", "real_sgcc"]
        if data_source not in VALID_DATA_SOURCES:
            raise ValueError(f"Invalid data_source: '{data_source}'. Must be one of {VALID_DATA_SOURCES}")

        risk_score = risk_profile["risk_score"]
        raw_prob = risk_profile["raw_probability"]
        risk_level = risk_profile["risk_level"]  # e.g., 'low', 'medium', 'high', 'critical'
        explanations = risk_profile.get("explanations", [])
        
        # Map risk level to database severity (info, warning, high, critical)
        severity_map = {
            "low": "info",
            "medium": "warning",
            "high": "high",
            "critical": "critical"
        }
        severity = severity_map.get(risk_level, "warning")
        
        # 1. Check if severity meets the minimum configured alert threshold
        min_rank = SEVERITY_RANKS.get(alert_min_severity.lower(), 3)
        curr_rank = SEVERITY_RANKS.get(severity, 2)
        
        if curr_rank < min_rank:
            return {
                "status": "skipped",
                "reason": f"Severity '{severity}' is below configured alert minimum threshold '{alert_min_severity}'."
            }
            
        # 2. De-duplication: Check for existing active alerts for this customer in the last N days
        cutoff_date = datetime.utcnow() - timedelta(days=dedup_days)
        existing_alert = Alert.query.filter(
            Alert.customer_id == customer_id,
            Alert.status.in_(["open", "investigating"]),
            Alert.created_at >= cutoff_date
        ).first()
        
        if existing_alert:
            return {
                "status": "skipped",
                "reason": f"Duplicate Alert Skipped: Existing open alert #{existing_alert.id} "
                          f"({existing_alert.severity}) created in the last {dedup_days} days."
            }

        # 3. Create new Alert
        title = f"{severity.capitalize()} Theft Risk Alert"
        message = (
            f"Customer risk score reached {risk_score}/100. "
            f"Theft probability: {raw_prob:.2%}. "
            f"Primary indicators: {'; '.join(explanations)}"
        )
        
        alert = Alert(
            customer_id=customer_id,
            prediction_id=prediction_id,
            severity=severity,
            status="open",
            title=title,
            message=message,
            data_source=data_source,
            contributing_features=risk_profile.get("explanations", [])
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return {
            "status": "created",
            "alert_id": alert.id,
            "alert": alert.to_dict()
        }

    @staticmethod
    def update_alert_status(alert_id: int, target_status: str, user_id: int, notes: str = None) -> Alert:
        """
        Updates alert status with strict lifecycle transition validation:
        - Allowed transitions:
          - open -> investigating
          - open -> false_positive
          - investigating -> resolved
          - investigating -> false_positive
        - Reject all other transitions (e.g. going back from terminal state) with ValueError.
        """
        alert = Alert.query.get_or_404(alert_id)
        current = alert.status
        target = target_status.lower()

        # Validate Lifecycle State Machine
        allowed_transitions = {
            "open": ["investigating", "false_positive"],
            "investigating": ["resolved", "false_positive"],
            "resolved": [],
            "false_positive": []
        }
        
        if target not in allowed_transitions:
            raise ValueError(f"Invalid target status code: '{target}'")
            
        if target not in allowed_transitions.get(current, []):
            raise ValueError(f"Forbidden state transition: cannot transition alert from '{current}' to '{target}'")

        alert.status = target
        if notes:
            # Append notes if they exist
            if alert.notes:
                alert.notes = f"{alert.notes}\n[{datetime.utcnow().isoformat()}] User #{user_id}: {notes}"
            else:
                alert.notes = f"[{datetime.utcnow().isoformat()}] User #{user_id}: {notes}"

        if target in ["resolved", "false_positive"]:
            alert.resolved_by = user_id
            alert.resolved_at = datetime.utcnow()
            
        db.session.commit()
        return alert

    @staticmethod
    def get_active_alerts(severity: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Queries open and investigating alerts.
        """
        query = Alert.query.filter(Alert.status.in_(["open", "investigating"]))
        
        if severity:
            query = query.filter_by(severity=severity.lower())
            
        alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
        return [a.to_dict() for a in alerts]

ClassInstance = AlertService()
