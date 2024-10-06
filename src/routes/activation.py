import os
from flask import render_template, request, Blueprint, jsonify, session, flash, redirect, url_for

from src.config import app, secret_key
from src.activator import (
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
    license_key = ""
    activation_code = ""

    if request.method == 'POST':
        activation_code = request.form.get('activation_code')

        # Verify activation code and update license key
        is_valid, new_license_key = verify_activation_code(activation_code, systemguard_unique_id, secret_key)
        
        if is_valid:
            with open('internal_license_key.txt', 'w') as f:
                f.write("license_key:{}\nactivation_code:{}\nsystemguard_unique_id:{}".format(new_license_key, activation_code, systemguard_unique_id))
            flash('Activation successful', 'success')
            return redirect(url_for('activation'))
        else:
            flash('Invalid activation code. Please try again.', 'danger')

    return render_template('activation/activation.html', 
                           systemguard_unique_id=systemguard_unique_id,
                           message=message,
                           activation_code=activation_code,
                           license_key=license_key)


@app.route('/download-license', methods=['GET'])
def download_license():
    try:
        with open('internal_license_key.txt', 'r') as f:
            license_data = f.read()
            license_key = license_data.split('\n')[0].split(':')[1]
            activation_code = license_data.split('\n')[1].split(':')[1]
            systemguard_unique_id = license_data.split('\n')[2].split(':')[1]
            return jsonify({"license_key": license_key, "activation_code": activation_code, "systemguard_unique_id": systemguard_unique_id})
    except Exception as e:
        return jsonify({"error": str(e)})
