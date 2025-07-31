# cython: language_level=3
from flask import request, session, flash
from src.services.firewall.firewall_helper import PortManager
from src.helper.logger import get_logger

logger = get_logger(__name__)

class FirewallService:
    def __init__(self):
        self.port_manager = PortManager()

    def handle_firewall_request(self, request, session):
        message = ''
        open_ports = []
        sudo_password = session.get('sudo_password', '')

        try:
            if request.method == 'POST':
                if all(field in request.form for field in ['port', 'protocol', 'action']):
                    port = request.form['port']
                    protocol = request.form['protocol']
                    action = request.form['action']

                    if not self.validate_port(port):
                        message = f"Invalid port number: {port}."
                        flash(message, 'danger')
                        logger.error(message)
                    else:
                        logger.info(f"Port: {port}, Protocol: {protocol}, Action: {action}")
                        if action == 'enable':
                            message = self.port_manager.enable_port(port, protocol, sudo_password)
                        elif action == 'disable':
                            message = self.port_manager.disable_port(port, protocol, sudo_password)
                        else:
                            message = "Invalid action specified."
                            flash(message, 'danger')
                            logger.error(message)

                        flash(message, 'info')
                        logger.info(message)
                else:
                    message = "Missing required fields: port, protocol, action."
                    flash(message, 'danger')
                    logger.error(message)

            if sudo_password:
                open_ports, error_message = self.port_manager.list_open_ports(sudo_password)
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

        return message, open_ports

    @staticmethod
    def validate_port(port):
        try:
            port_number = int(port)
            return 1 <= port_number <= 65535
        except ValueError:
            return False
