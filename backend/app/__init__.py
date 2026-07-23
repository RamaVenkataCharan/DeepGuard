"""
Flask Application Factory.
Defines the `create_app` function, registers extensions, blueprints, and configures celery.
"""
import os
from flask import Flask
from flask_smorest import Api
from app.config import config_by_name
from app.extensions import db, jwt, cors, celery

def create_app(config_name=None):
    """
    Creates and configures the Flask application.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
        
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    
    # Configure Celery
    init_celery(app)
    
    # Initialize Flask-Smorest API wrapper for OpenAPI docs
    api = Api(app)
    
    # Register blueprints (implemented in next steps)
    from app.api.auth import auth_blp
    from app.api.customers import customers_blp
    from app.api.predictions import predictions_blp
    from app.api.alerts import alerts_blp
    from app.api.dashboard import dashboard_blp
    from app.api.reports import reports_blp
    from app.api.weather import weather_blp
    
    api.register_blueprint(auth_blp)
    api.register_blueprint(customers_blp)
    api.register_blueprint(predictions_blp)
    api.register_blueprint(alerts_blp)
    api.register_blueprint(dashboard_blp)
    api.register_blueprint(reports_blp)
    api.register_blueprint(weather_blp)
    
    # Create database tables if in dev mode
    with app.app_context():
        if config_name == "development":
            db.create_all()
            
    return app

def init_celery(app):
    """
    Hooks Celery configuration into Flask configuration.
    """
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_always_eager=app.config["CELERY_TASK_ALWAYS_EAGER"]
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
                
    celery.Task = ContextTask
