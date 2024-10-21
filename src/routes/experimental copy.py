# cython: language_level=3
from flask import render_template, request, blueprints, jsonify, send_from_directory
from datetime import datetime

from src.config import app
from src.routes.helper.network_helper import handle_network_scan, handle_port_scan
from src.routes.helper.system_performance_helper import get_running_daemons, get_running_docker_containers

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


@app.route('/api/v1/metrics/system/performance')
def get_system_performance_metrics():
    """Get all system metrics including running daemons and Docker containers"""
    daemons = get_running_daemons()
    containers = get_running_docker_containers()
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'daemons': daemons,
        'containers': containers
    })

# @app.route('/api/v1/metrics/system/daemons')
# def get_daemon_metrics():
#     """Get list of running Python daemons"""
#     daemons = get_running_daemons()
    
#     return jsonify({
#         'timestamp': datetime.now().isoformat(),
#         'daemons': daemons
#     })

# @app.route('/api/v1/metrics/system/containers')
# def get_container_metrics():
#     """Get metrics for all running Docker containers"""
#     containers = get_running_docker_containers()
    
#     return jsonify({
#         'timestamp': datetime.now().isoformat(),
#         'containers': containers
#     })

# Sample data - in production this would likely come from a database or file
METRICS_DATA = {
    "/api/dashboard/stats": {
        "buckets": [
            {"le": "0.005", "value": 0.0},
            {"le": "0.01", "value": 0.0},
            {"le": "0.025", "value": 0.0},
            {"le": "0.05", "value": 0.0},
            {"le": "0.075", "value": 0.0},
            {"le": "0.1", "value": 0.0},
            {"le": "0.25", "value": 999.0},
            {"le": "0.5", "value": 1024.0},
            {"le": "0.75", "value": 1025.0},
            {"le": "1.0", "value": 1025.0},
            {"le": "2.5", "value": 1025.0},
            {"le": "5.0", "value": 1025.0},
            {"le": "7.5", "value": 1025.0},
            {"le": "10.0", "value": 1025.0},
            {"le": "+Inf", "value": 1025.0}
        ],
        "count": 1025.0,
        "sum": 170.69313788414001
    },
    "/api/v1/system-info": {
        "buckets": [
            {"le": "0.005", "value": 0.0},
            {"le": "0.01", "value": 0.0},
            {"le": "0.025", "value": 0.0},
            {"le": "0.05", "value": 0.0},
            {"le": "0.075", "value": 0.0},
            {"le": "0.1", "value": 0.0},
            {"le": "0.25", "value": 0.0},
            {"le": "0.5", "value": 0.0},
            {"le": "0.75", "value": 0.0},
            {"le": "1.0", "value": 0.0},
            {"le": "2.5", "value": 1023.0},
            {"le": "5.0", "value": 1023.0},
            {"le": "7.5", "value": 1023.0},
            {"le": "10.0", "value": 1023.0},
            {"le": "+Inf", "value": 1024.0}
        ],
        "count": 1024.0,
        "sum": 1952.390257358551
    }
}

@app.route('/data')
def root():
    return render_template('other/data.html')

@app.route('/api/metrics/endpoints')
def get_endpoints():
    """Return list of available endpoints"""
    return jsonify(list(METRICS_DATA.keys()))

@app.route('/api/metrics/data/<path:endpoint>')
def get_metrics(endpoint):
    """Return metrics data for specific endpoint"""
    endpoint = '/' + endpoint
    if endpoint not in METRICS_DATA:
        return jsonify({"error": "Endpoint not found"}), 404
        
    data = METRICS_DATA[endpoint]
    
    # Calculate average
    avg = data['sum'] / data['count'] if data['count'] > 0 else 0
    
    return jsonify({
        "buckets": data['buckets'],
        "count": data['count'],
        "sum": data['sum'],
        "average": avg
    })
