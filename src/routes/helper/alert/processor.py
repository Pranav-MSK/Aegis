# cython: language_level=3
from datetime import datetime
from src.logger import get_logger
logger = get_logger(__name__)

from src.routes.helper.notification.notification_helper import notify_alert
from src.routes.helper.alert.models import AlertMessage
from src.routes.helper.notification.manager import generate_system_notification

from src.models import (
    AlertTicket,
    AlertLog,

)
from src.routes.helper.alert.ticket_assigner import create_alert_ticket

def process_alert(alert):
    """
    Handles an individual alert by extracting necessary details and
    triggering logging and notification mechanisms.

    Args:
        alert (dict): The alert payload containing labels and annotations.
    """
    alert_name = alert["labels"].get("alertname", "Unknown Alert")
    alert_status = alert.get("status", "firing")
    system_username = alert["labels"].get("username", "Unknown User")
    system_hostname = alert["labels"].get("system_hostname", "Unknown System")
    instance = alert["labels"].get("instance", "Unknown Instance")
    severity = alert["labels"].get("severity", "info")
    description = alert["annotations"].get("description", "No description provided")
    summary = alert["annotations"].get("summary", "No summary provided")
    fingerprint = alert.get("fingerprint", None)
    runbook_url = alert["annotations"].get("runbook_url", None)

    # check if fingerprint already exists
    if fingerprint:
        existing_alert = AlertTicket.query.filter_by(fingerprint=fingerprint).first()
        # if alert_status of existing alert is "firing" and new alert_status is "resolved", update the existing alert
        if (
            existing_alert
            and existing_alert.alert_status == "firing"
            and alert_status == "resolved"
        ):
            existing_alert.alert_status = alert_status
            existing_alert.updated_at = datetime.utcnow()
            # also log
            log_message = f"SystemGuard Bot: Alert with fingerprint {fingerprint} updated to resolved status by systemgaurd(Auto-Resolve)."
            alert_log = AlertLog(alert_ticket_id=existing_alert.id, 
                                 log=log_message)
            alert_log.save()
            existing_alert.save()
            logger.info(
                f"SystemGuard Bot: Alert with fingerprint {fingerprint} updated to resolved status by systemgaurd(Auto-Resolve)."
            )
            return
        elif (
            existing_alert
            and existing_alert.alert_status == "resolved"
            and alert_status == "firing"
        ):
            logger.info(
                f"Alert with fingerprint {fingerprint} already exists and is resolved. Ignoring the alert."
            )
            return

    notification_data = {
        "type": severity,
        "icon": "info-circle",  # Font Awesome icon
        "title": alert_name,
        "message": description,
        "is_global": True,
    }
    generate_system_notification(notification_data)

    # Create an Alert object to encapsulate the alert details
    alert_instance = AlertMessage(
        alert_name=alert_name,
        alert_status=alert_status,
        instance=instance,
        severity=severity,
        description=description,
        summary=summary,
        system_username=system_username,
        system_hostname=system_hostname,
        fingerprint=fingerprint,
        runbook_url=runbook_url,
    )

    log_alert(alert_instance)
    create_alert_ticket(alert_instance)
    notify_alert(alert_instance)

def log_alert(alert_instance):
    """
    Logs an alert using the appropriate log level based on the alert's severity.

    Args:
        alert_instance (object): An object with attributes:
            - severity (str): Severity level of the alert (e.g., critical, warning, info, debug).
            - alert_name (str): Name of the alert.
            - instance (str): Instance generating the alert.
            - summary (str): Brief summary of the alert.
            - description (str): Detailed description of the alert.
    """
    message = (
        f"[{alert_instance.severity.upper()}] "
        f"{alert_instance.alert_name} on {alert_instance.instance}: "
        f"{alert_instance.summary} - {alert_instance.description}"
    )

    log_method = {
        "critical": logger.error,
        "warning": logger.warning,
        "info": logger.info,
        "debug": logger.debug,
    }.get(alert_instance.severity.lower(), logger.info)

    log_method(message)
