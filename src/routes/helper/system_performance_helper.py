# cython: language_level=3
import psutil
import docker
from datetime import datetime
from typing import List, Dict, Any, Union
import traceback


KNOWN_SERVICES = [
    'apache', 'nginx', 'mysql', 'postgresql', 'mongodb', 'redis',
    'memcached', 'elasticsearch', 'rabbitmq', 'docker', 'sshd',
    'ftpd', 'smbd', 'ntpd', 'named', 'httpd', 'tomcat', 'jenkins',
    'gitlab', 'zookeeper', 'kafka', 'cassandra', 'prometheus',
    'grafana', 'influxd', 'telegraf', 'logstash', 'kibana', 'haproxy',
    'varnishd', 'squid', 'postfix', 'dovecot', 'cups', 'ntp', 'cron',
    'systemd', 'udev', 'dbus', 'rsyslogd', 'supervisord'
]

# Type aliases
ContainerMetrics = Dict[str, Any]

def get_running_daemons() -> List[str]:
    """
    Get the list of running Python daemons on the system.
    
    Returns:
        List[str]: List of daemon process names
    """
    try:
        daemons = []
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                proc_info = proc.info
                if proc_info['cmdline'] and any('python' in cmd.lower() for cmd in proc_info['cmdline']):
                    # Get the actual script name being run
                    script_name = proc_info['cmdline'][-1]
                    if script_name.endswith('.py'):
                        daemons.append(script_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return daemons
    except Exception as e:
        print(f"Error collecting running daemons: {e}")
        return []

def format_bytes(bytes_value: Union[int, float, str]) -> str:
    """
    Format bytes into human readable format.
    
    Args:
        bytes_value (Union[int, float, str]): Number of bytes
        
    Returns:
        str: Formatted string with appropriate unit
    """
    try:
        # Convert string to float if necessary
        if isinstance(bytes_value, str):
            bytes_value = float(bytes_value)
        bytes_value = float(bytes_value)  # Ensure float type
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f} TB"
    except (ValueError, TypeError):
        return "0.00 B"

def safe_int_convert(value: Union[int, str, float]) -> int:
    """
    Safely convert a value to integer.
    
    Args:
        value (Union[int, str, float]): Value to convert
        
    Returns:
        int: Converted integer value
    """
    try:
        if isinstance(value, str):
            # Remove any non-numeric characters
            value = ''.join(c for c in value if c.isdigit() or c == '.')
        return int(float(value))
    except (ValueError, TypeError):
        return 0

def calculate_cpu_percent(stats: dict) -> float:
    """
    Calculate CPU percentage in a more robust way.
    
    Args:
        stats (dict): Container stats from Docker API
        
    Returns:
        float: CPU usage percentage
    """
    try:
        cpu_count = safe_int_convert(stats['cpu_stats'].get('online_cpus', 1))
        
        cpu_delta = safe_int_convert(stats['cpu_stats']['cpu_usage']['total_usage']) - \
                   safe_int_convert(stats['precpu_stats']['cpu_usage']['total_usage'])
                   
        system_delta = safe_int_convert(stats['cpu_stats']['system_cpu_usage']) - \
                      safe_int_convert(stats['precpu_stats']['system_cpu_usage'])
        
        if system_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * 100.0 * cpu_count
            return round(cpu_percent, 2)
        return 0.0
    except KeyError:
        return 0.0

def format_container_creation_time(created_str):
    """Convert the container creation timestamp to a formatted string."""
    try:
        formatted_created = datetime.strptime(created_str.split('.')[0], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        return formatted_created
    except ValueError as e:
        print(f"Error formatting container creation time: {e}")
        return "Unknown"

def get_running_docker_containers() -> List[ContainerMetrics]:
    """
    Get metrics for all running Docker containers.
    
    Returns:
        List[ContainerMetrics]: List of container metrics dictionaries
    """
    try:
        client = docker.from_env()
        containers = []
        
        for container in client.containers.list():
            try:
                stats = container.stats(stream=False)
                
                # Calculate CPU percentage using the more robust method
                cpu_percent = calculate_cpu_percent(stats)
                
                # Calculate memory usage with proper error handling
                try:
                    memory_usage = safe_int_convert(stats['memory_stats'].get('usage', 0))
                    memory_limit = safe_int_convert(stats['memory_stats'].get('limit', 1))
                    memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0
                except KeyError:
                    memory_usage = 0
                    memory_percent = 0
                
                # Get network stats if available
                network_stats = {
                    'rx_bytes': 0,
                    'tx_bytes': 0
                }
                
                if 'networks' in stats:
                    for interface in stats['networks'].values():
                        network_stats['rx_bytes'] += safe_int_convert(interface.get('rx_bytes', 0))
                        network_stats['tx_bytes'] += safe_int_convert(interface.get('tx_bytes', 0))
                
                containers.append({
                    'name': container.name,
                    'id': container.id[:12],  # Short ID
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'none',
                    'created': format_container_creation_time(container.attrs['Created']),
                    'cpu_percent': cpu_percent,
                    'memory': {
                        'usage': format_bytes(memory_usage),
                        'percent': round(memory_percent, 2)
                    },
                    'network': {
                        'received': format_bytes(network_stats['rx_bytes']),
                        'transmitted': format_bytes(network_stats['tx_bytes'])
                    }
                })
            except Exception as e:
                tb = traceback.format_exc()
                print(f"Error collecting metrics for container {container.name} at line {tb.splitlines()[-3].strip()}: {e}")
                continue
                
        return containers
    except Exception as e:
        print(f"Error connecting to Docker: {e}")
        return []
