import os
from flask import render_template, request, Blueprint, jsonify, session, flash, redirect, url_for

from src.config import app, secret_key
from src.routes.helper.activation_helper import (
    calculate_unique_system_id, 
    verify_activation_code, 
    check_license_expiration
)

activation_bp = Blueprint('activation', __name__)

@app.route('/activation', methods=['GET', 'POST'])
def activation():
    sudo_password = session.get('sudo_password', '')
    
    # Fetch the system unique ID
    systemguard_unique_id = (calculate_unique_system_id(sudo_password) if sudo_password 
                             else "Superadmin mode is required to view the unique system ID.")
    
    # Read license key from file
    license_key = None
    message = ""
    remaining_days = 0
    plan_type = ""
    is_trial = False

    try:
        with open('license_key.txt', 'r') as f:
            license_key = f.read().strip()

            # Validate the license
            is_not_expired, remaining_days, plan_type, is_trial = check_license_expiration(license_key, secret_key)
            message = f"License is valid for {remaining_days} days." if is_not_expired else "License has expired."
            
            # Store license info in session
            session.update({'plan_type': plan_type, 'is_trial': is_trial})
            
    except FileNotFoundError:
        flash("Product is not activated. Please activate the application.", "danger")

    if request.method == 'POST':
        activation_code = request.form.get('activation_code')

        # Verify activation code and update license key
        is_valid, new_license_key = verify_activation_code(activation_code, systemguard_unique_id, secret_key)
        
        if is_valid:
            # Save new license key
            with open('license_key.txt', 'w') as f:
                f.write(new_license_key)
            flash('Activation successful', 'success')
            return redirect(url_for('activation'))
        else:
            flash('Invalid activation code. Please try again.', 'danger')

    return render_template('activation/activation.html', 
                           systemguard_unique_id=systemguard_unique_id,
                           message=message,
                           remaining_days=remaining_days,
                           plan_type=plan_type,
                           is_trial=is_trial)
