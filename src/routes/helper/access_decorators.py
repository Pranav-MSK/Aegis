# cython: language_level=3
from functools import wraps
from typing import Optional
from flask import abort, current_app

class PlanAuthorizationError(Exception):
    """Custom exception for plan authorization failures."""
    pass

class PlanAuthorization:
    """Handler for plan-based authorization."""
    
    PLAN_HIERARCHY = [
        "Free",
        "Community",
        "Core", 
        "Plus",
        "Enterprise"
    ]

    @classmethod
    def get_current_plan(cls) -> str:
        """
        Get the current user's plan type from the activator.
        Falls back to Free Edition if plan details cannot be retrieved.
        """
        try:
            from src.activator import get_plan_details
            plan_details = get_plan_details()
            return plan_details.get("plan_type") if plan_details else "Free Edition"
        except Exception as e:
            current_app.logger.error(f"Failed to get plan details: {str(e)}")
            return "Free Edition"

    @classmethod
    def check_plan_access(cls, required_plan: str) -> bool:
        """
        Check if the current plan has access to the required plan level.
        
        Args:
            required_plan: The minimum plan level required
            
        Returns:
            bool: True if access is allowed, False otherwise
        """
        try:
            current_plan = cls.get_current_plan()
            return cls.PLAN_HIERARCHY.index(current_plan) >= cls.PLAN_HIERARCHY.index(required_plan)
        except ValueError as e:
            current_app.logger.error(f"Invalid plan type encountered: {str(e)}")
            return False

    @classmethod
    def requires_plan(cls, required_plan: str):
        """
        Decorator to enforce minimum plan requirements for routes.
        
        Args:
            required_plan: The minimum plan level required to access the route
            
        Returns:
            decorator: The decorated function with plan checks
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                current_plan = cls.get_current_plan()

                if not cls.check_plan_access(required_plan):
                    abort(403, description=(
                        f"This feature requires {required_plan} or higher. "
                        f"Your current plan is: {current_plan}"
                    ))
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# Convenience decorators for specific plan levels
def free_edition():
    """Decorator for Free Edition features."""
    return PlanAuthorization.requires_plan("Free")

def community_edition():
    """Decorator for Community Edition features."""
    return PlanAuthorization.requires_plan("Community")

def systemguard_core():
    """Decorator for SystemGuard Core features."""
    return PlanAuthorization.requires_plan("Core")

def systemguard_plus():
    """Decorator for SystemGuard Plus features."""
    return PlanAuthorization.requires_plan("Plus")

def systemguard_enterprise():
    """Decorator for SystemGuard Enterprise features."""
    return PlanAuthorization.requires_plan("Enterprise")