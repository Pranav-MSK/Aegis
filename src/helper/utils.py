# cython: language_level=3
import os
import time
import platform
import datetime
import subprocess
import psutil
import requests
import GPUtil
import functools
from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from functools import lru_cache

from src.helper.logger import get_logger
from src.models import GeneralSettings
from src.helper.basic_info import get_basic_system_information, get_ip_address
from src.config.config_loader import configuration_settings

logger = get_logger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cache = {}

CACHE_EXPIRATION = configuration_settings.getint("metrics.settings", "CACHE_EXPIRATION")
DIVIDE_BY_1024 = configuration_settings.getboolean("metrics.settings", "DIVIDE_BY_1024")

CONVERSION_FACTOR_MB = 1024**2 if DIVIDE_BY_1024 else 1000**2
CONVERSION_FACTOR_GB = 1024**3 if DIVIDE_BY_1024 else 1000**3
domain_name = "google.com"

def run_speedtest():
    """Run a speed test using speedtest-cli."""
    try:
        result = subprocess.run(
            ["speedtest-cli"], capture_output=True, text=True, check=True
        )
        output_lines = result.stdout.splitlines()
        download_speed = upload_speed = ping = None

        for line in output_lines:
            if "Download:" in line:
                download_speed = line.split("Download: ")[1]
            elif "Upload:" in line:
                upload_speed = line.split("Upload: ")[1]
            elif "Ping:" in line:
                ping = line.split("Ping: ")[1]

        return {
            "download_speed": download_speed,
            "upload_speed": upload_speed,
            "ping": ping,
            "status": "Success",
        }

    except subprocess.CalledProcessError as e:
        return {"status": "Error", "message": e.stderr}

    except Exception as e:
        return {"status": "Error", "message": str(e)}


def format_speed(speed):
    """Format the speed in appropriate units."""
    if speed < 1000:
        return f"{speed:.2f} Bytes/s"
    elif speed < 1000**2:
        return f"{speed / 1000:.2f} KB/s"
    else:
        return f"{speed / (1000 ** 2):.2f} MB/s"


def render_template_from_file(template_file_path, **context):
    """Renders a Jinja template from a file with the given context and returns the rendered HTML content."""
    template_dir = os.path.dirname(template_file_path)
    template_file = os.path.basename(template_file_path)

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_file)

    return template.render(**context)


@functools.lru_cache(maxsize=1)
def get_os_info():
    return {"operating_system": platform.system(), "kernel_version": platform.release()}


@functools.lru_cache(maxsize=1)
def get_os_release_info():
    """Reads /etc/os-release and returns a dictionary with distribution information."""
    try:
        with open("/etc/os-release", "r") as file:
            os_info = dict(line.strip().split("=", 1) for line in file if "=" in line)
        return {
            "os_name": os_info.get("NAME", "").strip('"'),
            "os_version": os_info.get("VERSION_ID", "").strip('"'),
            "os_codename": os_info.get("VERSION_CODENAME", "").strip('"'),
            "os_full_name": os_info.get("PRETTY_NAME", "").strip('"'),
        }
    except Exception as e:
        logger.error(f"Error reading os-release: {e}")
        return {}


@functools.lru_cache(maxsize=1)
def get_linux_processor_name():
    """Get the processor name from /proc/cpuinfo."""
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":")[1].strip()
    except Exception as e:
        logger.error(f"Error reading processor info: {e}")
        return None


def get_cached_value(key, fresh_value_func):
    """Get a cached value if available and not expired, otherwise get fresh value."""
    current_time = time.time()
    if key not in cache:
        cache[key] = {"value": None, "timestamp": 0}

    general_settings = GeneralSettings.query.first()
    enable_cache = general_settings.enable_cache if general_settings else False

    if (
        enable_cache
        and cache[key]["value"] is not None
        and (current_time - cache[key]["timestamp"] < CACHE_EXPIRATION)
    ):
        return cache[key]["value"]

    fresh_value = fresh_value_func()
    cache[key]["value"] = fresh_value
    cache[key]["timestamp"] = current_time
    return fresh_value


