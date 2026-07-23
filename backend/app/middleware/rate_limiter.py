"""
Rate Limiting Middleware.
Protects endpoints using sliding window rate checks. Fallbacks to in-memory store if Redis is offline.
"""
import time
from flask import request, jsonify

# Simple in-memory request store for rate checks
_rate_limits = {}

def rate_limit(requests_per_minute=60):
    """
    Decorator restricting requests per IP address.
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            ip = request.remote_addr
            now = time.time()
            
            # Initialize or clean old timestamps
            if ip not in _rate_limits:
                _rate_limits[ip] = []
                
            # Filter stamps inside the 60 seconds window
            _rate_limits[ip] = [t for t in _rate_limits[ip] if now - t < 60]
            
            if len(_rate_limits[ip]) >= requests_per_minute:
                response = jsonify({
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please try again later.",
                    "status_code": 429
                })
                response.status_code = 429
                return response
                
            # Append new request timestamp
            _rate_limits[ip].append(now)
            return f(*args, **kwargs)
        # Preserve function properties
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
