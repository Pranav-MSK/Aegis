from functools import wraps
from flask import abort
from src.config import plan_details

# Get the current user's plan type
current_plan = plan_details["plan_type"]

# All plan types in increasing order of privileges
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
    """Decorator to check if the user has the required plan."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if is_plan_allowed(required_plan):
                return f(*args, **kwargs)
            else:
                # Abort with 403 to trigger the custom 403 error page
                abort(403, description="You do not have the required plan to access this resource. Current Plan: {}\nRequired Plan: {}".format(current_plan, required_plan))
        return decorated_function
    return decorator

# Specific decorators for each plan type
def free_edition():
    return plan_decorator("Free Edition")

def community_edition():
    return plan_decorator("Community Edition")

def systemguard_core():
    return plan_decorator("SystemGuard Core")

def systemguard_plus():
    return plan_decorator("SystemGuard Plus")

def systemguard_enterprise():
    return plan_decorator("SystemGuard Enterprise")