def get_cpu_metrics():
    """Collect all CPU-related metrics in one go"""
    cpu_freq = psutil.cpu_freq()
    temps = psutil.sensors_temperatures().get("coretemp", [None])[0]
    return {
        "cpu_core": psutil.cpu_count(logical=True),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "cpu_frequency": round(cpu_freq.current) if cpu_freq else 0,
        "cpu_max_frequency": round(cpu_freq.max) if cpu_freq else 0,
        "current_temp": getattr(temps, "current", 0) if temps else 0,
        "high_temp": getattr(temps, "high", 0) if temps else 0,
        "critical_temp": getattr(temps, "critical", 0) if temps else 0,
        "cpu_usage_core": [
            round(x, 2) for x in psutil.cpu_percent(interval=0.1, percpu=True)
        ],
    }


def get_gpu_metrics():
    """Collect all GPU-related metrics in one go"""
    gpus = GPUtil.getGPUs()

    if gpus:
        main_gpu = gpus[0]  # Assuming the first GPU is the main one
        return {
            "is_gpu": True,
            "gpu_id": main_gpu.id,
            "gpu_name": main_gpu.name,
            "gpu_load": round(main_gpu.load * 100, 2),  # Load in percentage
            "gpu_memory_total": main_gpu.memoryTotal,
            "gpu_memory_used": main_gpu.memoryUsed,
            "gpu_memory_free": main_gpu.memoryFree,
            "gpu_temperature": main_gpu.temperature,
        }


def get_memory_metrics():
    """Collect all memory-related metrics in one go"""
    memory_info = psutil.virtual_memory()
    return {
        "memory_percent": round(memory_info.percent, 2),
        "memory_used": round(
            (memory_info.total - memory_info.available) / CONVERSION_FACTOR_GB, 2
        ),
        "memory_available": round(memory_info.total / CONVERSION_FACTOR_GB, 1),
        "dashboard_memory_usage": round(
            psutil.Process().memory_info().rss / CONVERSION_FACTOR_MB
        ),
    }


def get_disk_metrics():
    """Collect all disk-related metrics in one go"""
    # Initial metrics
    disk_info = psutil.disk_usage("/")

    return {
        "disk_percent": round(disk_info.percent, 2),
        "disk_total": round(disk_info.total / CONVERSION_FACTOR_GB, 1),
        "disk_used": round(disk_info.used / CONVERSION_FACTOR_GB, 1),
        "disk_free": round(disk_info.free / CONVERSION_FACTOR_GB, 1),
    }


