# cython: language_level=3
import time
import datetime
from flask import blueprints, request, redirect, url_for, flash
from flask_login import current_user
from sqlalchemy import event
from sqlalchemy.engine import Engine

from src.config import app
from src.logger import logger
from src.activator import get_plan_details
from src.background_task.prometheus_metrics import metrics

middleware_bp = blueprints.Blueprint("middleware", __name__)

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


# Define a dictionary for query types
QUERY_TYPE_LABELS = {
    "insert": "insert",
    "select": "select",
    "delete": "delete",
    "update": "update"
}

@event.listens_for(Engine, 'before_cursor_execute')
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    # Identify the query type and observe it
    query_type = statement.split()[0].lower()
    if query_type in QUERY_TYPE_LABELS:
        metrics['DB_REQUESTS'].labels(route=QUERY_TYPE_LABELS[query_type]).observe(1)

    context._query_start_time = time.time()  # Record the start time

@event.listens_for(Engine, 'after_cursor_execute')
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    try:
        query_time = time.time() - context._query_start_time
        query_type = statement.split()[0].lower()

        metrics['DB_REQUESTS_COUNTER'].inc()

        if query_type in QUERY_TYPE_LABELS:
            metrics['DB_QUERY_TIME'].labels(query_type=query_type).observe(query_time)

        if query_time > 0.5:  # Example threshold of 0.5 seconds
                # slow_query_duration.labels(query_type=query_type).observe(query_time)
            metrics['SLOW_DB_QUERY'].labels(query_type=query_type).observe(query_time)
    except Exception as e:
        logger.error(f"Error in after_cursor_execute: {e}", exc_info=True)
        metrics['ERROR_QUERY_COUNTER'].inc()
