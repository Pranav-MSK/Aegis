# cython: language_level=3
import os
import hashlib
import markdown
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from humanize import naturaltime

from src.disk_manager import DiskMetrics
from src.network_manager import NetworkMetrics
from src.helper import get_system_node_name, get_ip_address, load_secret_key
from src.activator import get_plan_details

# disk and metrics background process
disk_metrics = DiskMetrics()
disk_metrics.start()
network_metrics = NetworkMetrics()
network_metrics.start()

app = Flask(__name__)

# Application Metadata
APP_NAME = "SystemGuard"
DESCRIPTION = f"{APP_NAME} is a web application that allows you to monitor, analyze, and manage your system resources."
AUTHOR = "{} Team".format(APP_NAME)
YEAR = datetime.now().year
PRE_RELEASE = False
VERSION = "v1.0.0"
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
app.config['under_maintenance'] = False


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


@app.template_filter()
def natural_time(value):
    """Convert a datetime object to a human-readable format."""
    if isinstance(value, datetime):
        return naturaltime(value)
    return value

@app.template_filter()
def get_profile_picture_url(email, size=200):
    # Create an MD5 hash of the email address
    email_hash = hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"


# Define a custom filter to convert Markdown to HTML
@app.template_filter('markdown')
def markdown_filter(content):
    return markdown.markdown(content, extensions=['fenced_code', 'tables'])