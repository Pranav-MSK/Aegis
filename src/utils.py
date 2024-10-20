# cython: language_level=3
import os
import time
import platform
import datetime
import subprocess
import psutil
import functools
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from src.logger import logger
from src.models import GeneralSettings
from src.helper import get_system_node_name, get_ip_address, get_system_username

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Simple in-memory cache for specific data with individual timestamps
cache = {}
# enable_cahce = True # moved to the database
CACHE_EXPIRATION = 3600
DIVIDE_BY_1024 = False
CONVERSION_FACTOR_MB = (1024 ** 2) if DIVIDE_BY_1024 else (1000 ** 2)
CONVERSION_FACTOR_GB = (1024 ** 3) if DIVIDE_BY_1024 else (1000 ** 3)


def format_uptime(uptime_seconds):
    """Convert uptime from seconds to a human-readable format.
    ---
    Parameters:
        uptime_seconds (datetime.timedelta): Uptime in seconds.
    ---
    Returns:
        dict: Uptime in days, hours, minutes, and seconds.

    """
    uptime_seconds = uptime_seconds.total_seconds()
    days = int(uptime_seconds // (24 * 3600))
    uptime_seconds %= (24 * 3600)
    hours = int(uptime_seconds // 3600)
    uptime_seconds %= 3600
    minutes = int(uptime_seconds // 60)
    seconds = int(uptime_seconds % 60)
    
    return {
        'uptime_days': days,
        'uptime_hours': hours,
        'uptime_minutes': minutes,
        'uptime_seconds': seconds
    }


def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    """Format a datetime object to a string.
    ---
    Parameters:
        value (datetime.datetime): Datetime object to format.
        format (str): Format string for the output.
    ---
    Returns:
        str: Formatted datetime string.
    """
    return value.strftime(format)

def get_flask_memory_usage():
    """
    Returns the memory usage of the current Flask application in MB.
    ---
    Parameters:
        None
    ---
    Returns:
        float: Memory usage of the Flask application in MB.
    """
    try:
        pid = os.getpid()  # Get the current process ID
        process = psutil.Process(pid)  # Get the process information using psutil
        memory_info = process.memory_info()  # Get the memory usage information
        memory_in_mb = memory_info.rss / CONVERSION_FACTOR_MB
        return round(memory_in_mb)  # Return the memory usage rounded to 2 decimal places
    except Exception as e:
        logger.info(f"Error getting memory usage: {e}")
        return None
    
def get_established_connections():
    """ 
    Get the first available IPv4 and IPv6 addresses of established network connections.
    ---
    Parameters:
        None
    ---
    Returns:
        tuple: First available IPv4 and IPv6 addresses of established network connections.
    """
    # Get all active network connections of type 'inet' (IPv4 and IPv6)
    connections = psutil.net_connections(kind='inet')
    
    # Use sets to store unique IPv4 and IPv6 addresses
    ipv4_addresses = set()
    ipv6_addresses = set()

    # Iterate through each connection
    for conn in connections:
        # Filter only established connections
        if conn.status == 'ESTABLISHED':
            # Check if the local address (laddr) is IPv4 or IPv6 and add to the corresponding set
            if '.' in conn.laddr.ip:
                ipv4_addresses.add(conn.laddr.ip)
            elif ':' in conn.laddr.ip:
                ipv6_addresses.add(conn.laddr.ip)

    # Return the first available IP from each set, or "N/A" if none found
    ipv4 = next(iter(ipv4_addresses), "N/A")
    ipv6 = next(iter(ipv6_addresses), "N/A")

    return ipv4, ipv6

def run_speedtest():
    """ Run a speed test using speedtest-cli.
    ---
    Parameters:
        None
    ---
    Returns:
        dict: Download speed, upload speed, ping, and status of the speed test.
    """
    try:
        result = subprocess.run(['speedtest-cli'], capture_output=True, text=True, check=True)
        output_lines = result.stdout.splitlines()
        download_speed, upload_speed, ping = None, None, None

        for line in output_lines:
            if "Download:" in line:
                download_speed = line.split("Download: ")[1]
            elif "Upload:" in line:
                upload_speed = line.split("Upload: ")[1]
            elif "Ping:" in line:
                ping = line.split("Ping: ")[1]

        return {"download_speed": download_speed, "upload_speed": upload_speed, "ping": ping, "status": "Success"}

    except subprocess.CalledProcessError as e:
        return {"status": "Error", "message": e.stderr}

    except Exception as e:
        return {"status": "Error", "message": str(e)}

def get_cpu_frequency():
    """
    Get the current CPU frequency in MHz.
    ---
    Parameters:
        None
    ---
    Returns:
        int: Current CPU frequency in MHz.
    """
    current_freq = round(psutil.cpu_freq().current)
    max_freq = round(psutil.cpu_freq().max)
    return current_freq, max_freq

@functools.lru_cache(maxsize=1)
def get_cpu_core_count():
    """
    Get the number of CPU cores.
    ---
    Parameters:
    ---
    Returns:
        int: Number of CPU cores.
    """
    return psutil.cpu_count(logical=True)

def cpu_usage_percent():
    """
    Get the current CPU usage percentage.
    ---
    Parameters:
    ---
    Returns:
        float: Current CPU usage percentage
    """
    cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
    return round(cpu_percent, 2)

def cpu_usage_per_core():
    """
    Get the current CPU usage percentage per core.
    ---
    Parameters:
    ---
    Returns:
        list: Current CPU usage percentage per core.
    """
    cpu_percent_per_core = psutil.cpu_percent(interval=1, percpu=True)
    return [round(usage, 2) for usage in cpu_percent_per_core]


def get_cpu_temp():
    """
    Get the current CPU temperature, high temperature, and critical temperature.

    Returns:
        tuple: Current CPU temperature, high temperature, and critical temperature.
    """
    try:
        # Fetch temperatures for sensors labeled 'coretemp'
        temps = psutil.sensors_temperatures().get('coretemp')
        
        # Check if we have temperatures data
        if temps:
            temp = temps[0]  # Get the first sensor's readings
            
            # Extract current, high, and critical temperatures
            current_temp = getattr(temp, 'current', 'N/A')
            high_temp = getattr(temp, 'high', 'N/A')
            critical_temp = getattr(temp, 'critical', 'N/A')
            
            return (current_temp, high_temp, critical_temp)
        else:
            # If no 'coretemp' sensors found, return 'N/A'
            return (0, 0, 0)
    
    except Exception as e:
        logger.warning(f"Error getting CPU temperature: {e}")
        return (0, 0, 0)

def get_top_processes(number=5, combined=False):
    """Get the top processes by memory usage.
    
    ---
    Parameters:
        number (int): Number of top processes to return.
        combined (bool): Whether to combine metrics of processes with the same name.
    
    ---
    Returns:
        list: List of top processes with name, CPU percent, memory percent, and PID.
    """
    if combined:
        # Use a defaultdict to aggregate processes by name
        combined_processes = defaultdict(lambda: {'cpu_percent': 0, 'memory_percent': 0, 'pid': None})

        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent', 'pid']):
            try:
                name = p.info['name'].title()
                combined_processes[name]['cpu_percent'] = max(combined_processes[name]['cpu_percent'], p.info['cpu_percent'])
                combined_processes[name]['memory_percent'] = max(combined_processes[name]['memory_percent'], p.info['memory_percent'])
                # Store one PID (you can modify this logic if needed)
                combined_processes[name]['pid'] = p.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Convert the combined processes to a list and sort by memory percent
        processes = sorted(
            [(name, info['cpu_percent'], round(info['memory_percent'], 2), info['pid'])
             for name, info in combined_processes.items()],
            key=lambda x: x[2],  # Sort by memory percent
            reverse=True
        )[:number]
    else:
        processes = [
            (p.info['name'].title(), p.info['cpu_percent'], round(p.info['memory_percent'], 2), p.info['pid'])
            for p in sorted(
                psutil.process_iter(['name', 'cpu_percent', 'memory_percent', 'pid']),
                key=lambda p: p.info['memory_percent'],
                reverse=True
            )[:number]
        ]

    return processes

def get_disk_free():
    """Returns the free disk space in GB.
    ---
    Parameters:
    ---
    Returns:
        float: Free disk space in GB
    """
    return round(psutil.disk_usage("/").free / CONVERSION_FACTOR_GB, 1)

def get_disk_used():
    """Returns the used disk space in GB.
    ---
    Parameters:
    ---
    Returns:
        float: Used disk space in GB
    """
    return round(psutil.disk_usage("/").used / CONVERSION_FACTOR_GB, 1)

@functools.lru_cache(maxsize=1)
def get_disk_total():
    """Returns the total disk space in GB.
    ---
    Parameters:
    ---
    Returns:
        float: Total disk space in GB
    """
    return round(psutil.disk_usage("/").total / CONVERSION_FACTOR_GB, 1)

def get_disk_usage_percent():
    """Returns the percentage of disk used.
    ---
    Parameters:
    ---
    Returns:
        tuple: Disk usage percentage and calculated disk usage percentage
    """
    disk_usage = psutil.disk_usage("/")
    return disk_usage.percent


def format_speed(speed):
    """Format the speed in appropriate units."""
    if speed < 1024:
        return f"{speed:.2f} Bytes/s"
    elif speed < 1024 ** 2:
        return f"{speed / 1024:.2f} KB/s"
    else:
        return f"{speed / (1024 ** 2):.2f} MB/s"

def get_disk_io():
    """Get the disk I/O statistics.
    
    Returns:
        tuple: Disk read and write speed with units.
    """
    try:
        # Get initial disk I/O stats
        disk_io_start = psutil.disk_io_counters()
        time.sleep(1)  # Sleep for 1 second to measure the speed
        # Get final disk I/O stats
        disk_io_end = psutil.disk_io_counters()

        # Calculate read and write speeds in Bytes/s
        disk_read_speed = (disk_io_end.read_bytes - disk_io_start.read_bytes) / 1  # Already in Bytes
        disk_write_speed = (disk_io_end.write_bytes - disk_io_start.write_bytes) / 1  # Already in Bytes

        # Format the speeds
        formatted_read_speed = format_speed(disk_read_speed)
        formatted_write_speed = format_speed(disk_write_speed)

        return formatted_read_speed, formatted_write_speed
    
    except Exception as e:
        print(f"Error measuring disk I/O: {e}")
        return None, None  # Return None if there's an error


@functools.lru_cache(maxsize=1)
def get_memory_available():
    """Returns the available memory in GB.
    ---
    Parameters:
    ---
    Returns:
        float: Available memory in GB
    """
    return round(psutil.virtual_memory().total / CONVERSION_FACTOR_GB, 1)


def get_memory_used():
    """Returns the used memory in GB.
    ---
    Parameters:
    ---
    Returns:
        float: Used memory in GB
    """
    return round((psutil.virtual_memory().total - psutil.virtual_memory().available) / CONVERSION_FACTOR_GB, 2)

def get_memory_percent():
    """Returns the percentage of memory used.
    ---
    Parameters:
    ---
    Returns:
        float: Memory usage percentage
    """
    return psutil.virtual_memory().percent

def get_swap_memory_info():
    """Returns the total, used, and free swap memory in GB.
    ---
    Parameters:
    --- 
    Returns:
        dict: Total, used, and free swap memory in GB
    """
    swap = psutil.swap_memory()
    total_swap = swap.total
    used_swap = swap.used
    free_swap = total_swap - used_swap  # Calculate free swap memory

    return {
        "total_swap": round(total_swap / CONVERSION_FACTOR_GB, 1),  # In GB
        "used_swap": round(used_swap / CONVERSION_FACTOR_GB, 1),    # In GB
        "free_swap": round(free_swap / CONVERSION_FACTOR_GB, 1)     # In GB
    }

def render_template_from_file(template_file_path, **context):
    """
    Renders a Jinja template from a file with the given context and returns the rendered HTML content.

    :param template_file_path: Path to the template file to render.
    :param context: Context variables to pass to the template.
    :return: Rendered HTML content as a string.
    """
    template_dir = os.path.dirname(template_file_path)
    template_file = os.path.basename(template_file_path)
    
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # Load the template file
    template = env.get_template(template_file)
    
    # Render the template with the provided context
    rendered_html = template.render(**context)
    
    return rendered_html

@functools.lru_cache(maxsize=1)
def get_os_info():
    kernel_version = platform.release()
    os_name = platform.system()

    # Return results in a dictionary
    return {
        "operating_system": os_name,
        "kernel_version": kernel_version
    }


def check_battery_status():
    battery = psutil.sensors_battery()
    
    output = {}
    if battery is not None:
        percent = battery.percent
        is_plugged = battery.power_plugged

        if is_plugged:
            status = "Charging"
        else:
            status = "Discharging"

        output = {
            "status": status,
            "percent": round(percent)
        }
        
    else:
        output = {
            "status": "Not available",
            "percent": 0
        }

    return output


@functools.lru_cache(maxsize=1)
def get_os_release_info():
    """
    Reads /etc/os-release and returns a dictionary with distribution information.
    """
    os_info = {}

    try:        
        with open('/etc/os-release', 'r') as file:
            print("Reading /etc/os-release file...")
            for line in file:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    # Remove surrounding quotes if present
                    value = value.strip('"')
                    # Add to dictionary
                    os_info[key] = value

        # Extract required information
        return {
            "os_name": os_info.get("NAME", "Unknown"),
            "os_version": os_info.get("VERSION_ID", "Unknown"),
            "os_codename": os_info.get("VERSION_CODENAME", "Unknown"),
            "os_full_name": os_info.get("PRETTY_NAME", "Unknown")
        }

    except FileNotFoundError:
        print("The /etc/os-release file was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@functools.lru_cache(maxsize=1)
def get_linux_processor_name():
    """ Get the processor name from /proc/cpuinfo.
    ---
    Parameters:
        None
    ---
    Returns:
        str: Processor name
    """
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if "model name" in line:
                    return line.split(":")[1].strip()
    except Exception as e:
        print(f"Error reading processor info: {e}")
        return None

def get_cached_value(key, fresh_value_func):
    """ Get a cached value if available and not expired, otherwise get fresh value. 
    ---
    Parameters:
        key (str): Key to store the value in the cache.
        fresh_value_func (function): Function to get the fresh value if the cache is expired.
    ---
    Returns:
        Any: Cached value if available and not expired, otherwise the fresh value.
    """
    general_settings = GeneralSettings.query.first()
    if general_settings:
        enable_cahce = general_settings.enable_cache
    
    current_time = time.time()
    # if key not in cache, create a new entry
    if key not in cache:
        cache[key] = {'value': None, 'timestamp': 0}

    # Check if cache is valid
    if enable_cahce and cache[key]['value'] is not None and (current_time - cache[key]['timestamp'] < CACHE_EXPIRATION):
        return cache[key]['value']

    # Fetch fresh value
    fresh_value = fresh_value_func()

    # Store value in cache
    cache[key]['value'] = fresh_value
    cache[key]['timestamp'] = current_time

    return fresh_value

def get_network_io():
    """
    Get the network I/O statistics.
    ---
    Parameters:
        None
    ---
    Returns:
        tuple: Network sent and received data in MB.
    """
    net_io = psutil.net_io_counters(pernic=False)
    network_sent = round(net_io.bytes_sent / CONVERSION_FACTOR_MB, 1)  # In MB
    network_received = round(net_io.bytes_recv / CONVERSION_FACTOR_MB, 1)  # In MB
    return network_sent, network_received


def get_cpu_metrics():
    """Collect all CPU-related metrics in one go"""
    try:
        cpu_freq = psutil.cpu_freq()
        temps = psutil.sensors_temperatures().get('coretemp', [None])[0]
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),  # Reduced interval
            'cpu_frequency': round(cpu_freq.current) if cpu_freq else 0,
            'cpu_max_frequency': round(cpu_freq.max) if cpu_freq else 0,
            'current_temp': getattr(temps, 'current', 0) if temps else 0,
            'high_temp': getattr(temps, 'high', 0) if temps else 0,
            'critical_temp': getattr(temps, 'critical', 0) if temps else 0,
            'cpu_usage_core': [round(x, 2) for x in psutil.cpu_percent(interval=0.1, percpu=True)]
        }
    except Exception as e:
        logger.error(f"Error collecting CPU metrics: {e}")
        return {}
    
def get_memory_metrics():
    """Collect all memory-related metrics in one go"""
    try:
        memory_info = psutil.virtual_memory()
        return {
            'memory_percent': round(memory_info.percent, 2),
            'memory_used': round((memory_info.total - memory_info.available) / CONVERSION_FACTOR_GB, 2),
            'memory_available': round(memory_info.total / CONVERSION_FACTOR_GB, 1),
            'dashboard_memory_usage': round(psutil.Process().memory_info().rss / CONVERSION_FACTOR_MB)
        }
    except Exception as e:
        logger.error(f"Error collecting memory metrics: {e}")
        return {}
    
def get_disk_metrics():
    """Collect all disk-related metrics in one go"""
    try:
        disk_info = psutil.disk_usage('/')
        disk_total = round(disk_info.total / CONVERSION_FACTOR_GB, 1)
        
        # Get disk I/O without sleep
        disk_io = psutil.disk_io_counters()
        read_speed = format_speed(disk_io.read_bytes)
        write_speed = format_speed(disk_io.write_bytes)

        return {
            'disk_percent': round(disk_info.percent, 2),
            'disk_total': disk_total,
            'disk_used': round(disk_info.used / CONVERSION_FACTOR_GB, 1),
            'disk_free': round(disk_info.free / CONVERSION_FACTOR_GB, 1),
            'disk_read': read_speed,
            'disk_write': write_speed
        }
    except Exception as e:
        logger.error(f"Error collecting disk metrics: {e}")
        return {}
    
def get_network_metrics():
    """Collect all network-related metrics in one go"""
    try:
        net_io = psutil.net_io_counters()
        network_sent = round(net_io.bytes_sent / CONVERSION_FACTOR_MB, 1)
        network_received = round(net_io.bytes_recv / CONVERSION_FACTOR_MB, 1)
        return {
            'network_sent': network_sent,
            'network_received': network_received,
            'network_stats': f"D: {network_sent} MB / U: {network_received} MB"
        }
    except Exception as e:
        logger.error(f"Error collecting network metrics: {e}")
        return {}
    
def get_battery_metrics():
    """Collect battery metrics"""
    try:
        battery = psutil.sensors_battery()
        if battery:
            return {
                'battery_percent': round(battery.percent),
                'battery_status': "Charging" if battery.power_plugged else "Discharging"
            }
        return {'battery_percent': 0, 'battery_status': "Not available"}
    except Exception as e:
        logger.error(f"Error collecting battery metrics: {e}")
        return {'battery_percent': 0, 'battery_status': "Not available"}
    
def get_process_metrics():
    """Collect process metrics with optimized collection"""
    try:
        process_dict = {}
        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent', 'pid'], ad_value=None):
            try:
                pinfo = p.info
                name = pinfo['name'].title()
                if name not in process_dict or pinfo['memory_percent'] > process_dict[name]['memory_percent']:
                    process_dict[name] = {
                        'cpu_percent': pinfo['cpu_percent'] or 0,
                        'memory_percent': pinfo['memory_percent'] or 0,
                        'pid': pinfo['pid']
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        top_processes = sorted(
            [(name, info['cpu_percent'], round(info['memory_percent'], 2), info['pid'])
             for name, info in process_dict.items()],
            key=lambda x: x[2],
            reverse=True
        )[:8]

        return {'top_processes': top_processes}
    except Exception as e:
        logger.error(f"Error collecting process metrics: {e}")
        return {'top_processes': []}

def _collect_metrics():
    """Optimized system information collection using parallel processing"""
    try:
        # Create a ThreadPoolExecutor to run metrics collection in parallel
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all metric collection tasks
            futures = {
                'cpu': executor.submit(get_cpu_metrics),
                'memory': executor.submit(get_memory_metrics),
                'disk': executor.submit(get_disk_metrics),
                'network': executor.submit(get_network_metrics),
                'battery': executor.submit(get_battery_metrics),
                'processes': executor.submit(get_process_metrics)
            }

            # Collect all results
            results = {}
            for key, future in futures.items():
                try:
                    results.update(future.result())
                except Exception as e:
                    logger.error(f"Error collecting {key} metrics: {e}")

        # Add timestamp
        results['timestamp'] = datetime.datetime.now()
        
        return results

    except Exception as e:
        logger.error(f"Error in _collect_metrics: {e}")
        return {}

def fetch_system_metrics():
    """ Get system information with caching for certain values and fresh data for others. 
    ---
    Parameters:
    ---
    Returns:
        dict: System information dictionary with various system metrics.
    """
    # get system username
    system_username = get_cached_value('system_username', get_system_username)
    nodename = get_cached_value('nodename', get_system_node_name)
    boot_time = get_cached_value('boot_time', lambda: datetime.datetime.fromtimestamp(psutil.boot_time()))
    uptime_dict = get_cached_value('uptime', lambda: format_uptime(datetime.datetime.now() - boot_time))
    current_server_time = datetime.datetime.now()
    ipv4_address = get_ip_address()
    os_info = get_cached_value('os_info', get_os_info)
    os_info.update(get_cached_value('os_release_info', get_os_release_info))
    
    # Prepare system information dictionary
    info = {
        "system_username": system_username,
        'nodename': nodename,
        'cpu_core': get_cpu_core_count(),
        'processor_name': get_linux_processor_name(),
        'boot_time': boot_time.strftime("%Y-%m-%d %H:%M:%S"),
        'process_count': len(psutil.pids()),
        'swap_memory': psutil.swap_memory().percent,
        'ipv4_connections': ipv4_address,
        'timestamp': datetime.datetime.now(),
        'current_server_time': current_server_time.strftime("%Y-%m-%d %H:%M:%S"),
        'timestamp': current_server_time,
        'os_info': os_info
    }
    # update uptime dictionary
    _info = _collect_metrics()
    info.update(uptime_dict)
    info.update(_info)

    return info
