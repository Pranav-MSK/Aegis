# cython: language_level=3
from datetime import datetime
from functools import wraps
from http import HTTPStatus

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from src.core.config.app_config import app, csrf, db, get_app_info
from src.helper.basic_info import get_ip_address
from src.helper.logger import get_logger
from src.models import (
    AlertLog,
    AlertTicket,
    CustomFields,
    InvestigationNote,
    SystemNotification,
    UserProfile,
)
from src.schemas import UserNotification
from src.services.alert.alertmanager_adapter import send_test_alert
from src.services.alert.processor import AlertProcessor
from src.services.common_helper import award_points
from src.services.decorators.access_decorators import (
    community_edition,
    systemguard_enterprise,
)
from src.services.notification.manager import (
    fetch_user_notifications,
    generate_system_notification,
)

# Initialize logger
logger = get_logger(__name__)

# Initialize blueprint
alert_bp = Blueprint("alert", __name__)



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

@app.route("/api/v1/check_monthly_alerts")
@login_required
def check_monthly_alerts():
    try:
        # Get the first day of current month at midnight (00:00:00)
        current_date = datetime.now()
        first_date_of_month = current_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Get the first day of next month for upper bound
        if current_date.month == 12:
            next_month = current_date.replace(
                year=current_date.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            next_month = current_date.replace(
                month=current_date.month + 1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        # Query total alerts for current month
        total_alerts = AlertTicket.query.filter(
            AlertTicket.created_at >= first_date_of_month,
            AlertTicket.created_at < next_month,
        ).count()

        # Get monthly limit from config
        monthly_limit = get_app_info().get("monthly_alert_tickets_limit", 100)

        # Check if limit is reached
        limit_reached = total_alerts >= monthly_limit

        response = {
            "status": "success",
            "data": {
                "total_alerts": total_alerts,
                "monthly_limit": monthly_limit,
                "limit_reached": limit_reached,
                "current_month": current_date.strftime("%B %Y"),
                "alerts_remaining": max(0, monthly_limit - total_alerts),
            },
        }

        return jsonify(response), HTTPStatus.OK

    except Exception as e:
        app.logger.error(f"Error checking monthly alerts: {str(e)}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to check monthly alerts",
                    "error": str(e),
                }
            ),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@app.route("/alerts", methods=["POST"])
@csrf.exempt
def receive_alerts():
    """
    Receives and processes incoming alerts from external sources. Alertmanager will 
    send alerts in JSON format to this endpoint.

    Validates the request content type and alert data, logs the alert based on severity,
    and triggers notifications via Slack, email, and Discord.
    """
    if request.headers.get("Content-Type") != "application/json":
        return (
            jsonify({"error": "Unsupported Media Type. Expected application/json"}),
            415,
        )

    try:
        alert_data = request.json
        if not alert_data or "alerts" not in alert_data:
            return jsonify({"error": "No alert data received"}), 400

        for alert in alert_data["alerts"]:
            logger.info(f"Processing alert: {alert}")
            # process_alert(alert)
            AlertProcessor(alert=alert).process()

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.exception(f"Error occurred while processing alert: {e}")
        return (
            jsonify({"error": "An internal error occurred while processing the alert"}),
            500,
        )


@app.route("/alerts/test", methods=["GET"])
@login_required
@community_edition()
def test_alert():
    response = send_test_alert("Test Alert", "warning", "Test Instance")
    return jsonify(response), response.get("status", 500)


@app.route("/system/alerts", methods=["GET", "POST"])
@systemguard_enterprise()
@login_required
def alert_history():
    admin_users = UserProfile.query.filter_by(user_level="admin").all()
    users = UserProfile.query.all()

    if request.method == "POST":
        alert_id = request.form.get("alert_id")
        if alert_id:
            alert = AlertTicket.query.get(alert_id)
            if alert:
                alert.delete()
                flash("Alert deleted successfully!", "success")
            else:
                flash("Alert not found!", "error")
        return redirect(url_for("alert_history"))

    search_query = request.args.get("search", "")
    base_query = AlertTicket.query

    if search_query:
        base_query = base_query.filter(
            db.or_(
                AlertTicket.alert_name.ilike(f"%{search_query}%"),
                AlertTicket.severity.ilike(f"%{search_query}%"),
                AlertTicket.instance.ilike(f"%{search_query}%"),
                AlertTicket.description.ilike(f"%{search_query}%"),
                AlertTicket.summary.ilike(f"%{search_query}%"),
                AlertTicket.alert_status.ilike(f"%{search_query}%"),
                AlertTicket.ticket_status.ilike(f"%{search_query}%"),
                AlertTicket.assigned_user_id.ilike(f"%{search_query}%"),
                AlertTicket.assigned_supervisor_id.ilike(f"%{search_query}%"),
                AlertTicket.fingerprint.ilike(f"%{search_query}%"),
                db.func.date(AlertTicket.created_at).ilike(f"%{search_query}%"),
                db.func.date(AlertTicket.updated_at).ilike(f"%{search_query}%"),
            )
        )

    per_page = 10

    # Pagination for each alert status
    unassigned_page = request.args.get("unassigned_page", 1, type=int)
    open_page = request.args.get("open_page", 1, type=int)
    in_progress_page = request.args.get("in_progress_page", 1, type=int)
    resolved_page = request.args.get("resolved_page", 1, type=int)
    closed_page = request.args.get("closed_page", 1, type=int)

    def paginate_alerts(query, page):
        return query.order_by(
            AlertTicket.updated_at.desc(), AlertTicket.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

    unassigned_alerts = paginate_alerts(
        base_query.filter(AlertTicket.assigned_user_id.is_(None)), unassigned_page
    )
    open_alerts = paginate_alerts(
        base_query.filter(
            AlertTicket.ticket_status == "Open",
            AlertTicket.assigned_user_id.isnot(None),
        ),
        open_page,
    )
    in_progress_alerts = paginate_alerts(
        base_query.filter(
            AlertTicket.ticket_status == "In Progress",
            AlertTicket.assigned_user_id.isnot(None),
        ),
        in_progress_page,
    )
    resolved_alerts = paginate_alerts(
        base_query.filter(
            AlertTicket.ticket_status == "Resolved",
            AlertTicket.assigned_user_id.isnot(None),
        ),
        resolved_page,
    )
    closed_alerts = paginate_alerts(
        base_query.filter(
            AlertTicket.ticket_status == "Closed",
            AlertTicket.assigned_user_id.isnot(None),
        ),
        closed_page,
    )

    # Get counts for unassigned, open, in progress, resolved, and closed alerts
    unassigned_count = base_query.filter(AlertTicket.assigned_user_id.is_(None)).count()
    open_count = base_query.filter(
        AlertTicket.ticket_status == "Open", AlertTicket.assigned_user_id.isnot(None)
    ).count()
    in_progress_count = base_query.filter(
        AlertTicket.ticket_status == "In Progress",
        AlertTicket.assigned_user_id.isnot(None),
    ).count()
    resolved_count = base_query.filter(
        AlertTicket.ticket_status == "Resolved",
        AlertTicket.assigned_user_id.isnot(None),
    ).count()
    closed_count = base_query.filter(
        AlertTicket.ticket_status == "Closed", AlertTicket.assigned_user_id.isnot(None)
    ).count()

    critical_count = base_query.filter(AlertTicket.severity == "critical").count()
    warning_count = base_query.filter(AlertTicket.severity == "warning").count()
    info_count = base_query.filter(AlertTicket.severity == "info").count()

    return render_template(
        "alerts/alert_history.html",
        users=users,
        admin_users=admin_users,
        unassigned_alerts=unassigned_alerts,
        open_alerts=open_alerts,
        in_progress_alerts=in_progress_alerts,
        resolved_alerts=resolved_alerts,
        closed_alerts=closed_alerts,
        search_query=search_query,
        unassigned_count=unassigned_count,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        closed_count=closed_count,
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=info_count,
        current_user=current_user,
    )


@app.route("/system/alerts/<int:alert_id>", methods=["GET", "POST"])
@systemguard_enterprise()
@user_has_access_to_alert
@login_required
def alert_ticket(alert_id):
    alert = AlertTicket.query.get(alert_id)
    if not alert:
        flash("Alert not found!", "error")
        return redirect(url_for("alert_history"))

    if request.method == "POST":
        form_type = request.form.get("form_type")
        log_message = ""

        def log_and_save(message):
            AlertLog(alert_ticket_id=alert_id, log=message).save() # type: ignore

        # User Assignment
        if form_type in ["assign_user", "assign_supervisor"]:
            assigned_user_id = request.form.get(
                "assigned_user_id"
                if form_type == "assign_user"
                else "assigned_supervisor_id"
            )
            previous_user_id = (
                alert.assigned_user_id
                if form_type == "assign_user"
                else alert.assigned_supervisor_id
            )

            if assigned_user_id:
                if form_type == "assign_user":
                    alert.assigned_user_id = assigned_user_id
                    alert.ticket_status = "In Progress"
                    log_message = f"User {user_id_to_username(assigned_user_id)} assigned to alert ticket by {current_user.username}"
                    flash("User assigned successfully!", "success")

                    notification_data = UserNotification(
                        type="info",
                        icon="info-circle",
                        title="Alert Ticket Assignment",
                        message=f"Alert ticket assigned to you by {current_user.first_name} {current_user.last_name}",
                        is_global=False,
                    )
                    generate_system_notification(notification_data, assigned_user_id)
                    award_points("ticket", user_id=assigned_user_id)
                else:
                    alert.assigned_supervisor_id = assigned_user_id
                    log_message = f"Supervisor {user_id_to_username(assigned_user_id)} assigned to alert ticket by {current_user.username}"
                    flash("Supervisor assigned successfully!", "success")
            else:
                if form_type == "assign_user":
                    alert.assigned_user_id = None
                    log_message = f"User {user_id_to_username(previous_user_id)} removed from alert ticket by {current_user.username}"
                    award_points("ticket", reverse=True, user_id=previous_user_id)
                    flash("User removed successfully!", "success")
                else:
                    alert.assigned_supervisor_id = None
                    log_message = f"Supervisor {user_id_to_username(previous_user_id)} removed from alert ticket by {current_user.username}"
                    flash("Supervisor removed successfully!", "success")

            log_and_save(log_message)
            return redirect(url_for("alert_ticket", alert_id=alert.id))

        # Edit Status, Severity, Description, Summary
        elif form_type in [
            "edit_status",
            "edit_severity",
            "edit_description",
            "edit_summary",
        ]:
            new_value = request.form.get(
                "ticket_status"
                if form_type == "edit_status"
                else (
                    "severity"
                    if form_type == "edit_severity"
                    else "description" if form_type == "edit_description" else "summary"
                )
            )

            if new_value in ["Closed", "Resolved"]:
                award_points(new_value.lower(), user_id=alert.assigned_user_id)

            if form_type == "edit_status":
                alert.ticket_status = new_value
                log_message = f"Status changed to '{alert.ticket_status}' by {current_user.username}"
                flash("Status updated successfully!", "success")
            elif form_type == "edit_severity":
                alert.severity = new_value
                log_message = (
                    f"Severity changed to '{alert.severity}' by {current_user.username}"
                )
                flash("Severity updated successfully!", "success")
            elif form_type == "edit_description":
                alert.description = new_value
                log_message = f"Description updated by {current_user.username}"
                flash("Description updated successfully!", "success")
            elif form_type == "edit_summary":
                alert.summary = new_value
                log_message = f"Summary updated by {current_user.username}"
                flash("Summary updated successfully!", "success")

            log_and_save(log_message)
            return redirect(url_for("alert_ticket", alert_id=alert.id))

        # Add Comment
        elif form_type == "add_comment":
            note_content = request.form.get("investigation_notes")
            if note_content:
                InvestigationNote(
                    alert_ticket_id=alert.id, user_id=current_user.id, note=note_content # type: ignore
                ).save()
                log_message = f"Comment added by {current_user.username}"
                log_and_save(log_message)
                flash("Your comment has been added successfully!", "success")
                return redirect(url_for("alert_ticket", alert_id=alert.id))
            else:
                flash("Note cannot be empty!", "error")

        # Custom Fields
        elif form_type in ["add_customfield", "delete_customfield", "edit_customfield"]:
            customfield_id = request.form.get("customfield_id")
            if form_type == "add_customfield":
                field_name = request.form.get("field_name")
                field_value = request.form.get("field_value")
                if field_name and field_value:
                    alert.customfields.append(
                        CustomFields(field_name=field_name, field_value=field_value) # type: ignore
                    )
                    log_message = (
                        f"Custom field '{field_name}' added by {current_user.username}"
                    )
                    flash("Field added successfully!", "success")
                else:
                    flash("Field name and value cannot be empty!", "error")

            elif form_type == "delete_customfield" and customfield_id:
                customfield = CustomFields.query.get(customfield_id)
                if customfield:
                    field_name = customfield.field_name
                    customfield.delete()
                    log_message = f"Custom field '{field_name}' deleted by {current_user.username}"
                    flash("Field deleted successfully!", "success")
                else:
                    flash("Custom field not found!", "error")

            elif form_type == "edit_customfield" and customfield_id:
                customfield = CustomFields.query.get(customfield_id)
                if customfield:
                    field_name = request.form.get("field_name")
                    field_value = request.form.get("field_value")
                    customfield.field_name = field_name
                    customfield.field_value = field_value
                    log_message = f"Custom field '{field_name}' updated by {current_user.username}"
                    flash("Field updated successfully!", "success")
                else:
                    flash("Custom field not found!", "error")

            log_and_save(log_message)
            alert.save()
            return redirect(url_for("alert_ticket", alert_id=alert.id))

        elif form_type in [
            "close_ticket",
            "reopen_ticket",
            "progress_ticket",
            "resolve_ticket",
        ]:
            if form_type == "close_ticket":
                alert.ticket_status = "Closed"
                note_content = request.form.get("investigation_notes")
                award_points("closed", user_id=alert.assigned_user_id)
                if note_content:
                    InvestigationNote(
                        alert_ticket_id=alert.id, # type: ignore
                        user_id=current_user.id, # type: ignore
                        note=note_content, # type: ignore
                    ).save()
                    log_message = (
                        f"Ticket closed as 'Resolved' by {current_user.username}"
                    )
                    flash("Ticket closed successfully!", "success")
                else:
                    flash("Note cannot be empty!", "error")
            elif form_type == "reopen_ticket":
                alert.ticket_status = "Open"
                note_content = request.form.get("investigation_notes")
                if note_content:
                    InvestigationNote(
                        alert_ticket_id=alert.id, # type: ignore
                        user_id=current_user.id, # type: ignore
                        note=note_content, # type: ignore
                    ).save() 
                    log_message = f"Ticket reopened for further investigation by {current_user.username}"
                    flash("Ticket reopened successfully!", "success")
                else:
                    flash("Note cannot be empty!", "error")

            elif form_type == "progress_ticket":
                alert.ticket_status = "In Progress"
                note_content = request.form.get("investigation_notes")
                if note_content:
                    InvestigationNote(
                        alert_ticket_id=alert.id, # type: ignore
                        user_id=current_user.id, # type: ignore
                        note=note_content, # type: ignore
                    ).save()
                    log_message = (
                        f"Ticket marked as 'In Progress' by {current_user.username}"
                    )
                    flash("Ticket marked as in progress successfully!", "success")
                else:
                    flash("Note cannot be empty!", "error")

            elif form_type == "resolve_ticket":
                alert.ticket_status = "Resolved"
                note_content = request.form.get("investigation_notes")
                award_points("resolved", user_id=alert.assigned_user_id)
                if note_content:
                    InvestigationNote(
                        alert_ticket_id=alert.id, # type: ignore
                        user_id=current_user.id, # type: ignore
                        note=note_content, # type: ignore
                    ).save()
                    log_message = (
                        f"Ticket marked as 'Resolved' by {current_user.username}"
                    )
                    flash("Ticket marked as resolved successfully!", "success")
                else:
                    flash("Note cannot be empty!", "error")

            log_and_save(log_message)
            alert.save()
            return redirect(url_for("alert_ticket", alert_id=alert.id))

        elif form_type in ["warning_ticket", "info_ticket", "critical_ticket"]:
            if form_type == "critical_ticket":
                alert.severity = "critical"
                note_content = request.form.get("investigation_notes")
                if note_content:
                    InvestigationNote(
                        alert_ticket_id=alert.id, # type: ignore
                        user_id=current_user.id, # type: ignore
                        note=note_content, # type: ignore
                    ).save()
                    log_message = f"Ticket marked as 'Critical Severity' by {current_user.username}"
                    flash("Ticket marked as critical severity successfully!", "success")
                else:
                    flash("Note cannot be empty!", "error")

            elif form_type == "warning_ticket":
                alert.severity = "warning"
                note_content = request.form.get("investigation_notes")
                if note_content:
                    InvestigationNote(
                        alert_ticket_id=alert.id, # type: ignore
                        user_id=current_user.id, # type: ignore
                        note=note_content, # type: ignore
                    ).save()
                    log_message = f"Ticket marked as 'Warning Severity' by {current_user.username}"
                    flash("Ticket marked as warning severity successfully!", "success")
                else:
                    flash("Note cannot be empty!", "error")

            elif form_type == "info_ticket":
                alert.severity = "info"
                note_content = request.form.get("investigation_notes")
                if note_content:
                    InvestigationNote(
                        alert_ticket_id=alert.id, # type: ignore
                        user_id=current_user.id, # type: ignore
                        note=note_content, # type: ignore
                    ).save()
                    log_message = (
                        f"Ticket marked as 'Info Severity' by {current_user.username}"
                    )
                    flash("Ticket marked as info severity successfully!", "success")
                else:
                    flash("Note cannot be empty!", "error")

            log_and_save(log_message)
            alert.save()
            return redirect(url_for("alert_ticket", alert_id=alert.id))

        elif form_type in ["assign_me", "assign_user"]:
            if form_type == "assign_me":
                assigned_user_id = request.form.get("assigned_user_id")
                if assigned_user_id:
                    alert.assigned_user_id = assigned_user_id
                    alert.ticket_status = "In Progress"
                    log_message = f"User {user_id_to_username(assigned_user_id)} assigned to alert ticket by {current_user.username}"
                    flash("User assigned successfully!", "success")
                else:
                    flash("User not found!", "error")

            elif form_type == "assign_user":
                # assign some user based on load balancer and other factors
                pass

            log_and_save(log_message)
            alert.save()
            return redirect(url_for("alert_ticket", alert_id=alert.id))

        alert.save()
        flash("Changes saved successfully!", "success")
        return redirect(url_for("alert_ticket", alert_id=alert.id))

    # Pagination parameters for alert logs and investigation notes
    logs_page = request.args.get("logs_page", 1, type=int)
    logs_per_page = request.args.get("logs_per_page", 10, type=int)
    notes_page = request.args.get("notes_page", 1, type=int)
    notes_per_page = request.args.get("notes_per_page", 10, type=int)

    alert_logs = (
        AlertLog.query.filter_by(alert_ticket_id=alert_id)
        .order_by(AlertLog.created_at.desc())
        .paginate(page=logs_page, per_page=logs_per_page, error_out=False)
    )
    investigation_notes = (
        InvestigationNote.query.filter_by(alert_ticket_id=alert_id)
        .order_by(InvestigationNote.created_at.desc())
        .paginate(page=notes_page, per_page=notes_per_page, error_out=False)
    )

    return render_template(
        "alerts/alert_ticket.html",
        alert=alert,
        users=UserProfile.query.all(),
        admin_users=UserProfile.query.filter_by(user_level="admin").all(),
        current_user=current_user,
        alert_logs=alert_logs,
        investigation_notes=investigation_notes,
    )


@app.route("/api/v1/mark_notification/<int:notification_id>", methods=["POST"])
@csrf.exempt
@login_required
def mark_notification(notification_id):
    user_id = current_user.id

    user_notification = SystemNotification.query.filter_by(
        user_id=user_id, notification_id=notification_id
    ).first()
    if user_notification:
        user_notification.unread = False  # Mark as read
        db.session.commit()
        # flash("Notification marked as read!", "success")
        return jsonify({"message": "Notification marked as read!"}), 200
    else:
        return jsonify({"message": "Notification not found for user."}), 404

@app.route("/api/v1/mark_all_notifications", methods=["POST"])
@csrf.exempt
@login_required
def mark_all_notifications():
    user_id = current_user.id

    user_notifications = SystemNotification.query.filter_by(user_id=user_id, unread=True).all()
    for user_notification in user_notifications:
        user_notification.unread = False
    user_notification.save() # type: ignore

    return jsonify({"message": "All notifications marked as read!"}), 200


@app.route("/api/v1/system/notifications/", methods=["GET"])
@login_required
def show_all_notifications():
    """API endpoint to retrieve user notifications with optional query parameters."""
    try:
        unread_only = request.args.get("unread_only", "true").lower() == "true"
        limit = min(int(request.args.get("limit", 50)), 100)  # Cap at 100
        offset = max(int(request.args.get("offset", 0)), 0)  # Ensure non-negative

        notifications = fetch_user_notifications(
            user_id=current_user.id, unread_only=unread_only, limit=limit, offset=offset
        )

        return jsonify(notifications), 200
    except Exception as e:
        return (
            jsonify({"error": "Failed to retrieve notifications", "message": str(e)}),
            500,
        )


@app.route("/api/v1/system/notifications/<int:notification_id>", methods=["GET"])
@login_required
def get_notification(notification_id):
    user_id = current_user.id
    user_notification = SystemNotification.query.filter_by(
        user_id=user_id, notification_id=notification_id
    ).first()
    if user_notification:
        return jsonify(user_notification.notification.to_dict()), 200
    else:
        return jsonify({"message": "Notification not found for user."}), 404
