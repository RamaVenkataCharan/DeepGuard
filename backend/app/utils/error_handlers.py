"""
Global API Error Handlers.
Registers handlers for standard exceptions returning structured JSON payloads.
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended.exceptions import JWTExtendedException

def register_error_handlers(app):
    """
    Hooks exception catching middleware into the Flask application.
    """
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Catches standard HTTP errors."""
        response = jsonify({
            "error": e.name,
            "message": e.description,
            "status_code": e.code
        })
        response.status_code = e.code
        return response

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(e):
        """Catches database connectivity or syntax errors."""
        response = jsonify({
            "error": "Database Error",
            "message": "A database operation failed. Check logs for details.",
            "status_code": 500
        })
        response.status_code = 500
        return response

    @app.errorhandler(JWTExtendedException)
    def handle_jwt_error(e):
        """Catches invalid/expired auth tokens."""
        response = jsonify({
            "error": "Authentication Error",
            "message": str(e),
            "status_code": 401
        })
        response.status_code = 401
        return response

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        """Catch-all handler for unhandled server issues."""
        response = jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred.",
            "status_code": 500
        })
        response.status_code = 500
        return response
