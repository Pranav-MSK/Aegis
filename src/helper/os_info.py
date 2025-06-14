
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
from src.helper.helper import get_basic_system_information, get_ip_address
from src.config.config_loader import configuration_settings

logger = get_logger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cache = {}

CACHE_EXPIRATION = configuration_settings.getint("metrics.settings", "CACHE_EXPIRATION")
DIVIDE_BY_1024 = configuration_settings.getboolean("metrics.settings", "DIVIDE_BY_1024")

CONVERSION_FACTOR_MB = 1024**2 if DIVIDE_BY_1024 else 1000**2
CONVERSION_FACTOR_GB = 1024**3 if DIVIDE_BY_1024 else 1000**3
domain_name = "google.com"


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
