from functools import wraps
from flask import jsonify

# Current user's plan
current_plan = "SystemguardBasic"

# All plan types in increasing order
all_plan_types = [
    "Free Edition",
    "Community Edition",
    "SystemGuard Core",
    "SystemGuard Plus",
    "SystemGuard Enterprise"
]

def is_plan_allowed(required_plan):
    """Check if the user's plan is at or above the required plan."""
    return all_plan_types.index(current_plan) >= all_plan_types.index(required_plan)

def plan_decorator(required_plan):
    """Generic decorator to check if the user has the required plan."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if is_plan_allowed(required_plan):
                return f(*args, **kwargs)
            else:
                return jsonify({"error": "You do not have permission to view this page."}), 403
        return decorated_function
    return decorator

# Specific decorators for each plan type
def free_edition():
    return plan_decorator("Free Edition")

def community_edition():
    return plan_decorator("Community Edition")

def systemguard_core():
    return plan_decorator("Systemguard Core")

def systemguard_plus():
    return plan_decorator("Systemguard Plus")

def systemguard_enterprise():
    return plan_decorator("Systemguard Enterprise")
