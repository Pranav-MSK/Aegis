# cython: language_level=3
import os
from datetime import datetime
from fpdf import FPDF
from src.helper.basic_info import ROOT_DIR

def generate_license_pdf(license_file_path):
    with open(license_file_path, 'r') as f:
        license_data = f.read()
        license_key = license_data.split('\n')[1].split(':')[1]
        activation_code = license_data.split('\n')[2].split(':')[1]
        systemguard_unique_id = license_data.split('\n')[3].split(':')[1]
    
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

