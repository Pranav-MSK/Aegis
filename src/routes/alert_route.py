# cython: language_level=3
from flask import (
    request, 
    jsonify, 
    Blueprint, 
    render_template, 
    redirect, 
    url_for, 
    flash
)
from flask_login import current_user, login_required
from src.config import app, csrf
from src.logger import logger

from src.routes.helper.notification_helper import send_test_alert, process_alert
from src.utils import get_ip_address
from src.models import AlertTicket, UserProfile, InvestigationNote, Report, AlertLog
from functools import wraps
from flask import abort

alert_bp = Blueprint("alert", __name__)


def user_has_access_to_alert(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        alert_id = kwargs.get('alert_id')
        alert = AlertTicket.query.get(alert_id)
        if not alert:
            flash('Alert not found!', 'error')
            return redirect(url_for('alert_history'))

        if current_user.user_level != 'admin' and current_user.id not in [alert.assigned_user_id, alert.assigned_supervisor_id]:
            abort(403, description="You do not have access to this alert ticket.")

        return f(*args, **kwargs)
    return decorated_function

def user_id_to_username(user_id):
    user = UserProfile.query.get(user_id)
    return user.username if user else 'Unknown'

@app.route("/alerts", methods=["POST"])
@csrf.exempt
def receive_alerts():
    """
    Receives and processes incoming alerts from external sources.

    Validates the request content type and alert data, logs the alert based on severity,
    and triggers notifications via Slack, email, and Discord.

    Returns:
        JSON response indicating the result of alert processing:
        - 200 if successfully processed
        - 400 if alert data is missing
        - 415 if the content type is not application/json
        - 500 if an internal server error occurs
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
        logger.exception("Error occurred while processing alert, error: {}".format(e))
        return (
            jsonify({"error": "An internal error occurred while processing the alert"}),
            500,
        )

@app.route("/alerts/test", methods=["GET"])
def test_alert():
    alertmanager_ip = get_ip_address()
    alertmanager_port = "9093"
    alertmanager_url = f"http://{alertmanager_ip}:{alertmanager_port}"

    # Send a test alert with a unique name
    response = send_test_alert(alertmanager_url, "Test Alert", "warning", "Test Instance")
    return jsonify(response), response.get("status", 500)

@app.route('/alerts/ticket', methods=['GET', 'POST'])
@login_required
def alert_history():
    admin_users = UserProfile.query.filter_by(user_level="admin").all()
    users = UserProfile.query.filter_by().all()

    if request.method == 'POST':
        alert_id = request.form.get('alert_id')
        if alert_id:  # Check if alert_id is provided
            alert = AlertTicket.query.get(alert_id)
            if alert:
                alert.delete()  # Assuming delete() is a method of the model
                flash('Alert deleted successfully!', 'success')  # Add success message
            else:
                flash('Alert not found!', 'error')  # Add error message for not found
        return redirect(url_for('alert_history'))

    # Get search query
    search_query = request.args.get('search', '')
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Fetch alerts with pagination and filtering based on search
    if search_query:
        alert_data = AlertTicket.query.filter(
            AlertTicket.alert_name.contains(search_query) | 
            AlertTicket.severity.contains(search_query) |
            AlertTicket.instance.contains(search_query) |
            AlertTicket.description.contains(search_query) |
            AlertTicket.summary.contains(search_query) |
            AlertTicket.status.contains(search_query) |
            AlertTicket.investigation_notes.contains(search_query) |
            AlertTicket.report.contains(search_query) |
            AlertTicket.assigned_user_id.contains(search_query) |
            AlertTicket.assigned_supervisor_id.contains(search_query) |
            AlertTicket.created_at.contains(search_query) |
            AlertTicket.updated_at.contains(search_query)
        ).paginate(page=page, per_page=per_page, error_out=False)
    else:
        alert_data = AlertTicket.query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('alerts/alert_history.html', 
                           alerts=alert_data.items, 
                           pagination=alert_data,
                           users=users,
                           admin_users=admin_users)



@app.route('/alerts/ticket/<int:alert_id>', methods=['GET', 'POST'])
@user_has_access_to_alert
@login_required
def alert_ticket(alert_id):

    alert = AlertTicket.query.get(alert_id)
    if not alert:
        flash('Alert not found!', 'error')
        return redirect(url_for('alert_history'))

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        log_message = ""
        
        # Helper function to log changes
        def log_and_save(message):
            nonlocal log_message
            log_message = message
            alert_log = AlertLog(alert_ticket_id=alert_id, log=log_message)
            alert_log.save()

        # Assign user and supervisor logic
        if form_type in ['assign_user', 'assign_supervisor']:
            assigned_user_id = request.form.get('assigned_user_id') if form_type == 'assign_user' else request.form.get('assigned_supervisor_id')
            previous_user_id = alert.assigned_user_id if form_type == 'assign_user' else alert.assigned_supervisor_id
            
            if assigned_user_id:
                if form_type == 'assign_user':
                    alert.assigned_user_id = assigned_user_id
                    log_message = f"User {user_id_to_username(assigned_user_id)} assigned to alert ticket by {current_user.username}"
                else:
                    alert.assigned_supervisor_id = assigned_user_id
                    log_message = f"Supervisor {user_id_to_username(assigned_user_id)} assigned to alert ticket by {(current_user.username)}"
            else:
                if form_type == 'assign_user':
                    alert.assigned_user_id = None
                    log_message = f"User {user_id_to_username(previous_user_id)} removed from alert ticket by {(current_user.username)}"
                else:
                    alert.assigned_supervisor_id = None
                    log_message = f"Supervisor {user_id_to_username(previous_user_id)} removed from alert ticket by {(current_user.username)}"
                
            log_and_save(log_message)

        # Edit status and severity logic
        elif form_type in ['edit_status', 'edit_severity', 'edit_description']:
            if form_type == 'edit_status':
                new_status = request.form.get('status')
                alert.status = new_status
                log_message = f"Status changed to '{alert.status}' by {current_user.username}"
            elif form_type == 'edit_severity':
                new_severity = request.form.get('severity')
                alert.severity = new_severity
                log_message = f"Severity changed to '{alert.severity}' by {current_user.username}"
            elif form_type == 'edit_description':
                new_description = request.form.get('description')
                alert.description = new_description
                log_message = f"Description updated by {current_user.username}"

            log_and_save(log_message)

        # Add comment (investigation notes)
        elif form_type == 'add_comment':
            note_content = request.form.get('investigation_notes')  # Ensure this matches the name in your form
            if note_content:  # Check if the note is not empty
                note = InvestigationNote(alert_ticket_id=alert.id, user_id=current_user.id, note=note_content)
                note.save()
                log_message = f"Comment added by {current_user.username}"  
                log_and_save(log_message)
            else:
                flash('Note cannot be empty!', 'error')

        alert.save()
        flash('Changes saved successfully!', 'success')
        return redirect(url_for('alert_ticket', alert_id=alert.id))

     # Pagination parameters for alert logs
    logs_page = request.args.get('logs_page', 1, type=int)
    logs_per_page = request.args.get('logs_per_page', 10, type=int)

    # Pagination parameters for investigation notes
    notes_page = request.args.get('notes_page', 1, type=int)
    notes_per_page = request.args.get('notes_per_page', 10, type=int)

    # Fetch alert logs with pagination
    alert_logs = AlertLog.query.filter_by(alert_ticket_id=alert_id).order_by(AlertLog.created_at.desc()).paginate(page=logs_page, per_page=logs_per_page, error_out=False)

    # Fetch investigation notes with pagination
    investigation_notes = InvestigationNote.query.filter_by(alert_ticket_id=alert_id).order_by(InvestigationNote.created_at.desc()).paginate(page=notes_page, per_page=notes_per_page, error_out=False)

    return render_template('alerts/alert_ticket.html', alert=alert,
                           users=UserProfile.query.all(),
                           admin_users=UserProfile.query.filter_by(user_level='admin').all(),
                           current_user=current_user,
                           alert_logs=alert_logs,
                           investigation_notes=investigation_notes)

