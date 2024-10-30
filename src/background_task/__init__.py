# cython: language_level=3
import os
from src.background_task.log_system_info import initialize_logging



def start_background_tasks():
    """
    Starts the background tasks for the application.
    """
    if os.getenv('FLASK_ENV') == 'production':
        initialize_logging()