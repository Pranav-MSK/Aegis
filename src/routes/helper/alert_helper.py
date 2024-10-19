# cython: language_level=3
from functools import wraps
from datetime import datetime
from flask import flash, redirect, url_for, abort
from flask_login import current_user

from src.models import AlertTicket, UserProfile
from src.logger import logger
from src.config import get_app_info


def paginate_alerts(ticket_status, page, per_page=10):
    return AlertTicket.query.filter_by(ticket_status=ticket_status).paginate(
        page=page, per_page=per_page, error_out=False
    )


def user_has_access_to_alert(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        alert_id = kwargs.get("alert_id")
        alert = AlertTicket.query.get(alert_id)

        if not alert:
            flash("Alert not found!", "error")
            return redirect(url_for("alert_history"))

        if current_user.user_level != "admin" and current_user.id not in {
            alert.assigned_user_id,
            alert.assigned_supervisor_id,
        }:
            abort(403, description="You do not have access to this alert ticket.")

        return f(*args, **kwargs)

    return decorated_function


def user_id_to_username(user_id):
    user = UserProfile.query.get(user_id)
    return user.username if user else "Unknown"


def can_create_alert():
    try:
        current_date = datetime.now()
        first_date_of_month = current_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        if current_date.month == 12:
            next_month = current_date.replace(
                year=current_date.year + 1, month=1, day=1
            )
        else:
            next_month = current_date.replace(month=current_date.month + 1, day=1)

        total_alerts = AlertTicket.query.filter(
            AlertTicket.created_at >= first_date_of_month,
            AlertTicket.created_at < next_month,
        ).count()

        monthly_limit = get_app_info().get("monthly_alert_tickets_limit", 100)

        return total_alerts < monthly_limit

    except Exception as e:
        logger.error(f"Error checking monthly alerts: {str(e)}")
        return False  # Fail safe - don't create alert if there's an error
