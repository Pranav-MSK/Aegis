# cython: language_level=3
from flask import render_template, request, blueprints
import psutil

from src.config import app
from src.routes.helper.network_helper import handle_network_scan, handle_port_scan

experimental_bp = blueprints.Blueprint('experimental', __name__)

@app.route('/security_analysis', methods=['GET', 'POST'])
def security_analysis():
    if request.method == 'POST':
        if 'scan_network' in request.form:
            return handle_network_scan()
        elif 'scan_ports' in request.form:
            return handle_port_scan()
    
    # Render the default scan page if the request method is GET or no valid action is found in POST.
    return render_template('experimental/scan.html')

KNOWN_SERVICES = [
    'apache', 'nginx', 'mysql', 'postgresql', 'mongodb', 'redis',
    'memcached', 'elasticsearch', 'rabbitmq', 'docker', 'sshd',
    'ftpd', 'smbd', 'ntpd', 'named', 'httpd', 'tomcat', 'jenkins',
    'gitlab', 'zookeeper', 'kafka', 'cassandra', 'prometheus',
    'grafana', 'influxd', 'telegraf', 'logstash', 'kibana', 'haproxy',
    'varnishd', 'squid', 'postfix', 'dovecot', 'cups', 'ntp', 'cron',
    'systemd', 'udev', 'dbus', 'rsyslogd', 'supervisord'
]

@app.route('/services')
def discover_services():
    services = []
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'status'])
            if any(known_service in pinfo['name'].lower() for known_service in KNOWN_SERVICES):
                services.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return render_template('other/services.html', services=services)