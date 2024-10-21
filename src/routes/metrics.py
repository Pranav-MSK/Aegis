# cython: language_level=3
from datetime import datetime
import requests
from flask import render_template, blueprints, jsonify
from datetime import datetime

from src.config import app
from src.routes.helper.system_helper import get_running_docker_containers

metrics_bp = blueprints.Blueprint('metrics', __name__)

PROMETHEUS_URL = 'http://localhost:9090'

def query_prometheus(query):
    """Helper function to query Prometheus"""
    response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params={'query': query})
    response.raise_for_status()
    return response.json()

def get_histogram_metrics():
    """Fetch all histogram metrics and their endpoints from Prometheus."""
    query = 'count by (route, __name__) ({__name__=~".*_bucket"})'
    result = query_prometheus(query)

    metrics = {}
    if result['status'] == 'success':
        for metric in result['data']['result']:
            route = metric['metric']['route']
            metric_name = metric['metric']['__name__']
            if route not in metrics:
                metrics[route] = []
            if metric_name not in metrics[route]:
                metrics[route].append(metric_name)

    return metrics

@app.route('/api/v1/system/containers')
def fetch_running_docker_containers():
    """Get all system metrics including running daemons and Docker containers"""
    containers = get_running_docker_containers()
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'containers': containers
    })

@app.route('/system/metrics')
def api_metrics_analysis():
    return render_template('other/metrics.html')

@app.route('/api/v1/metrics/endpoints')
def get_endpoints():
    """Get list of endpoints that have histogram metrics."""
    try:
        metrics = get_histogram_metrics()
        return jsonify(metrics)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Prometheus connection error: {str(e)}"}), 500


@app.route('/api/v1/metrics/data/<path:endpoint>/<metric_name>')
def get_metrics(endpoint, metric_name):
    """Get histogram data for specific endpoint and metric."""
    try:
        if endpoint == "root":
            endpoint = "/"
        else:
            endpoint = "/" + endpoint

        metric_name = metric_name.replace("_bucket", "")

        bucket_query = f'{metric_name}_bucket{{route="{endpoint}"}}'
        sum_query = f'{metric_name}_sum{{route="{endpoint}"}}'
        count_query = f'{metric_name}_count{{route="{endpoint}"}}'
        
        bucket_result = query_prometheus(bucket_query)
        
        sum_result = query_prometheus(sum_query)
        count_result = query_prometheus(count_query)

        if bucket_result['status'] != 'success':
            return jsonify({"error": "Failed to fetch bucket data"}), 500
        
        # Extract and process bucket data
        bucket_data = bucket_result['data']['result']
        buckets = []
        for item in bucket_data:
            le = item['metric'].get('le', '+Inf')
            value = float(item['value'][1]) if item['value'][1] else 0.0
            buckets.append({"le": le, "value": value})

        # Sort buckets by le value, handling "+Inf" specially
        buckets.sort(key=lambda x: float(x['le']) if x['le'] != '+Inf' else float('inf'))

        # Get sum and count
        total_sum = float(sum_result['data']['result'][0]['value'][1]) if sum_result['data']['result'] else 0.0
        total_count = float(count_result['data']['result'][0]['value'][1]) if count_result['data']['result'] else 0.0
        
        # Calculate average
        average = total_sum / total_count if total_count > 0 else 0.0

        return jsonify({
            "buckets": buckets,
            "count": total_count,
            "sum": total_sum,
            "average": average,
            "endpoint": endpoint,
            "metric": metric_name
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Prometheus connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing data: {str(e)}"}), 500
