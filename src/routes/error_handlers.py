# cython: language_level=3
import time
import datetime
from flask import render_template, blueprints, request, redirect, url_for, flash
from flask_login import current_user

from src.config import app
from src.logger import logger
from src.activator import get_plan_details
from src.background_task.prometheus_metrics import metrics

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


def days_until_password_expiry(user):
    return (user.password_last_changed + datetime.timedelta(days=60) - datetime.datetime.now()).days


@app.before_request
def check_password_expiry():
    # Allow access to login, password change, and static files routes without restriction
    request.start_time = time.time()

    if request.endpoint in ['login', 'change_password', 'static']:
        return
    # Perform checks only for authenticated users
    if current_user.is_authenticated:
        remaining_days = days_until_password_expiry(current_user)
        
        # Redirect if the password has expired
        if remaining_days <= 0:
            flash("Your password has expired. Please change it to continue.", "danger")
            return redirect(url_for('change_password'))

        # Warn the user if the password will expire soon
        if remaining_days <= 10:
            flash(f"Your password will expire in {remaining_days} days. Please change it soon.", "warning")

        # Check if the user is still using the default password (e.g., 'admin')
        if current_user.check_password("admin"):
            flash("Security Alert: Please change the default password for your security.", "danger")
            return redirect(url_for('change_password'))

    if request.endpoint in ['activation', 'download_license', '/']:
        plan_details = get_plan_details()
        app.jinja_env.globals.update(
            is_plan_not_expired=plan_details.get('is_plan_not_expired'),
            remaining_plan_days=plan_details.get('remaining_plan_days'),
            plan_type=plan_details.get('plan_type'),
            is_trial=plan_details.get('is_trial'),
            license_key=plan_details.get('license_key'),
            activation_code=plan_details.get('activation_code'),
            systemguard_unique_id=plan_details.get('systemguard_unique_id'),
            max_scrap_target=plan_details.get('max_scrap_target'),
            max_alert_rules=plan_details.get('max_alert_rules'),
            max_number_of_graphs=plan_details.get('max_number_of_graphs'),
            monthly_alert_tickets_limit=plan_details.get('monthly_alert_tickets_limit'),
            max_users_allowed=plan_details.get('max_users_allowed')
        )

@app.after_request
def after_request(response):
    if request.endpoint in ['static']:
        return response

    try:
        elapsed_time = time.time() - request.start_time
        metrics['REQUEST_HISTOGRAM'].labels(route=request.path).observe(elapsed_time)
        metrics['REQUEST_METHOD_COUNT'].labels(method=request.method).observe(elapsed_time) 
        
        if response.data:
            metrics['RESPONSE_SIZE'].labels(route=request.path).observe(len(response.data))
    except Exception as e:
        logger.error(f"Error in after_request: {e}")

    return response