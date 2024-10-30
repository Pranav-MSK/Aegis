# cython: language_level=3
import time
import datetime

from flask import blueprints, request, redirect, url_for, flash, Response
from flask_login import current_user
from sqlalchemy import event
from sqlalchemy.engine import Engine
from prometheus_client import Counter

from src.config import app
from src.logger import logger
from src.activator import get_plan_details
from src.background_task.prometheus_metrics import metrics

middleware_bp = blueprints.Blueprint("middleware", __name__)

class SecurityMiddleware:
    """Handle security-related middleware functions"""
    
    @staticmethod
    def days_until_password_expiry(user) -> int:
        """Calculate days until password expires"""
        expiry_date = user.password_last_changed + datetime.timedelta(days=60)
        return (expiry_date - datetime.datetime.now()).days

    @staticmethod
    def check_password_strength(password: str) -> tuple[bool, str]:
        """Verify password meets security requirements"""
        if len(password) < 12:
            return False, "Password must be at least 12 characters long"
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"
        return True, "Password meets requirements"

class MetricsMiddleware:
    """Handle metrics collection and monitoring"""
    
    def __init__(self):
        # Initialize additional metrics
        self.failed_logins = Counter(
            'failed_login_attempts',
            'Number of failed login attempts',
            ['ip_address']
        )

    def record_request_metrics(self, response: Response, start_time: float):
        """Record various request-related metrics"""
        try:
            elapsed_time = time.time() - start_time
            endpoint = request.endpoint or 'unknown'
            
            # Record basic request metrics
            metrics['REQUEST_HISTOGRAM'].labels(route=request.path).observe(elapsed_time)
            metrics['REQUEST_METHOD_COUNT'].labels(method=request.method).observe(elapsed_time)
            
            # Record response size if available
            if response.data:
                metrics['RESPONSE_SIZE'].labels(route=request.path).observe(len(response.data))
                            
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
            metrics['ERROR_METRIC_COUNTER'].inc()

class PlanMiddleware:
    """Handle plan and license-related functionality"""
    
    @staticmethod
    def update_plan_globals():
        """Update Jinja globals with current plan details"""
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
    
    @staticmethod
    def check_plan_limits():
        """Check if current usage is within plan limits"""
        plan_details = get_plan_details()
        if not plan_details.get('is_plan_not_expired'):
            flash("Your plan has expired. Please renew to continue.", "danger")
            return redirect(url_for('activation'))
        return None

# Initialize middleware instances
security = SecurityMiddleware()
metrics_middleware = MetricsMiddleware()
plan_middleware = PlanMiddleware()

# Define routes that bypass certain middleware checks
BYPASS_ROUTES = {
    'login', 'change_password', 'static', 'health_check', 'metrics', 'activation', 'signup', 'logout',
}

@app.before_request
def global_middleware():
    """Global middleware for all requests"""
    request.start_time = time.time()
    
    # Skip middleware for bypass routes
    if request.endpoint in BYPASS_ROUTES:
        return
    
    try:
        # Check IP whitelist
        # if not check_ip_whitelist(request.remote_addr):
        #     logger.warning(f"Blocked request from non-whitelisted IP: {request.remote_addr}")
        #     return "Access denied", 403
            
        # Apply rate limiting
        # try:
        #     rate_limiter.check_rate_limit(request)
        # except RateLimitExceeded:
        #     return "Rate limit exceeded", 429
            
        # Authentication checks
        if current_user.is_authenticated:
            # Password expiry check
            remaining_days = security.days_until_password_expiry(current_user)
            if remaining_days <= 0:
                flash("Your password has expired. Please change it to continue.", "danger")
                return redirect(url_for('change_password'))
            
            # Password expiry warning
            if remaining_days <= 10:
                flash(f"Your password will expire in {remaining_days} days. Please change it soon.", "warning")
            
            # Default password check
            if current_user.check_password("admin"):
                flash("Security Alert: Please change the default password for your security.", "danger")
                return redirect(url_for('change_password'))
                    
        # Plan-related checks for specific endpoints
        if request.endpoint in ['activation', 'download_license', '/']:
            plan_middleware.update_plan_globals()
            plan_check_result = plan_middleware.check_plan_limits()
            if plan_check_result:
                return plan_check_result
                
    except Exception as e:
        logger.error(f"Error in global middleware: {e}")
        return "Internal server error", 500

@app.after_request
def after_request(response: Response) -> Response:
    """Process response and record metrics"""
    try:
        if request.endpoint not in BYPASS_ROUTES:
            metrics_middleware.record_request_metrics(response, request.start_time)
    except Exception as e:
        logger.error(f"Error processing response: {e}")
    
    return response

# Database query monitoring
QUERY_TYPE_LABELS = {
    "insert": "insert",
    "select": "select",
    "delete": "delete",
    "update": "update",
    "create": "create",
    "alter": "alter",
    "drop": "drop"
}

@event.listens_for(Engine, 'before_cursor_execute')
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record database query start time and type"""
    context._query_start_time = time.time()

@event.listens_for(Engine, 'after_cursor_execute')
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Monitor and record database query metrics"""
    try:
        query_time = time.time() - context._query_start_time
        query_type = statement.split()[0].lower()

        # Update query counters and timing metrics
        metrics['DB_REQUESTS_COUNTER'].inc()
        if query_type in QUERY_TYPE_LABELS:
            metrics['DB_REQUESTS'].labels(route=request.endpoint).observe(query_time)
        
        if query_type in QUERY_TYPE_LABELS:
            metrics['DB_QUERY_TIME'].labels(query_type=query_type).observe(query_time)
            
            # Monitor for slow queries
            if query_time > app.config.get('SLOW_QUERY_THRESHOLD', 0.5):
                metrics['SLOW_DB_QUERY'].labels(query_type=query_type).observe(query_time)
                logger.warning(f"Slow query detected ({query_time:.2f}s): {statement[:200]}...")
                
    except Exception as e:
        pass
