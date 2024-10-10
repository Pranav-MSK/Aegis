# cython: language_level=3
import os
import csv
from flask import (
    request, 
    jsonify, 
    Blueprint, 
    render_template, 
    Response, 
    stream_with_context, 
    redirect, 
    url_for, 
    flash
)
from src.config import app, csrf
from src.logger import logger

from src.routes.helper.notification_helper import send_test_alert, process_alert
from src.utils import get_ip_address
from src.models import AlertTicket, UserProfile

alert_bp = Blueprint("alert", __name__)

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
def alert_ticket(alert_id):
    alert = AlertTicket.query.get(alert_id)
    if not alert:
        flash('Alert not found!', 'error')
        return redirect(url_for('alert_history'))
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'assign_user':
            alert.assigned_user_id = request.form.get('assigned_user_id')
        elif form_type == 'assign_supervisor':
            alert.assigned_supervisor_id = request.form.get('assigned_supervisor_id')
        elif form_type == 'add_comment':
            alert.investigation_notes = request.form.get('investigation_notes')
        elif form_type == 'add_report':
            alert.report = request.form.get('report')
        elif form_type == 'edit_status':
            alert.status = request.form.get('status')
        elif form_type == 'edit_severity':
            alert.severity = request.form.get('severity')

        alert.save()        
        flash('Changes saved successfully!', 'success')
        return redirect(url_for('alert_ticket', alert_id=alert.id))
    
    return render_template('alerts/alert_ticket.html', alert=alert, 
                           users=UserProfile.query.all(), 
                           admin_users=UserProfile.query.filter_by(user_level='admin').all())


@app.route('/assign_user', methods=['POST'])
def assign_user():
    alert_id = request.form.get('alert_id')
    user_id = request.form.get('assigned_user_id')
    print("Alert ID: ", alert_id)
    print("User ID: ", user_id)
    if alert_id and user_id:
        alert = AlertTicket.query.get(alert_id)
        if alert:
            alert.assigned_user_id = user_id
            alert.save()
            flash('User assigned successfully!', 'success')
            return redirect(url_for('alert_history'))
    flash('Failed to assign user!', 'error')
    return redirect(url_for('alert_history'))


@app.route('/assign_supervisor', methods=['POST'])
def assign_supervisor():
    alert_id = request.form.get('alert_id')
    supervisor_id = request.form.get('assigned_supervisor_id')
    print("Alert ID: ", alert_id)
    print("Supervisor ID: ", supervisor_id)
    if alert_id and supervisor_id:
        alert = AlertTicket.query.get(alert_id)
        if alert:
            alert.assigned_supervisor_id = supervisor_id
            alert.save()
            flash('Supervisor assigned successfully!', 'success')
            return redirect(url_for('alert_history'))
    flash('Failed to assign supervisor!', 'error')
    return redirect(url_for('alert_history'))