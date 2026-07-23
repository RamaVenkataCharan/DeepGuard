"""
Request Logging Middleware.
Logs incoming requests with correlation IDs and processing durations.
"""
import time
import uuid
import logging
from flask import request, g

logger = logging.getLogger(__name__)

def setup_request_logging(app):
    """
    Registers before_request and after_request hooks to log API calls.
    """
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        logger.info(
            f"[{g.correlation_id}] {request.method} {request.path} from {request.remote_addr}"
        )

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            logger.info(
                f"[{getattr(g, 'correlation_id', 'unknown')}] Status: {response.status} | Took: {duration:.4f}s"
            )
        return response
