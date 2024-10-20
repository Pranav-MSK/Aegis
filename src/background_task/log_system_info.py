# cython: language_level=3
import datetime
from threading import Timer
from sqlalchemy.exc import SQLAlchemyError

from src.logger import logger
from src.config import app, db
from src.utils import _collect_metrics
from src.logger import logger
from src.models import GeneralSettings, SystemInformation
# Flag to track if logging is already scheduled
is_logging_scheduled = False
fetch_system_info_interval = 1

from src.background_task.prometheus_metrics import metrics

def log_system_info():
    """
    Logs system information at regular intervals based on the general settings.
    This function checks if logging is enabled and schedules the next log if active.
    """
    global is_logging_scheduled
    with app.app_context():
        try:
            if not is_logging_enabled():
                logger.info("System info logging has been stopped.")
                is_logging_scheduled = False
                return

            log_system_info_to_db()
            logger.debug("System information logged successfully.")
            schedule_next_log(interval=fetch_system_info_interval)

        except Exception as e:
            logger.error(f"Error during system info logging: {e}")
            is_logging_scheduled = False


def is_logging_enabled():
    """
    Checks if system info logging is enabled in the general settings.
    """
    try:
        general_settings = GeneralSettings.query.first()
        return general_settings.is_logging_system_info if general_settings else False
    except SQLAlchemyError as e:
        logger.error(f"Error fetching general settings: {e}")
        return False


def schedule_next_log(interval=10):
    """
    Schedules the next logging event after the specified interval (in seconds).
    """
    Timer(interval, log_system_info).start()


def log_system_info_to_db():
    """
    Fetches system information and logs it to the database and updates Prometheus metrics.
    """
    with app.app_context():
        try:
            system_info = _collect_metrics()

            # Update Prometheus metrics
            update_prometheus_metrics(system_info)

            logger.info("System information logged to database.")

        except SQLAlchemyError as db_err:
            logger.error(f"Database error while logging system info: {db_err}")
            db.session.rollback()
        except Exception as e:
            logger.error(f"Failed to log system information: {e}")


def update_prometheus_metrics(system_info):
    """
    Updates Prometheus metrics with the latest system information.
    """
    metrics['cpu_usage_metric'].set(system_info['cpu_percent'])
    metrics['memory_usage_metric'].set(system_info['memory_percent'])
    metrics['disk_usage_metric'].set(system_info['disk_percent'])
    metrics['network_sent_metric'].set(system_info['network_sent'])
    metrics['network_recv_metric'].set(system_info['network_received'])
    metrics['cpu_temp_metric'].set(system_info['current_temp'])
    metrics['cpu_frequency_metric'].set(system_info['cpu_frequency'])
    metrics['battery_percentage_metric'].set(system_info['battery_percent'])
    metrics['dashboard_memory_usage_metric'].set(system_info['dashboard_memory_usage'])
    metrics['request_count'].inc()


def store_system_info_in_db(system_info):
    """
    Stores the collected system information into the database.
    """
    system_log = SystemInformation(
        cpu_percent=system_info["cpu_percent"],
        memory_percent=system_info["memory_percent"],
        battery_percent=system_info["battery_percent"],
        network_sent=system_info["network_sent"],
        network_received=system_info["network_received"],
        dashboard_memory_usage=system_info["dashboard_memory_usage"],
        cpu_frequency=system_info["cpu_frequency"],
        current_temp=system_info["current_temp"],
        timestamp=datetime.datetime.now(),
    )
    system_log.save()


def monitor_settings():
    """
    Monitors application general settings for changes and controls system logging dynamically.
    """
    global is_logging_scheduled
    with app.app_context():
        try:
            if is_logging_enabled():
                logger.info("System logging enabled. Starting system info logging.")
                if not is_logging_scheduled:
                    logger.debug("Scheduling system info logging.")
                    Timer(0, log_system_info).start()
                    is_logging_scheduled = True
            else:
                logger.info("System logging disabled. Stopping system info logging.")
                is_logging_scheduled = False

            # Recheck settings every 10 seconds
            Timer(10, monitor_settings).start()

        except SQLAlchemyError as db_err:
            logger.error(f"Error fetching settings: {db_err}")
