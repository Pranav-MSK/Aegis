# cython: language_level=3
from datetime import datetime
import requests
from flask import render_template, request, blueprints, jsonify
from http.client import HTTPException
from pprint import pprint

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

PROMETHEUS_URL = 'http://localhost:9090'

def query_prometheus(query):
    """Helper function to query Prometheus"""
    response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params={'query': query})
    response.raise_for_status()
    return response.json()

@app.route('/api/metrics')
def api_metrics_analysis():
    return render_template('other/metrics.html')

def get_histogram_metrics():
    """Fetch all histogram metrics and their endpoints from Prometheus."""
    query = 'count by (route, __name__) ({__name__=~".*_bucket"})'
    print(f"query : {query}")
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

@app.route('/api/metrics/endpoints')
def get_endpoints():
    """Get list of endpoints that have histogram metrics."""
    try:
        metrics = get_histogram_metrics()
        return jsonify(metrics)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Prometheus connection error: {str(e)}"}), 500


@app.route('/api/metrics/data/<path:endpoint>/<metric_name>')
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

        print(f"bucket_result : {bucket_query}")
        
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


#--------------------------------------------------------------------------------

import psutil
from datetime import datetime
from typing import Dict, List, Any


class ServiceMonitor:
    def __init__(self):
        self.service_patterns = {
            'Python': ['python', 'python3', 'gunicorn', 'uvicorn', 'django'],
            'Java': ['java', 'javaw', 'tomcat'],
            'Node.js': ['node', 'npm', 'yarn'],
            'Go': ['go'],
            'Databases': ['mysql', 'mysqld', 'postgres', 'mongodb', 'redis', 'elasticsearch'],
            'Web Servers': ['nginx', 'apache2', 'httpd'],
            'Docker': ['docker', 'containerd'],
            'Kubernetes': ['kubelet', 'kube-proxy', 'kube-apiserver']
        }

    def get_process_info(self, proc: psutil.Process) -> Dict[str, Any]:
        """Get relevant information about a process."""
        try:
            with proc.oneshot():
                created_time = datetime.fromtimestamp(proc.create_time())
                uptime = datetime.now() - created_time
                
                return {
                    'pid': proc.pid,
                    'name': proc.name(),
                    'cmd': ' '.join(proc.cmdline())[:100] if proc.cmdline() else '',
                    'status': proc.status(),
                    'cpu': round(proc.cpu_percent(), 2),
                    'memory_mb': round(proc.memory_info().rss / (1024 * 1024), 2),
                    'ports': self.get_process_ports(proc),
                    'created_time': created_time.isoformat(),
                    'uptime_seconds': int(uptime.total_seconds()),
                    'uptime_human': self.format_uptime(uptime)
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return {}

    def get_process_ports(self, proc: psutil.Process) -> List[int]:
        """Get ports used by the process."""
        try:
            connections = proc.net_connections(kind='inet')
            return sorted(list(set(
                conn.laddr.port for conn in connections 
                if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port
            )))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

    def get_running_services(self) -> Dict[str, Any]:
        """Get information about running services grouped by type."""
        timestamp = datetime.now().isoformat()
        services = {category: [] for category in self.service_patterns.keys()}
        summary = {category: {'count': 0, 'total_memory_mb': 0} 
                  for category in self.service_patterns.keys()}
        
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    proc_name = proc.name().lower()
                    cmdline = ' '.join(proc.cmdline()).lower() if proc.cmdline() else ''
                    
                    for category, patterns in self.service_patterns.items():
                        if any(pattern.lower() in proc_name or pattern.lower() in cmdline 
                              for pattern in patterns):
                            proc_info = self.get_process_info(proc)
                            if proc_info:
                                services[category].append(proc_info)
                                summary[category]['count'] += 1
                                summary[category]['total_memory_mb'] += proc_info['memory_mb']
                            break
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        # Round summary memory values
        for category in summary:
            summary[category]['total_memory_mb'] = round(
                summary[category]['total_memory_mb'], 2
            )
            
        return {
            'timestamp': timestamp,
            'services': services,
            'summary': summary
        }

    def format_uptime(self, uptime) -> str:
        """Format uptime duration to readable string."""
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"

monitor = ServiceMonitor()

@app.get("/api/services")
def get_services():
    """Get all running services."""
    try:
        return jsonify(monitor.get_running_services())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/services/{category}")
def get_services_by_category(category: str):
    """Get services for a specific category."""
    try:
        data = monitor.get_running_services()
        if category not in data['services']:
            raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
        
        return jsonify({
            'timestamp': data['timestamp'],
            'category': category,
            'processes': data['services'][category],
            'summary': data['summary'][category]
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
def get_categories():
    """Get list of available service categories."""
    return jsonify({
        'categories': list(monitor.service_patterns.keys())
    })
