# cython: language_level=3
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

from src.helper import get_system_node_name, get_ip_address, load_secret_key
from src.activator import get_plan_details

app = Flask(__name__)

# Application Metadata
APP_NAME = "SystemGuard"
DESCRIPTION = f"{APP_NAME} is a web application that allows you to monitor your system resources."
AUTHOR = "SystemGuard Team"
YEAR = "2024"
PRE_RELEASE = False
VERSION = "v1.0.6"
PROJECT_URL = f"https://github.com/codeperfectplus/{APP_NAME}"
CONTACT_EMAIL = ""
SYSTEM_NAME = get_system_node_name()
SYSTEM_IP_ADDRESS = get_ip_address()


obfuscated_flask_config = load_secret_key("flask_configuration.so")

HOME_DIR = os.path.expanduser("~")
DB_DIR = os.path.join(HOME_DIR, ".database")
os.makedirs(DB_DIR, exist_ok=True)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_DIR}/systemguard.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 5
app.config['SECRET_KEY'] = obfuscated_flask_config
app.config['WTF_CSRF_SECRET_KEY'] = obfuscated_flask_config
app.config['WTF_CSRF_TIME_LIMIT'] = 3600
app.config['WTF_CSRF_HEADER_NAME'] = "X-CSRFToken"
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent access to cookies via JavaScript
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"  # Prevent CSRF attacks via cross-site requests
app.config['SESSION_COOKIE_SECURE'] = False  # Change to True for production with HTTPS


# Initialize the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# systemgaurd plan details
plan_details = get_plan_details()

# Define global variables for templates
app.jinja_env.globals.update(
    title=APP_NAME,
    description=DESCRIPTION,
    author=AUTHOR,
    year=YEAR,
    version=VERSION,
    pre_release=PRE_RELEASE,
    project_url=PROJECT_URL,
    contact_email=CONTACT_EMAIL,
    system_name=SYSTEM_NAME,
    system_ip_address=SYSTEM_IP_ADDRESS,
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
    max_users_allowed=plan_details.get('max_users_allowed'),
)

def safe_int_conversion(value, default=0):
    """Safely convert a value to an integer."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def get_app_info():
    """Retrieve application metadata."""
    return {
        "title": APP_NAME,
        "description": DESCRIPTION,
        "author": AUTHOR,
        "year": int(YEAR),
        "version": VERSION,
        "pre_release": PRE_RELEASE,
        "project_url": PROJECT_URL,
        "contact_email": CONTACT_EMAIL,
        "system_name": SYSTEM_NAME,
        "system_ip_address": SYSTEM_IP_ADDRESS,
        "is_plan_not_expired": plan_details.get('is_plan_not_expired'),
        "remaining_plan_days": safe_int_conversion(plan_details.get('remaining_plan_days', 0)),
        "plan_type": plan_details.get('plan_type'),
        "is_trial": plan_details.get('is_trial'),
        "license_key": plan_details.get('license_key'),
        "activation_code": plan_details.get('activation_code'),
        "systemguard_unique_id": plan_details.get('systemguard_unique_id'),
        "max_scrap_target": safe_int_conversion(plan_details.get('max_scrap_target', 0)),
        "max_alert_rules": safe_int_conversion(plan_details.get('max_alert_rules', 0)),
        "max_number_of_graphs": safe_int_conversion(plan_details.get('max_number_of_graphs', 0)),
        "monthly_alert_tickets_limit": safe_int_conversion(plan_details.get('monthly_alert_tickets_limit', 0)),
        "max_users_allowed": safe_int_conversion(plan_details.get('max_users_allowed', 0))
    }
