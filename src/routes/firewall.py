# cython: language_level=3
from flask import Blueprint, render_template, request, session, flash
from flask_login import login_required

from src.config.app_config import app
from src.services.access_decorators import systemguard_enterprise
from src.routes.helper.common_helper import handle_sudo_password, admin_required
from src.helper.logger import get_logger
from src.services.firewall.firewall_service import FirewallService
from src.services.firewall.security_scan_service import SecurityScanService

logger = get_logger(__name__)
firewall_bp = Blueprint('firewall', __name__)
firewall_service = FirewallService()
scan_service = SecurityScanService()

@app.route('/system/firewall', methods=['GET', 'POST'])
@admin_required
@systemguard_enterprise()
@handle_sudo_password("firewall")
def firewall():
    message, open_ports = firewall_service.handle_firewall_request(request, session)
    return render_template('firewall/firewall.html', message=message, open_ports=open_ports)

@app.route('/system/security', methods=['GET', 'POST'])
@login_required
def perform_security_analysis():
    if request.method == 'POST':
        if 'scan_network' in request.form:
            return scan_service.handle_network_scan()
        elif 'scan_ports' in request.form:
            return scan_service.handle_port_scan()
    return render_template('security/scan.html')
