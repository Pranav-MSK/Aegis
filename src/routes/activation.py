# cython: language_level=3
import os
from flask import render_template, request, Blueprint, jsonify, session, flash, redirect, url_for, send_file
from flask_login import login_required

from src.utils import ROOT_DIR
from src.config import app, limiter
from src.activator import (
    calculate_unique_system_id, 
    verify_activation_code, 
)
from src.routes.helper.activation_helper import generate_license_pdf

activation_bp = Blueprint('activation', __name__)
internal_license_key_path = os.path.join(os.path.expanduser('~'), '.database', 'internal_license_key.txt')

@app.route('/activation', methods=['GET', 'POST'])
@login_required
def activation():
    systemguard_unique_id = calculate_unique_system_id()

    license_key = None
    activation_code = ""

    if request.method == 'POST':
        activation_code = request.form.get('activation_code')
        is_valid, new_license_key = verify_activation_code(activation_code, systemguard_unique_id, obfuscated_key)

        if is_valid:
            try:
                with open(internal_license_key_path, 'w') as f:
                    f.write(f"Don't modify this file. It contains the SystemGuard license information.\nlicense_key:{new_license_key}\nactivation_code:{activation_code}\nsystemguard_unique_id:{systemguard_unique_id}")
                flash('Activation successful', 'success')
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

@app.route('/download-license', methods=['GET'])
@login_required
@limiter.limit("1 per minute", error_message="Only 1 download per minute is allowed.")
def download_license():
    try:
        systemguard_unique_id = calculate_unique_system_id()
        pdf_file_path = generate_license_pdf(internal_license_key_path)
        return send_file(pdf_file_path, as_attachment=True, download_name=f"license_{systemguard_unique_id}.pdf")
    except Exception as e:
        flash('Error downloading the license file: {}'.format(str(e)), 'danger')
        return redirect(url_for('activation'))
