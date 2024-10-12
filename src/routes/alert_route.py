# cython: language_level=3
from flask import request, jsonify, Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from src.config import app, csrf, db
from src.logger import logger

from src.routes.helper.notification_helper import send_test_alert, process_alert
from src.utils import get_ip_address
from src.models import AlertTicket, UserProfile, InvestigationNote, AlertLog, CustomFields
from functools import wraps
from flask import abort

alert_bp = Blueprint("alert", __name__)


def paginate_alerts(status, page, per_page=10):
    return AlertTicket.query.filter_by(status=status).paginate(
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


@app.route("/alerts", methods=["POST"])
@csrf.exempt
def receive_alerts():
    """
    Receives and processes incoming alerts from external sources.

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
            process_alert(alert)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.exception(f"Error occurred while processing alert: {e}")
        return (
            jsonify({"error": "An internal error occurred while processing the alert"}),
            500,
        )


@app.route("/alerts/test", methods=["GET"])
def test_alert():
    alertmanager_ip = get_ip_address()
    alertmanager_port = "9093"
    alertmanager_url = f"http://{alertmanager_ip}:{alertmanager_port}"

    response = send_test_alert(
        alertmanager_url, "Test Alert", "warning", "Test Instance"
    )
    return jsonify(response), response.get("status", 500)


@app.route("/alerts/ticket", methods=["GET", "POST"])
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
                AlertTicket.alert_name.contains(search_query),
                AlertTicket.severity.contains(search_query),
                AlertTicket.instance.contains(search_query),
                AlertTicket.description.contains(search_query),
                AlertTicket.summary.contains(search_query),
                AlertTicket.status.contains(search_query),
                AlertTicket.assigned_user_id.contains(search_query),
                AlertTicket.assigned_supervisor_id.contains(search_query),
                AlertTicket.created_at.contains(search_query),
                AlertTicket.updated_at.contains(search_query),
            )
        )

    per_page = 10

    # Pagination for each alert status
    unassigned_page = request.args.get("unassigned_page", 1, type=int)
    open_page = request.args.get("open_page", 1, type=int)
    in_progress_page = request.args.get("in_progress_page", 1, type=int)
    resolved_page = request.args.get("resolved_page", 1, type=int)
    closed_page = request.args.get("closed_page", 1, type=int)


    unassigned_alerts = base_query.filter(AlertTicket.assigned_user_id.is_(None)).paginate(
        page=unassigned_page, per_page=per_page, error_out=False
    )
    open_alerts = base_query.filter(AlertTicket.status == "Open",
                                    AlertTicket.assigned_user_id.isnot(None)).paginate(
        page=open_page, per_page=per_page, error_out=False
    )
    in_progress_alerts = base_query.filter(
        AlertTicket.status == "In Progress", AlertTicket.assigned_user_id.isnot(None)
    ).paginate(page=in_progress_page, per_page=per_page, error_out=False)
    resolved_alerts = base_query.filter(
        AlertTicket.status == "Resolved", AlertTicket.assigned_user_id.isnot(None)
    ).paginate(page=resolved_page, per_page=per_page, error_out=False)
    closed_alerts = base_query.filter(
        AlertTicket.status == "Closed", AlertTicket.assigned_user_id.isnot(None)
    ).paginate(page=closed_page, per_page=per_page, error_out=False)

    # Get counts for unassigned, open, in progress, resolved, and closed alerts
    unassigned_count = base_query.filter(AlertTicket.assigned_user_id.is_(None)).count()
    open_count = base_query.filter(
        AlertTicket.status == "Open", AlertTicket.assigned_user_id.isnot(None)
    ).count()
    in_progress_count = base_query.filter(
        AlertTicket.status == "In Progress", AlertTicket.assigned_user_id.isnot(None)
    ).count()
    resolved_count = base_query.filter(
        AlertTicket.status == "Resolved", AlertTicket.assigned_user_id.isnot(None)
    ).count()
    closed_count = base_query.filter(
        AlertTicket.status == "Closed", AlertTicket.assigned_user_id.isnot(None)
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
    )

@app.route("/alerts/ticket/<int:alert_id>", methods=["GET", "POST"])
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
            AlertLog(alert_ticket_id=alert_id, log=message).save()

        # User Assignment
        if form_type in ["assign_user", "assign_supervisor"]:
            assigned_user_id = request.form.get("assigned_user_id" if form_type == "assign_user" else "assigned_supervisor_id")
            previous_user_id = alert.assigned_user_id if form_type == "assign_user" else alert.assigned_supervisor_id

            if assigned_user_id:
                if form_type == "assign_user":
                    alert.assigned_user_id = assigned_user_id
                    log_message = f"User {user_id_to_username(assigned_user_id)} assigned to alert ticket by {current_user.username}"
                    flash("User assigned successfully!", "success")
                else:
                    alert.assigned_supervisor_id = assigned_user_id
                    log_message = f"Supervisor {user_id_to_username(assigned_user_id)} assigned to alert ticket by {current_user.username}"
                    flash("Supervisor assigned successfully!", "success")
            else:
                if form_type == "assign_user":
                    alert.assigned_user_id = None
                    log_message = f"User {user_id_to_username(previous_user_id)} removed from alert ticket by {current_user.username}"
                    flash("User removed successfully!", "success")
                else:
                    alert.assigned_supervisor_id = None
                    log_message = f"Supervisor {user_id_to_username(previous_user_id)} removed from alert ticket by {current_user.username}"
                    flash("Supervisor removed successfully!", "success")

            log_and_save(log_message)
            return redirect(url_for("alert_ticket", alert_id=alert.id))

        # Edit Status, Severity, Description, Summary
        elif form_type in ["edit_status", "edit_severity", "edit_description", "edit_summary"]:
            new_value = request.form.get("status" if form_type == "edit_status" else
                                           "severity" if form_type == "edit_severity" else
                                           "description" if form_type == "edit_description" else
                                           "summary")
            if form_type == "edit_status":
                alert.status = new_value
                log_message = f"Status changed to '{alert.status}' by {current_user.username}"
                flash("Status updated successfully!", "success")
            elif form_type == "edit_severity":
                alert.severity = new_value
                log_message = f"Severity changed to '{alert.severity}' by {current_user.username}"
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
                InvestigationNote(alert_ticket_id=alert.id, user_id=current_user.id, note=note_content).save()
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
                    alert.customfields.append(CustomFields(field_name=field_name, field_value=field_value))
                    log_message = f"Custom field '{field_name}' added by {current_user.username}"
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

        # Save changes
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
