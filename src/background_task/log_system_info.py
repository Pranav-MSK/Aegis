# cython: language_level=3
import datetime
from threading import Timer, Lock
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

from src.logger import logger
from src.config import app, db
from src.utils import _collect_metrics
from src.models import GeneralSettings
from src.background_task.prometheus_metrics import metrics

# Constants
LOGGING_INTERVAL = 1  # Log every second
SETTINGS_CHECK_INTERVAL = 60  # Check settings every minute

# Global state management
class LoggingState:
    def __init__(self):
        self.is_logging_scheduled = False
        self.is_enabled = False
        self.lock = Lock()

state = LoggingState()

@contextmanager
def app_context():
    """
    Context manager to ensure proper application context handling.
    """
    ctx = app.app_context()
    ctx.push()
    try:
        yield
    finally:
        ctx.pop()

def log_system_info():
    """
    Logs system information at regular intervals.
    Ensures all database operations occur within application context.
    """
    if not state.is_enabled:
        return

    try:
        # Collect metrics outside app context as it doesn't need database
        system_info = _collect_metrics()
        
        with app_context():
            update_prometheus_metrics(system_info)
        
        # Schedule next log immediately to maintain timing accuracy
        Timer(LOGGING_INTERVAL, log_system_info).start()
        
    except Exception as e:
        logger.error(f"Error during system info logging: {e}")
        # Attempt to recover by scheduling next run
        Timer(LOGGING_INTERVAL, log_system_info).start()


def update_prometheus_metrics(system_info):
    """
    Updates Prometheus metrics with the latest system information.
    """
    try:
        metrics_mapping = {
            'cpu_usage_metric': system_info['cpu_percent'],
            'memory_usage_metric': system_info['memory_percent'],
            'disk_usage_metric': system_info['disk_percent'],
            'network_sent_metric': system_info['network_sent'],
            'network_recv_metric': system_info['network_received'],
            'cpu_temp_metric': system_info['current_temp'],
            'cpu_frequency_metric': system_info['cpu_frequency'],
            'battery_percentage_metric': system_info['battery_percent'],
            'dashboard_memory_usage_metric': system_info['dashboard_memory_usage']
        }
        # Batch update metrics
        for metric_name, value in metrics_mapping.items():
            metrics[metric_name].set(value)
            
        metrics['request_count'].inc()
    except Exception as e:
        logger.error(f"Failed to update Prometheus metrics: {e}")


def check_settings():
    """
    Periodically checks application settings and manages logging state.
    Ensures proper application context for database operations.
    """
    try:
        with app_context():
            with state.lock:
                previous_state = state.is_enabled
                current_state = is_logging_enabled()
                state.is_enabled = current_state

                # Only log state changes to reduce noise
                if previous_state != current_state:
                    if current_state:
                        logger.info("System logging enabled. Starting system info logging.")
                        if not state.is_logging_scheduled:
                            Timer(0, log_system_info).start()
                            state.is_logging_scheduled = True
                    else:
                        logger.info("System logging disabled. Stopping system info logging.")
                        state.is_logging_scheduled = False

        # Schedule next settings check
        Timer(SETTINGS_CHECK_INTERVAL, check_settings).start()

    except Exception as e:
        logger.error(f"Error checking settings: {e}")
        # Retry settings check after a delay
        Timer(SETTINGS_CHECK_INTERVAL, check_settings).start()


def is_logging_enabled():
    """
    Checks if system info logging is enabled in the general settings.
    Must be called within application context.
    """
    try:
        general_settings = GeneralSettings.query.first()
        return bool(general_settings and general_settings.is_logging_system_info)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching general settings: {e}")
        return False


def initialize_logging():
    """
    Initialize the logging system with proper state management and application context.
    """
    with app_context():
        with state.lock:
            state.is_enabled = is_logging_enabled()
            if state.is_enabled and not state.is_logging_scheduled:
                Timer(0, log_system_info).start()
                state.is_logging_scheduled = True
    
    # Start the settings monitoring loop
    Timer(0, check_settings).start()