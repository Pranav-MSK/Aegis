# cython: language_level=3
from prometheus_client import Gauge, Counter, Summary, Histogram

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
    'ACTIVE_REQUESTS': Gauge('dev_api_active_requests', 'Number of active requests'),
    'request_count': Counter('http_requests_total', 'Total HTTP requests made'),
    'error_codes': Summary('http_errors_total', 'Total HTTP errors', ['error_code']),
    'REQUEST_METHOD_COUNT': Summary('request_method_count', 'Request method count', ['method']),
    'RESPONSE_SIZE': Summary('response_size_bytes', 'Response size in bytes', ['route']),
    'REQUEST_HISTOGRAM': Histogram('request_duration_seconds', 'Duration of requests in seconds', ['route']),
    'API_REQUESTS': Summary('api_requests_total', 'Total API requests made', ['route']),
    'DB_REQUESTS': Summary('db_requests_total', 'Total database requests made', ['route']),
    'DB_QUERY_TIME': Summary('db_query_time_seconds', 'Database query time in seconds', ['query_type']),
    'SLOW_DB_QUERY': Summary('slow_db_query_time_seconds', 'Slow database query time in seconds', ['query_type']),
    'DB_REQUESTS_COUNTER': Counter('db_requests_counter', 'Total database requests made'),
    'ERROR_QUERY_COUNTER': Counter('error_query_counter', 'Total error queries made'),
}
