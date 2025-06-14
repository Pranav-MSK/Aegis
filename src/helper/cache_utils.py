
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