def get_battery_metrics():
    """Collect battery metrics"""
    try:
        battery = psutil.sensors_battery()
        if battery:
            time_remaining = battery.secsleft
            if time_remaining == psutil.POWER_TIME_UNKNOWN:
                time_remaining_str = "Calculating..."
            else:
                hours, remainder = divmod(time_remaining, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_remaining_str = f"{hours}h {minutes}m {seconds}s"

            return {
                "battery_percent": round(battery.percent),
                "battery_status": (
                    "Charging" if battery.power_plugged else "Discharging"
                ),
                "battery_time_remaining": time_remaining_str,
                "battery_health": "Good" if battery.percent > 20 else "Low",
            }
        else:
            return {
                "battery_percent": 0,
                "battery_status": "Not available",
                "time_remaining": "N/A",
                "battery_health": "N/A",
            }
    except Exception as e:
        logger.error(f"Error collecting battery metrics: {e}")
        return {
            "battery_percent": 0,
            "battery_status": "N/A",
            "time_remaining": "N/A",
            "battery_health": "N/A",
        }


def get_top_processes(number=5, combined=False):
    """Get the top processes by memory usage."""
    if combined:
        combined_processes = defaultdict(
            lambda: {"cpu_percent": 0, "memory_percent": 0, "pid": None}
        )

        for p in psutil.process_iter(["name", "cpu_percent", "memory_percent", "pid"]):
            try:
                name = p.info["name"].title()
                pinfo = p.info
                if pinfo["memory_percent"] > combined_processes[name]["memory_percent"]:
                    combined_processes[name] = {
                        "cpu_percent": pinfo["cpu_percent"] or 0,
                        "memory_percent": pinfo["memory_percent"] or 0,
                        "pid": pinfo["pid"],
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        processes = sorted(
            [
                (
                    name,
                    info["cpu_percent"],
                    round(info["memory_percent"], 2) if info["memory_percent"] is not None else 0,
                    info["pid"],
                )
                for name, info in combined_processes.items()
            ],
            key=lambda x: x[2],
            reverse=True,
        )[:number]
    else:
        processes = [
            (
                p.info["name"].title(),
                p.info["cpu_percent"],
                round(p.info["memory_percent"], 2),
                p.info["pid"],
            )
            for p in sorted(
                psutil.process_iter(["name", "cpu_percent", "memory_percent", "pid"]),
                key=lambda p: p.info["memory_percent"],
                reverse=True,
            )[:number]
        ]

    return processes


def get_process_metrics(num_processes=12):
    """Collect process metrics with optimized collection"""
    try:
        return {"top_processes": get_top_processes(number=num_processes, combined=True)}
    except Exception as e:
        logger.error(f"Error collecting process metrics: {e}")
        return {"top_processes": []}


@lru_cache(maxsize=1)
def get_instance_metadata():
    """
    Retrieve all available metadata about the current EC2 instance.

    Returns:
        dict: A dictionary containing all instance metadata.
    """
    base_url = "http://169.254.169.254/latest/meta-data/"
    metadata = {}

    try:
        logger.info("Fetching instance metadata")
        # Get a session token for IMDSv2
        token_response = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={
                "X-aws-ec2-metadata-token-ttl-seconds": "21600"
            },  # Token valid for 6 hours
        )
        token_response.raise_for_status()
        token = token_response.text

        # Get all metadata categories
        response = requests.get(base_url, headers={"X-aws-ec2-metadata-token": token})
        response.raise_for_status()  # Raise an error for bad responses

        # List all metadata keys
        keys = response.text.splitlines()

        for key in keys:
            # Fetch each piece of metadata
            full_url = f"{base_url}{key}"
            value_response = requests.get(
                full_url, headers={"X-aws-ec2-metadata-token": token}
            )
            metadata[key] = value_response.text

        return metadata

    except requests.RequestException as e:
        print(f"Error fetching instance metadata: {e}")
        return {}


def _collect_metrics():
    """Optimized system information collection using parallel processing"""
    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                "cpu": executor.submit(get_cpu_metrics),
                "memory": executor.submit(get_memory_metrics),
                "disk": executor.submit(get_disk_metrics),
                "battery": executor.submit(get_battery_metrics),
                "processes": executor.submit(get_process_metrics),
            }

            results = {}
            for key, future in futures.items():
                try:
                    results.update(future.result())
                except Exception as e:
                    logger.error(f"Error collecting {key} metrics: {e}")

        results["timestamp"] = datetime.datetime.now()
        results["process_count"] = len(psutil.pids())

        return results

    except Exception as e:
        logger.error(f"Error in _collect_metrics: {e}")
        return {}


def fetch_system_metrics():
    """Get system information with caching for certain values and fresh data for others."""
    boot_time = get_cached_value(
        "boot_time", lambda: datetime.datetime.fromtimestamp(psutil.boot_time())
    )
    ipv4_address = get_ip_address()
    os_info = get_cached_value("os_info", get_os_info)
    os_info.update(get_cached_value("os_release_info", get_os_release_info))

    info = {
        "processor_name": get_linux_processor_name(),
        "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
        "swap_memory": psutil.swap_memory().percent,
        "ipv4_connections": ipv4_address,
        "os_info": os_info,
    }
    info.update(_collect_metrics())
    info.update(get_basic_system_information())

    return info
