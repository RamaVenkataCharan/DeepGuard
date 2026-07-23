"""
Model Prediction and Inference Trigger API.
"""
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt
from marshmallow import Schema, fields
from app.models.customer import Customer
from app.models.prediction import Prediction
from app.models.meter_reading import MeterReading
from app.services.ml_service import MLService
from app.extensions import db

predictions_blp = Blueprint("predictions", "predictions", url_prefix="/api/predictions", description="Prediction operations")

class PredictRequestSchema(Schema):
    customer_id = fields.Int(required=True)

@predictions_blp.route("/run")
class RunPredictionView(MethodView):
    
    @jwt_required()
    @predictions_blp.arguments(PredictRequestSchema)
    def post(self, req_data):
        """Triggers local ML inference for a customer based on their latest readings."""
        # Check permissions (Analyst or Admin)
        claims = get_jwt()
        if claims.get("role") not in ["admin", "analyst"]:
            abort(403, message="Insufficient permissions to run models.")
            
        customer_id = req_data["customer_id"]
        customer = Customer.query.get_or_404(customer_id)
        
        # Pull readings history (e.g. last 14 days)
        readings = MeterReading.query.filter_by(customer_id=customer_id)\
            .order_by(MeterReading.timestamp.desc()).limit(14).all()
            
        if not readings:
            abort(400, message="No consumption readings found to generate a prediction sequence.")
            
        # Reverse to get chronological order
        consumption = [float(r.consumption_kwh) for r in reversed(readings)]
        
        # Ensure we pad/truncate or check minimum sequence length
        if len(consumption) < 7:
            # Generate dummy padding values if sequence is too short
            consumption = [15.0] * (7 - len(consumption)) + consumption
            
        # Call ML Prediction Service
        pred_dict = MLService.predict_customer(customer_id, consumption)
        
        # Record output in the database
        prediction = Prediction(
            customer_id=customer_id,
            bilstm_score=pred_dict["bilstm_score"],
            transformer_score=pred_dict["transformer_score"],
            fused_score=pred_dict["fused_score"],
            risk_score=pred_dict["risk_score"],
            risk_level=pred_dict["risk_level"],
            model_version="v1.0.0"
        )
        
        db.session.add(prediction)
        db.session.commit()
        
        # Create alert if critical risk
        if pred_dict["risk_score"] >= 51:
            from app.services.alert_service import AlertService
            AlertService.create_alert(
                customer_id=customer_id,
                prediction_id=prediction.id,
                severity="critical" if pred_dict["risk_score"] >= 76 else "high",
                title="Theft Risk Anomaly Flagged",
                message=f"Smart meter AI analysis flagged anomalous drop indicating possible theft. Risk Score: {pred_dict['risk_score']}."
            )
            
        return {
            "message": "Prediction generated successfully.",
            "prediction": prediction.to_dict()
        }, 200

@predictions_blp.route("/customer/<int:customer_id>")
class FetchPredictionHistoryView(MethodView):
    
    @jwt_required()
    def get(self, customer_id):
        """Retrieves prediction logs for a specific customer."""
        predictions = Prediction.query.filter_by(customer_id=customer_id)\
            .order_by(Prediction.predicted_at.desc()).all()
        return [p.to_dict() for p in predictions], 200
