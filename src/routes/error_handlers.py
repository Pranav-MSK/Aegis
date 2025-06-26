# cython: language_level=3
from flask import render_template, blueprints

from src.core.config.app_config import app
from src.tasks.prometheus_metrics import metrics

error_handlers_bp = blueprints.Blueprint("error_handlers", __name__)

class CustomError(Exception):
    """Custom exception for application-specific errors."""
    pass

# Error Handlers
@app.errorhandler(403)
def forbidden(e):
    """Handle 403 Forbidden error.k"""
    metrics['error_codes'].labels(error_code='403').observe(1)
    return render_template("error/403.html",
                           error_message=e.description,
                           ), 403
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 Not Found error."""
    metrics['error_codes'].labels(error_code='404').observe(1)
    return render_template("error/404.html"), 404

@app.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 Method Not Allowed error."""
    return "Method not allowed", 405

@app.errorhandler(429)
def ratelimit_handler(e):
    metrics['error_codes'].labels(error_code='429').observe(1)
    return render_template("error/429.html", 
                           error_message=e.description,
                           ), 429

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 Internal Server Error."""
    metrics['error_codes'].labels(error_code='500').observe(1)
    return "Internal server error", 500

@app.errorhandler(502)
def bad_gateway(e):
    """Handle 502 Bad Gateway error."""
    metrics['error_codes'].labels(error_code='502').observe(1)
    return "Bad gateway", 502

@app.errorhandler(503)
def service_unavailable(e):
    """Handle 503 Service Unavailable error."""
    metrics['error_codes'].labels(error_code='503').observe(1)
    return "Service unavailable", 503

@app.errorhandler(504)
def gateway_timeout(e):
    """Handle 504 Gateway Timeout error."""
    metrics['error_codes'].labels(error_code='504').observe(1)
    return "Gateway timeout", 504
