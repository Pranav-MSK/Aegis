import os
from datetime import datetime
from fpdf import FPDF
from flask import render_template, request, Blueprint, jsonify, session, flash, redirect, url_for, send_file

from src.utils import ROOT_DIR
from src.config import app, secret_key
from src.activator import (
    calculate_unique_system_id, 
    verify_activation_code, 
)

activation_bp = Blueprint('activation', __name__)

@app.route('/activation', methods=['GET', 'POST'])
def activation():
    sudo_password = session.get('sudo_password', '')
    if sudo_password:
        systemguard_unique_id = calculate_unique_system_id(sudo_password)
    else:
        systemguard_unique_id = "Superadmin mode is required to view the unique system ID."

    license_key = None
    activation_code = ""

    if request.method == 'POST':
        activation_code = request.form.get('activation_code')
        is_valid, new_license_key = verify_activation_code(activation_code, systemguard_unique_id, secret_key)

        if is_valid:
            try:
                with open('internal_license_key.txt', 'w') as f:
                    f.write(f"license_key:{new_license_key}\nactivation_code:{activation_code}\nsystemguard_unique_id:{systemguard_unique_id}")
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

def generate_license_pdf(license_file_path):
    with open(license_file_path, 'r') as f:
        license_data = f.read()
        license_key = license_data.split('\n')[0].split(':')[1]
        activation_code = license_data.split('\n')[1].split(':')[1]
        systemguard_unique_id = license_data.split('\n')[2].split(':')[1]
    
    # Create an instance of FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Add a page
    pdf.add_page()

    # Set title font (bold and size 16)
    pdf.set_font('Arial', 'B', 18)
    pdf.cell(0, 10, 'SystemGuard License Information', ln=True, align='C')

    # Add today's date in the header
    pdf.set_font('Arial', 'I', 10)
    today_date = datetime.now().strftime('%Y-%m-%d')
    pdf.cell(0, 10, f'Date: {today_date}', ln=True, align='C')

    
    # Line break
    pdf.ln(10)

    # Set section title font
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'SystemGuard Unique ID:', ln=True)

    # Set regular font (size 12)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, systemguard_unique_id, ln=True)

    pdf.ln(10)  # Add a line break
    
    # Add border for License Key section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'License Key:', ln=True)
    
    # Use multi_cell for long License Key, with borders
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, license_key, border=1, align='L')  # Border added

    pdf.ln(5)  # Add a small gap
    
    # Add border for Activation Code section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Activation Code:', ln=True)
    
    # Use multi_cell for long Activation Code, with borders
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, activation_code, border=1, align='L')  # Border added

    # Add a final line break
    pdf.ln(10)

    # Save the PDF to a file
    pdf_file_path = os.path.join(ROOT_DIR, 'SystemGuard_License.pdf')
    pdf.output(pdf_file_path)

    return pdf_file_path



@app.route('/download-license', methods=['GET'])
def download_license():
    try:
        sudo_password = session.get('sudo_password', '')
        license_file_path = os.path.join(ROOT_DIR, 'internal_license_key.txt')
        systemguard_unique_id = calculate_unique_system_id(sudo_password)
        pdf_file_path = generate_license_pdf(license_file_path)
        return send_file(pdf_file_path, as_attachment=True, download_name=f"license_{systemguard_unique_id}.pdf")
    except Exception as e:
        flash('Error downloading the license file: {}'.format(str(e)), 'danger')
        return redirect(url_for('activation'))
