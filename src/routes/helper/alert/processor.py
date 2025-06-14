# cython: language_level=3
from datetime import datetime
from src.logger import get_logger
logger = get_logger(__name__)

from src.routes.helper.notification.notification_helper import AlertNotifier
from schemas.alerts import AlertMessage

from src.models import (
    AlertLog,

)
from src.routes.helper.alert.ticket_assigner import create_alert_ticket


class AlertProcessor(AlertNotifier):
    def __init__(self, alert: dict):
        self.alert = alert
        self.alert_name = alert["labels"].get("alertname", "Unknown Alert")
        self.alert_status = alert.get("status", "firing")
        self.system_username = alert["labels"].get("username", "Unknown User")
        self.system_hostname = alert["labels"].get("system_hostname", "Unknown System")
        self.instance = alert["labels"].get("instance", "Unknown Instance")
        self.severity = alert["labels"].get("severity", "info")
        self.description = alert["annotations"].get("description", "No description provided")
        self.summary = alert["annotations"].get("summary", "No summary provided")
        self.fingerprint = alert.get("fingerprint", "Unknown Fingerprint")
        self.runbook_url = alert["annotations"].get("runbook_url", None)

    def process(self):
        # if self.fingerprint:
        #     existing_alert = AlertTicket.query.filter_by(fingerprint=self.fingerprint).first()
        #     if existing_alert and existing_alert.alert_status == "firing" and self.alert_status == "resolved":
        #         self.resolve_existing_alert(existing_alert)
        #         return
        #     elif existing_alert and existing_alert.alert_status == "resolved" and self.alert_status == "firing":
        #         logger.info(
        #             f"Alert with fingerprint {self.fingerprint} already exists and is resolved. Ignoring the alert."
        #         )
        #         return

        alert_instance = self.create_alert_instance()
        self.log_and_notify(alert_instance)

    def resolve_existing_alert(self, existing_alert):
        existing_alert.alert_status = self.alert_status
        existing_alert.updated_at = datetime.utcnow()
        log_message = f"SystemGuard Bot: Alert with fingerprint {self.fingerprint} updated to resolved status by systemgaurd(Auto-Resolve)."
        alert_log = AlertLog(alert_ticket_id=existing_alert.id, log=log_message) # type: ignore
        alert_log.save()
        existing_alert.save()
        logger.info(log_message)

    def create_alert_instance(self):
        return AlertMessage(
            alert_name=self.alert_name,
            alert_status=self.alert_status,
            instance=self.instance,
            severity=self.severity,
            description=self.description,
            summary=self.summary,
            system_username=self.system_username,
            system_hostname=self.system_hostname,
            fingerprint=self.fingerprint,
            runbook_url=self.runbook_url,
        )

    def log_and_notify(self, alert_instance):
        log_alert(alert_instance)
        create_alert_ticket(alert_instance)
        # AlertNotifier.notify_all(alert_instance)
        self.notify_all(alert_instance)

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
