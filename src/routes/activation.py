# cython: language_level=3
import os
from flask import render_template, request, Blueprint, flash, redirect, url_for, send_file
from flask_login import login_required

from src.config import app
from src.activator import (
    generate_unique_id, 
    LicenseManager
)
from src.helper import load_secret_key
from src.routes.helper.activation_helper import generate_license_pdf
from src.activator import get_plan_details

from src.routes.helper.notification.manager import generate_system_notification
from src.schemas.discussion_board import UserNotification   


activation_bp = Blueprint('activation', __name__)
internal_license_key_path = os.path.join(os.path.expanduser('~'), '.database', 'internal_license_key.txt')

@app.route('/system/activation', methods=['GET', 'POST'])
@login_required
def activation():
    """ 
    Activation page route to activate the product with the activation code and show the product details.

    Returns:
        render_template: Activation page template
    """
    plan_details = get_plan_details()
    app.jinja_env.globals.update(
        is_plan_not_expired=plan_details.get('is_plan_not_expired'),
        remaining_plan_days=plan_details.get('remaining_plan_days'),
        plan_type=plan_details.get('plan_type'),
        is_trial=plan_details.get('is_trial'),
        license_key=plan_details.get('license_key'),
        activation_code=plan_details.get('activation_code'),
        systemguard_unique_id=plan_details.get('systemguard_unique_id'),
        max_scrap_target=plan_details.get('max_scrap_target'),
        max_alert_rules=plan_details.get('max_alert_rules'),
        max_number_of_graphs=plan_details.get('max_number_of_graphs'),
        monthly_alert_tickets_limit=plan_details.get('monthly_alert_tickets_limit'),
        max_users_allowed=plan_details.get('max_users_allowed')
    )

    systemguard_unique_id = generate_unique_id()

    license_key = None
    activation_code = ""

    if request.method == 'POST':
        activation_code = request.form.get('activation_code') or ""
        is_valid = LicenseManager().verify_activation_code(activation_code, systemguard_unique_id)
        new_license_key = LicenseManager().get_license_key(activation_code)

        if is_valid:
            try:
                with open(internal_license_key_path, 'w') as f:
                    f.write(f"Don't modify this file. It contains the SystemGuard license information.\nlicense_key:{new_license_key}\nactivation_code:{activation_code}\nsystemguard_unique_id:{systemguard_unique_id}")
                flash('Activation successful', 'success')
                
                # send system notification
                # notification_data = {
                #     "type": "info",
                #     "icon": "info-circle",  # Font Awesome icon
                #     "title": "Product Activation",
                #     "message": "Product activation successful.",
                #     "is_global": True
                # }
                notification_data = UserNotification(
                    type="info",
                    icon="info-circle",
                    title="Product Activation",
                    message="Product activation successful.",
                    is_global=True
                )


                generate_system_notification(notification_data)
                    
                return redirect(url_for('activation'))
            except IOError as e:
                flash(f"Error writing to the license file: {str(e)}", 'danger')
        else:
            flash('Invalid activation code. Please try again.', 'danger')

    # Render the activation page, passing required data
    return render_template('activation/activation.html',
                           systemguard_unique_id=systemguard_unique_id,
                           activation_code=activation_code,
                           license_key=license_key)

@app.route('/system/download-license', methods=['GET'])
@login_required
def download_license():
    try:
        systemguard_unique_id = generate_unique_id()
        pdf_file_path = generate_license_pdf(internal_license_key_path)
        return send_file(pdf_file_path, as_attachment=True, download_name=f"license_{systemguard_unique_id}.pdf")
    except Exception as e:
        flash('Error downloading the license file: {}'.format(str(e)), 'danger')
        return redirect(url_for('activation'))
