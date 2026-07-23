"""
Weather Anomaly Analysis API.
"""
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required
from app.services.weather_service import WeatherService

weather_blp = Blueprint("weather", "weather", url_prefix="/api/weather", description="Weather operations")

@weather_blp.route("/<string:region>")
class WeatherByRegionView(MethodView):
    
    @jwt_required()
    def get(self, region):
        """Fetches regional weather history logs."""
        data = WeatherService.get_weather_data(region)
        return {
            "region": region,
            "weather_logs": data
        }, 200

@weather_blp.route("/analysis/<int:customer_id>")
class WeatherCorrelationAnalysisView(MethodView):
    
    @jwt_required()
    def get(self, customer_id):
        """Runs weather-correlation anomaly detection for a customer."""
        analysis = WeatherService.analyze_weather_correlation(customer_id)
        return analysis, 200
