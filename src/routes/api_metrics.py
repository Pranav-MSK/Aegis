# cython: language_level=3
from datetime import datetime
import requests
import requests
from flask import render_template, blueprints, jsonify, request
from flask_login import login_required

from src.config import app
from src.routes.helper.service_helper import get_running_docker_containers
from src.routes.helper.access_decorators import systemguard_enterprise, community_edition

metrics_bp = blueprints.Blueprint('metrics', __name__)

PROMETHEUS_URL = 'http://localhost:9090'

def query_prometheus(query):
    """Execute a query against Prometheus."""
    try:
        response = requests.get(
            f'{PROMETHEUS_URL}/api/v1/query',
            params={'query': query},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Prometheus query failed: {str(e)}")
        return {"status": "error", "data": {"result": []}}

def get_histogram_metrics():
    """Fetch all histogram metrics and their endpoints from Prometheus."""
    query = 'count by (route, __name__) ({__name__=~".*_bucket"})'
    result = query_prometheus(query)

    metrics = {}
    if result['status'] == 'success':
        for metric in result['data']['result']:
            if 'route' not in metric['metric']:
                route = 'root'
            else:
                route = metric['metric']['route']
            metric_name = metric['metric']['__name__']
            
            if route not in metrics:
                metrics[route] = []
            if metric_name not in metrics[route]:
                metrics[route].append(metric_name)

    return metrics

@app.route('/api/v1/histogram/endpoints')
@login_required
def get_endpoints_histogram():
    """Get list of endpoints that have histogram metrics."""
    try:
        metrics = get_histogram_metrics()
        return jsonify(metrics)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Prometheus connection error: {str(e)}"}), 500

@app.route('/api/v1/histogram/data/<path:endpoint>/<metric_name>')
@login_required
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

        # Sort buckets by le value
        buckets.sort(key=lambda x: float(x['le']) if x['le'] != '+Inf' else float('inf'))

        # Calculate statistics
        total_sum = float(sum_result['data']['result'][0]['value'][1]) if sum_result['data']['result'] else 0.0
        total_count = float(count_result['data']['result'][0]['value'][1]) if count_result['data']['result'] else 0.0
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

# only for sum and count, don't include the metrics from the bucket
def get_available_summary_metrics():
    """Get list of available metrics from Prometheus."""
    try:
        # Query to get all metric names
        result = query_prometheus('{__name__=~".+"}')
        if result['status'] != 'success':
            print("Failed to fetch metrics:", result)
            return []
            
        # Extract unique metric names and filter for histogram metrics
        metrics = set()
        for item in result['data']['result']:
            metric_name = item['metric']['__name__']
            if metric_name.endswith('_sum') or metric_name.endswith('_count'):
                # Remove the _sum or _count suffix to get base metric name
                base_name = metric_name.rsplit('_', 1)[0]
                metrics.add(base_name)
        
        return sorted(list(metrics))
    except Exception as e:
        print("Error fetching metrics:", str(e))
        return []

# only for sum and count, don't include the metrics from the bucket
@app.route('/api/v1/summary/endpoints')
@login_required
def get_metrics_list():
    """Get list of available metrics and their endpoints."""
    try:
        metrics = {}
        base_metrics = get_available_summary_metrics()
        
        for base_metric in base_metrics:
            # Query to get all routes for this metric using the _sum suffix
            # We use _sum since it will have the same routes as _count
            query = f'{base_metric}_sum'
            result = query_prometheus(query)
            
            if result['status'] == 'success':
                endpoints = set()
                for item in result['data']['result']:
                    # Get route label, default to '' if not present
                    route = item['metric'].get('route', '')
                    endpoints.add(route)
                
                # Only include metrics that have route information
                if endpoints:
                    metrics[base_metric] = sorted(list(endpoints))
        
        # Debug logging
        
        return jsonify({
            "status": "success",
            "data": metrics
        })
    except Exception as e:
        print("Error in get_metrics_list:", str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/v1/summary/data')
@login_required
def get_metrics_summary():
    """Get summary metrics for specific metric and optional endpoint."""
    try:
        metric_name = request.args.get('metric')
        endpoint = request.args.get('endpoint')
        
        if not metric_name:
            return jsonify({"error": "Metric name is required"}), 400
            
        # Build route filter if endpoint is specified
        route_filter = f',route="{endpoint}"' if endpoint else ''
        
        queries = {
            'sum': f'{metric_name}_sum{{{route_filter}}}',
            'count': f'{metric_name}_count{{{route_filter}}}',
        }
        
        results = {}
        for query_name, query in queries.items():
            result = query_prometheus(query)
            if result['status'] == 'success' and result['data']['result']:
                results[query_name] = [
                    {
                        'endpoint': r['metric'].get('route', ''),
                        'query_type': r['metric'].get('query_type', ''),
                        'method': r['metric'].get('method', ''),
                        'status': r['metric'].get('status', ''),
                        'status_code': r['metric'].get('status_code', ''),
                        'reason': r['metric'].get('reason', ''),
                        'error': r['metric'].get('error', ''),
                        'error_code': r['metric'].get('error_code', ''),
                        'error_type': r['metric'].get('error_type', ''),
                        'payment_method': r['metric'].get('payment_method', ''),
                        'user_id': r['metric'].get('user_id', ''),

                        'timestamp': r['value'][0],
                        'value': float(r['value'][1]),
                        
                        'instance': r['metric'].get('instance', ''),
                        'job': r['metric'].get('job', ''),
                        
                    }
                    # also need to update in the summary_metrics.html
                    for r in result['data']['result']
                ]
            else:
                results[query_name] = []
                
        # Calculate averages
        results['averages'] = []
        for sum_data in results['sum']:
            matching_count = next(
                (c for c in results['count'] if c['endpoint'] == sum_data['endpoint']),
                None
            )
            if matching_count and matching_count['value'] > 0:
                results['averages'].append({
                    'endpoint': sum_data['endpoint'],
                    'query_type': sum_data['query_type'],
                    'method': sum_data['method'],
                    'status': sum_data['status'],
                    'status_code': sum_data['status_code'],
                    'reason': sum_data['reason'],
                    'error': sum_data['error'],
                    'error_code': sum_data['error_code'],
                    'error_type': sum_data['error_type'],
                    'payment_method': sum_data['payment_method'],
                    'user_id': sum_data['user_id'],

                    'timestamp': sum_data['timestamp'],
                    'value': sum_data['value'] / matching_count['value'],
                    
                    'instance': sum_data['instance'],
                    'job': sum_data['job'],
                    
                })
        
        return jsonify({
            "status": "success",
            "data": results,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    


@app.route('/system/bucket_metrics')
@login_required
@community_edition()
def get_bucket_metrics():
    return render_template('other/bucket_metrics.html')


@app.route('/system/summary_metrics')
@login_required
@community_edition()
def get_summary_metrics():
    return render_template('other/summary_metrics.html')


@app.route('/api/v1/system/containers')
@login_required
def fetch_running_docker_containers():
    """Get all system metrics including running daemons and Docker containers"""
    containers = get_running_docker_containers()
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'containers': containers
    })
