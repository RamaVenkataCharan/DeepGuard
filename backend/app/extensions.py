"""
Flask Extensions Initialization.
Initializes SQLAlchemy, JWTManager, CORS, and Celery instances.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from celery import Celery

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize JWT Manager
jwt = JWTManager()

# Initialize CORS
cors = CORS()

# Initialize Celery client (configured later in app factory)
celery = Celery()
