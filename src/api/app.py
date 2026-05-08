"""
Flask API Application
REST API for MediSafeAI data generation and privacy operations
"""

import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import datetime
from pathlib import Path

from src.config.settings import settings
from src.utils.logger import setup_logging, get_logger, get_audit_logger
from src.api.routes import register_routes
from src.api.auth_routes import auth_bp

# Initialize logger
setup_logging()
logger = get_logger(__name__)
audit_logger = get_audit_logger()

# Create Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['JWT_SECRET_KEY'] = settings.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max request size

# Enable CORS if configured
if settings.CORS_ENABLED:
    CORS(app, resources={r"/api/*": {"origins": settings.CORS_ORIGINS}})

# Initialize JWT
jwt = JWTManager(app)

# Track app start time and metrics
app_start_time = time.time()
request_count = 0


# =============================================================================
# MIDDLEWARE
# =============================================================================

@app.before_request
def before_request():
    """Log request information"""
    global request_count
    request_count += 1
    request.start_time = time.time()
    logger.info(f"{request.method} {request.path} from {request.remote_addr}")


@app.after_request
def after_request(response):
    """Log response information"""
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        logger.info(f"{request.method} {request.path} {response.status_code} ({duration:.3f}s)")

    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    return response


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'error_code': 'NOT_FOUND',
        'error_message': 'Resource not found',
        'timestamp': datetime.utcnow().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'status': 'error',
        'error_code': 'INTERNAL_ERROR',
        'error_message': 'Internal server error',
        'timestamp': datetime.utcnow().isoformat()
    }), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all exceptions"""
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    return jsonify({
        'status': 'error',
        'error_code': 'EXCEPTION',
        'error_message': str(error),
        'timestamp': datetime.utcnow().isoformat()
    }), 500


# =============================================================================
# CORE ENDPOINTS
# =============================================================================

@app.route('/')
def index():
    """API root endpoint"""
    return jsonify({
        'name': 'MediSafeAI API',
        'version': settings.APP_VERSION,
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'api_v1': '/api/v1',
            'docs': '/api/docs'
        }
    })


@app.route('/health')
def health_check():
    """Health check endpoint"""
    uptime = time.time() - app_start_time

    # Check database connection
    db_connected = True
    try:
        from src.models.base import get_db_session
        session = get_db_session()
        session.execute('SELECT 1')
        session.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_connected = False

    # Check Redis connection
    redis_connected = True
    if settings.CACHE_ENABLED:
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            redis_connected = False

    health_status = 'healthy' if (db_connected and redis_connected) else 'degraded'

    return jsonify({
        'status': health_status,
        'version': settings.APP_VERSION,
        'uptime_seconds': uptime,
        'database_connected': db_connected,
        'redis_connected': redis_connected,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    uptime = time.time() - app_start_time

    metrics_data = [
        "# HELP medisafe_uptime_seconds Uptime of the MediSafeAI API in seconds",
        "# TYPE medisafe_uptime_seconds gauge",
        f"medisafe_uptime_seconds {uptime}",
        "# HELP medisafe_requests_total Total number of requests to the MediSafeAI API",
        "# TYPE medisafe_requests_total counter",
        f"medisafe_requests_total {request_count}"
    ]

    return "\n".join(metrics_data) + "\n", 200, {'Content-Type': 'text/plain; version=0.0.4'}


# =============================================================================
# REGISTER API ROUTES
# =============================================================================

app.register_blueprint(auth_bp)
register_routes(app)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    logger.info(f"Starting MediSafeAI API v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    app.run(
        host=settings.API_HOST,
        port=settings.API_PORT,
        debug=settings.DEBUG
    )
