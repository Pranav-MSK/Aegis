# cython: language_level=3
from prometheus_client import Gauge, Counter, Summary

metrics = {
    'cpu_usage_metric': Gauge('cpu_usage_percentage', 'Current CPU usage percentage'),
    'memory_usage_metric': Gauge('memory_usage_percentage', 'Current memory usage percentage'),
    'disk_usage_metric': Gauge('disk_usage_percentage', 'Disk usage percentage'),
    'network_sent_metric': Gauge('network_bytes_sent', 'Total network bytes sent'),
    'network_recv_metric': Gauge('network_bytes_received', 'Total network bytes received'),
    'cpu_temp_metric': Gauge('cpu_temperature', 'Current CPU temperature'),
    'cpu_frequency_metric': Gauge('cpu_frequency', 'Current CPU frequency'),
    'battery_percentage_metric': Gauge('battery_percentage', 'Current battery percentage'),
    'dashboard_memory_usage_metric': Gauge('dashboard_memory_usage_percentage', 'Current memory usage percentage'),
    'request_count': Counter('http_requests_total', 'Total HTTP requests made'),
    'error_count': Counter('http_errors_total', 'Total HTTP errors', ['error_type'])
}
