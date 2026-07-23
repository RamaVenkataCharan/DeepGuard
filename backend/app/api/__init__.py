# DeepGuard Backend API blueprints Package
from app.api.auth import auth_blp
from app.api.customers import customers_blp
from app.api.predictions import predictions_blp
from app.api.alerts import alerts_blp
from app.api.dashboard import dashboard_blp
from app.api.reports import reports_blp
from app.api.weather import weather_blp

__all__ = [
    "auth_blp",
    "customers_blp",
    "predictions_blp",
    "alerts_blp",
    "dashboard_blp",
    "reports_blp",
    "weather_blp"
]
