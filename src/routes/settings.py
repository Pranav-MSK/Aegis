# cython: language_level=3
import os
import datetime
import subprocess
from flask import render_template, request, flash, blueprints, redirect, url_for, session

from src.config.app_config import app, csrf
from src.models import UserDashboardSettings, GeneralSettings
from flask_login import login_required, current_user
from src.helper.template_utils import render_template_from_file, ROOT_DIR
from src.services.messaging.email_service import send_smtp_email
from src.routes.helper.common_helper import (
    get_email_addresses, 
    admin_required, 
    handle_sudo_password)

from src.config.app_config import get_app_info

settings_bp = blueprints.Blueprint("settings", __name__)

@app.route("/control_panel", methods=["GET", "POST"])
@login_required
def settings():
    return render_template("settings/control_panel.html", settings=settings)

@app.route('/control_panel/speedtest', methods=['GET', 'POST'])
@login_required
def user_settings():
    user_dashboard_settings = UserDashboardSettings.query.filter_by(user_id=current_user.id).first()  # Retrieve user-specific settings from DB
    if request.method == 'POST':
        user_dashboard_settings.speedtest_cooldown = request.form.get('speedtest_cooldown') # type: ignore
        user_dashboard_settings.number_of_speedtests = request.form.get('number_of_speedtests') # type: ignore
        user_dashboard_settings.refresh_interval = request.form.get('refresh_interval') # type: ignore
        user_dashboard_settings.save() # type: ignore
        flash('Speedtest settings updated successfully!', 'success')
        return redirect(url_for('user_settings'))
    return render_template('settings/user_settings.html', user_dashboard_settings=user_dashboard_settings)

@app.route('/control_panel/general', methods=['GET', 'POST'])
@admin_required
def general_settings():
    # Retrieve user-specific settings from DB
    general_settings = GeneralSettings.query.filter_by().first()
    # Store the current state of the 'enable_alerts' setting
    current_alert_status = general_settings.enable_alerts # type: ignore
    if request.method == 'POST':
        # Update the settings from the form
        general_settings.timezone = request.form.get('timezone') # type: ignore
        general_settings.enable_cache = 'enable_cache' in request.form # type: ignore
        general_settings.enable_alerts = 'enable_alerts' in request.form # type: ignore
        general_settings.is_logging_system_info = 'is_logging_system_info' in request.form # type: ignore

        # Check if the 'enable_alerts' status has changed
        if current_alert_status != general_settings.enable_alerts: # type: ignore
            # If 'enable_alerts' was changed, send an email to the admins
            admin_emails_with_alerts = get_email_addresses(user_level="admin", receive_email_alerts=True)
            if admin_emails_with_alerts:
                subject = f"{get_app_info()['title']} Alert Status Changed"
                context = {
                    "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "notifications_enabled": general_settings.enable_alerts, # type: ignore
                    "current_user": current_user.username,
                    "title": get_app_info()["title"],
                }
                notification_alert_template = os.path.join(ROOT_DIR, "src/templates/email_templates/notification_alert.html")
                email_body = render_template_from_file(notification_alert_template, **context)
                
                # Send email only if 'enable_alerts' changed
                send_smtp_email(admin_emails_with_alerts, subject, email_body, is_html=True, bypass_alerts=True)
        # Save the updated settings to the database
        general_settings.save() # type: ignore
        flash('General settings updated successfully!', 'success')
        return redirect(url_for('general_settings'))

    return render_template('settings/general_settings.html', general_settings=general_settings)


@app.route('/api/v1/utility', methods=['POST'])
@admin_required
@csrf.exempt
def utility_control_api():
    # Retrieve the saved sudo password from session
    sudo_password = session.get('sudo_password', '')
    if not sudo_password:
        return {"error": "Please enter the sudo password to proceed."}, 400

    # Handle action (shutdown or reboot)
    # action = request.json.get('action')

    json_data = request.get_json(silent=True)
    if not json_data or 'action' not in json_data:
        return {"error": "Invalid or missing JSON payload!"}, 400
    action = json_data.get('action')
    
    if action == 'shutdown':
        command = ['sudo', '-S', 'shutdown', '-h', 'now']
        success_message = "Server is shutting down..."
        error_message = "Failed to shutdown: {}"
    elif action == 'reboot':
        command = ['sudo', '-S', 'reboot']
        success_message = "Server is rebooting..."
        error_message = "Failed to reboot: {}"
    else:
        return {"error": "Invalid action!"}, 400

    # Execute the command
    try:
        result = subprocess.run(command, input=sudo_password + '\n', check=True, capture_output=True, text=True)
        return {"message": success_message, "success": True}
    
    except subprocess.CalledProcessError as e:
        return {"error": error_message.format(e)}, 400

@app.route('/utility', methods=['GET', 'POST'])
@admin_required
@handle_sudo_password("utility_control")
def utility_control():
    if request.method == 'POST':
        # Retrieve the saved sudo password from session
        sudo_password = session.get('sudo_password', '')
        if not sudo_password:
            flash("Please enter the sudo password to proceed.", 'danger')
            return redirect(url_for('utility_control'))

        # Handle action (shutdown or reboot)
        action = request.form.get('action')
        if action == 'shutdown':
            command = ['sudo', '-S', 'shutdown', '-h', 'now']
            success_message = "Server is shutting down..."
            error_message = "Failed to shutdown: {}"
        elif action == 'reboot':
            command = ['sudo', '-S', 'reboot']
            success_message = "Server is rebooting..."
            error_message = "Failed to reboot: {}"
        else:
            flash("Invalid action!", 'danger')
            return redirect(url_for('utility_control'))

        # Execute the command
        try:
            result = subprocess.run(command, input=sudo_password + '\n', check=True, capture_output=True, text=True)
            flash(success_message, 'info')
        except subprocess.CalledProcessError as e:
            flash(error_message.format(e), 'danger')

    # Render the control form on GET request
    return render_template("settings/utility.html")

@app.route('/superadmin', methods=['GET', 'POST'])
@admin_required
@handle_sudo_password("superadmin")
def superadmin():
    return redirect(url_for('view_profile', user_id=current_user.id))

