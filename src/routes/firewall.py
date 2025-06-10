# cython: language_level=3
from flask import Blueprint, render_template, request, session, flash
from flask_login import login_required

from src.config import app
from src.routes.helper.firewall_helper import PortManager
from src.routes.helper.common_helper import admin_required, handle_sudo_password
from src.logger import get_logger
logger = get_logger(__name__)
from src.routes.helper.network_helper import handle_network_scan, handle_port_scan
from src.routes.helper.access_decorators import systemguard_enterprise

firewall_bp = Blueprint('firewall', __name__)

@app.route('/system/firewall', methods=['GET', 'POST'])
@admin_required
@systemguard_enterprise()
@handle_sudo_password("firewall")
def firewall():
    """
    Flask view for the firewall page. Handles both GET and POST requests:
    - GET: Displays the open ports and checks if sudo password is saved in session.
    - POST: Handles sudo password verification, enabling/disabling ports, and
      session management.
    """
    message = ''
    open_ports = []
    sudo_password = session.get('sudo_password', '')
    port_manager = PortManager()

    try:
        if request.method == 'POST':
            # Validate form data
            if all(field in request.form for field in ['port', 'protocol', 'action']):
                port = request.form['port']
                protocol = request.form['protocol']
                action = request.form['action']

                if not validate_port(port):
                    message = f"Invalid port number: {port}."
                    flash(message, 'danger')
                    logger.error(message)
                    open_ports, _ = port_manager.list_open_ports(sudo_password)
                else:
                    logger.info(f"Port: {port}, Protocol: {protocol}, Action: {action}")

                    # Handle port enabling/disabling based on the action
                    if action == 'enable':
                        message = port_manager.enable_port(port, protocol, sudo_password)
                    elif action == 'disable':
                        message = port_manager.disable_port(port, protocol, sudo_password)
                    else:
                        message = "Invalid action specified."
                        flash(message, 'danger')
                        logger.error(message)

                    # Log the message and list the current open ports
                    flash(message, 'info')
                    logger.info(message)

                    open_ports, error_message = port_manager.list_open_ports(sudo_password)
                    if error_message:
                        message = error_message
                        flash(message, 'danger')
                        logger.error(message)
            else:
                message = "Missing required fields: port, protocol, action."
                flash(message, 'danger')
                logger.error(message)
                open_ports, error_message = port_manager.list_open_ports(sudo_password)
                if error_message:
                    message = error_message
                    flash(message, 'danger')

        else:
            # Handle GET request
            if sudo_password:
                open_ports, error_message = port_manager.list_open_ports(sudo_password)
                if error_message:
                    message = error_message
                    flash(message, 'danger')
                    logger.error(message)
            else:
                message = "Please enter your sudo password to view the open ports."
                flash(message, 'info')

    except Exception as e:
        message = f"An error occurred: {str(e)}"
        flash(message, 'danger')
        logger.error(message)

    return render_template('firewall/firewall.html', message=message, open_ports=open_ports)

def validate_port(port):
    """Validate if the provided port is a valid number and within the correct range."""
    try:
        port_number = int(port)
        return 1 <= port_number <= 65535
    except ValueError:
        return False


@app.route('/system/security', methods=['GET', 'POST'])
@login_required
def perform_security_analysis():
    if request.method == 'POST':
        if 'scan_network' in request.form:
            return handle_network_scan()
        elif 'scan_ports' in request.form:
            return handle_port_scan()
    
    # Render the default scan page if the request method is GET or no valid action is found in POST.
    return render_template('security/scan.html')
