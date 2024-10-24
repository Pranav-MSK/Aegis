# cython: language_level=3
import os
from src.background_task.log_system_info import initialize_logging
from src.background_task.disk_manager import DiskMetrics
from src.background_task.network_manager import NetworkMetrics
from src.logger import logger



def start_background_tasks():
    """
    Starts the background tasks for the application.
    """
    initialize_logging()
