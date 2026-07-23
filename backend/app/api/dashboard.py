"""
Dashboard Aggregated Analytics API.
"""
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required
from app.models.customer import Customer
from app.models.alert import Alert
from app.models.prediction import Prediction
from app.extensions import db

dashboard_blp = Blueprint("dashboard", "dashboard", url_prefix="/api/dashboard", description="Dashboard aggregation operations")

@dashboard_blp.route("/stats")
class DashboardStatsView(MethodView):
    
    @jwt_required()
    def get(self):
        """Aggregates and returns summary stats for indicators cards."""
        total_customers = Customer.query.count()
        active_alerts = Alert.query.filter(Alert.status.in_(["open", "investigating"])).count()
        
        # Calculate average risk score of latest predictions
        avg_risk_row = db.session.query(db.func.avg(Prediction.risk_score)).first()
        avg_risk = float(avg_risk_row[0]) if avg_risk_row and avg_risk_row[0] is not None else 0.0
        
        # Get count of customers at critical risk
        critical_count = Prediction.query.filter_by(risk_level="critical").count()
        
        return {
            "total_customers": total_customers,
            "active_alerts": active_alerts,
            "average_risk_score": avg_risk,
            "critical_risk_count": critical_count
        }, 200

@dashboard_blp.route("/risk-distribution")
class RiskDistributionView(MethodView):
    
    @jwt_required()
    def get(self):
        """Aggregates and returns distribution of risk levels across all customers."""
        # Simple query for risk_level distribution
        # Group by risk_level and count
        results = db.session.query(
            Prediction.risk_level, db.func.count(Prediction.id)
        ).group_by(Prediction.risk_level).all()
        
        distribution = {level: 0 for level in ["low", "medium", "high", "critical"]}
        for level, count in results:
            if level in distribution:
                distribution[level] = count
                
        return distribution, 200

@dashboard_blp.route("/recent-alerts")
class RecentAlertsView(MethodView):
    
    @jwt_required()
    def get(self):
        """Fetches the 5 most recent active alerts."""
        alerts = Alert.query.filter(Alert.status.in_(["open", "investigating"]))\
            .order_by(Alert.created_at.desc()).limit(5).all()
        return [a.to_dict() for a in alerts], 200
