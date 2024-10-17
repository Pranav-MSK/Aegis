# cython: language_level=3
import os
import subprocess
from flask import render_template, request, jsonify, flash, blueprints, redirect, url_for, session
from flask_login import login_required

from src.models import GeneralSettings
from src.config import app
from src.routes.helper.common_helper import get_email_addresses
from src.alert_manager import send_smtp_email
from src.utils import get_os_release_info, get_os_info
from src.helper import check_installation_information
from src.routes.helper.common_helper import admin_required
from src.activator import calculate_unique_system_id

other_bp = blueprints.Blueprint('other', __name__)

@app.route('/terminal', methods=['GET', 'POST'])
@admin_required
def terminal():
    if request.method == 'POST':
        command = request.form.get('command')
        if command:
            try:
                # Run the command and capture the output
                output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
            except subprocess.CalledProcessError as e:
                # If the command fails, capture the error output
                output = e.output
            return jsonify(output=output)
    return render_template('other/terminal.html')


@app.route("/send_email", methods=["GET", "POST"])
@admin_required
def send_email_page():
    receiver_email = get_email_addresses(user_level='admin', receive_email_alerts=True)    
    general_settings = GeneralSettings.query.first()
    if general_settings:
        enable_alerts = general_settings.enable_alerts
    if request.method == "POST":
        receiver_email = request.form.get("recipient")
        subject = request.form.get("subject")
        body = request.form.get("body")
        priority = request.form.get("priority")
        attachment = request.files.get("attachment")

        if not receiver_email or not subject or not body:
            flash("Please provide recipient, subject, and body.", "danger")
            return redirect(url_for('send_email_page'))
        
        # on high priority, send to all users or admin users even the receive_email_alerts is False
        if priority == "high" and receiver_email == "all_users":
            receiver_email = get_email_addresses(fetch_all_users=True)
        elif priority == "high" and receiver_email == "admin_users":
            receiver_email = get_email_addresses(user_level='admin', fetch_all_users=True)

        # priority is low, send to users with receive_email_alerts is True
        if priority == "low" and receiver_email == "all_users":
            receiver_email = get_email_addresses(receive_email_alerts=True)
        elif priority == "low" and receiver_email == "admin_users":
            receiver_email = get_email_addresses(user_level='admin', receive_email_alerts=True)

        if not receiver_email:
            flash("No users found to send email to.", "danger")
            return redirect(url_for('send_email_page'))
        
        # Save attachment if any
        attachment_path = None
        if attachment:
            attachment_path = f"/tmp/{attachment.filename}"
            attachment.save(attachment_path)
        try:
            respose = send_smtp_email(receiver_email, subject, body, attachment_path)
            if respose and respose.get("status") == "success":
                flash(respose.get("message"), "success")
        except Exception as e:
            flash(f"Failed to send email: {str(e)}", "danger")
        
        return redirect(url_for('send_email_page'))

    return render_template("other/send_email.html", enable_alerts=enable_alerts)

def fetch_bashrc_variable(variable_name):
    """
    Fetch the value of a given environment variable from the ~/.bashrc file.

    Args:
        variable_name (str): The name of the environment variable to fetch.

    Returns:
        str: The value of the environment variable if found, otherwise None.
    """
    bashrc_path = os.path.expanduser("~/.bashrc")
    
    if not os.path.exists(bashrc_path):
        raise FileNotFoundError(f"{bashrc_path} does not exist")

    with open(bashrc_path, "r") as file:
        for line in file:
            # Look for lines that set the variable
            if line.strip().startswith(f"{variable_name}="):
                # Extract the variable value
                parts = line.strip().split('=', 1)
                if len(parts) == 2:
                    return parts[1].strip().strip('"').strip("'")
    
    return None

@app.route("/about")
def about():
    installation_info = check_installation_information()
    # fetch sg_installation_method from .bashrc file
    sg_installation_method = fetch_bashrc_variable("sg_installation_method")
    installation_info["sg_installation_method"] = sg_installation_method
    systemguard_unique_id = calculate_unique_system_id()
    session['systemguard_unique_id'] = systemguard_unique_id
    
    return render_template("other/about.html", 
                            installation_info=installation_info,
                            systemguard_unique_id=systemguard_unique_id)


@app.route('/os_info', methods=['GET'])
@login_required
def show_os_info():
    # Fetch OS level information
    os_info = get_os_info()
    os_info.update(get_os_release_info())
    
    # Render the HTML page with the OS information
    return render_template('info_pages/os_info.html', os_info=os_info)

# terms
@app.route('/terms')
def terms():
    return render_template('other/terms.html')

@app.route('/privacy')
def privacy():
    return render_template('other/privacy.html')


# @app.route('/plan')
# def plan():
#     return render_template('other/plan.html')

