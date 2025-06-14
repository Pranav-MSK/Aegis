# cython: language_level=3
from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

from src.models import AlertTicket, UserProfile
from src.helper.logger import get_logger
logger = get_logger(__name__)



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
