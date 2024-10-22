# cython: language_level=3
import os
from src.background_task.monitor_website import start_website_monitoring
from src.background_task.log_system_info import monitor_settings
from src.logger import logger



def start_background_tasks():
    """
    Starts the background tasks for the application.
    """
    if os.getenv('FLASK_ENV') == 'production':
        logger.info("Starting background tasks for production environment.")
        start_website_monitoring()
        monitor_settings()