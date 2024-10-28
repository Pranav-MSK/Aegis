# cython: language_level=3
import os
import requests
import json
import time
import fpdf
from datetime import datetime
from flask_login import current_user

from src.config import db
from src.logger import logger
from src.alert_manager import (
    send_slack_alert,
    send_smtp_email,
    send_discord_alert,
    send_teams_alert,
    send_google_chat_alert,
)
from src.models import NotificationSettings, AlertTicket, UserProfile, AlertLog, Notification, UserNotification
from src.routes.helper.common_helper import get_email_addresses
from src.utils import render_template_from_file, ROOT_DIR
from src.routes.helper.alert_helper import can_create_alert


def send_test_alert(alertmanager_url, alert_name, severity, instance):
    # Generate a unique alert name by appending the current timestamp
    unique_alert_name = f"{alert_name}_{int(time.time())}"

    # Create a detailed description for the alert
    description = (
        f"This is a test alert generated at {time.strftime('%Y-%m-%d %H:%M:%S')}.\n"
        "This alert is intended for testing purposes only and does not indicate any real issues.\n"
        "If this alert appears in your monitoring system, please disregard it."
    )
    
    # Define the alert data with the unique alert name and improved annotations
    alert_data = [
        {
            "labels": {
                "alertname": unique_alert_name,
                "severity": severity,
                "instance": instance,
            },
            "annotations": {
                "description": description,
                "summary": f"Test Alert: {unique_alert_name}",
                "runbook_url": "Please refer to the documentation for troubleshooting steps.",
            },
        }
    ]

    # Send the POST request to Alertmanager
    try:
        response = requests.post(
            f"{alertmanager_url}/api/v2/alerts",
            headers={"Content-Type": "application/json"},
            data=json.dumps(alert_data),
        )

        # Check the response
        if response.status_code in (200, 202):
            return {
                "message": f"Test alert '{unique_alert_name}' sent successfully!",
                "status": 200,
            }
        else:
            return {
                "message": f"Failed to send alert. Response: {response.text}",
                "status": response.status_code,
            }

    except requests.exceptions.RequestException as e:
        return {
            "message": f"Request error occurred: {str(e)}",
            "status": 500,
        }
    except json.JSONDecodeError:
        return {
            "message": "Failed to decode JSON response from Alertmanager.",
            "status": 500,
        }
    except Exception as e:
        return {
            "message": f"An unexpected error occurred: {str(e)}",
            "status": 500,
        }


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
        if existing_alert and existing_alert.alert_status == "firing" and alert_status == "resolved":
            existing_alert.alert_status = alert_status
            existing_alert.updated_at = datetime.utcnow()
            # also log 
            log_message = f"SystemGuard Bot: Alert with fingerprint {fingerprint} updated to resolved status by systemgaurd(Auto-Resolve)."
            alert_log = AlertLog(
                alert_ticket_id=existing_alert.id,
                log=log_message
            )
            alert_log.save()
            existing_alert.save()
            logger.info(f"SystemGuard Bot: Alert with fingerprint {fingerprint} updated to resolved status by systemgaurd(Auto-Resolve).")
            return 
        elif existing_alert and existing_alert.alert_status == "resolved" and alert_status == "firing":
            logger.info(f"Alert with fingerprint {fingerprint} already exists and is resolved. Ignoring the alert.")
            return

    notification_data = {
        "type": severity,
        "icon": "info-circle",  # Font Awesome icon
        "title": alert_name,
        "message": description,
        "is_global": True
    }
    generate_system_notification(notification_data)

    log_alert(severity, alert_name, instance, description, summary)
    create_alert_ticket(alert_name, alert_status, instance, severity, description, summary, system_username, system_hostname, fingerprint, runbook_url)
    notify_alert(alert_name, instance, severity, description, summary)

def create_alert_ticket(alert_name, alert_status, instance, severity, 
                    description, summary, system_username, system_hostname, 
                    fingerprint, runbook_url=None):
    """
    Saves the alert data to the database.

    Args:
        alert_name (str): Name of the alert.
        instance (str): Instance generating the alert.
        severity (str): Severity level of the alert.
        description (str): Detailed alert description.
        summary (str): Brief alert summary.
    """
    # Fetch all supervisors with user_level "admin"
    all_supervisors = UserProfile.query.filter_by(user_level="admin").all()

    if not can_create_alert():
        logger.warning("Monthly alert ticket limit reached. Ignoring the alert.")
        return
    
    if not all_supervisors:
        assigned_supervisor_id = None
        logger.warning("No supervisors available to assign.")
    else:
        # Load calculation for each supervisor
        supervisor_loads = {
            supervisor.id: AlertTicket.query.filter(
                AlertTicket.assigned_supervisor_id == supervisor.id,
                AlertTicket.ticket_status.in_(["Open", "In Progress"])
            ).count()
            for supervisor in all_supervisors
        }
        logger.info(f"Supervisor loads: {supervisor_loads}")

        # Find the supervisor(s) with the minimum load
        min_load = min(supervisor_loads.values())
        eligible_supervisors = [supervisor_id for supervisor_id, load in supervisor_loads.items() if load == min_load]

        # If there's a tie, use round-robin logic based on the last assigned supervisor
        last_assigned_supervisor = AlertTicket.query.order_by(AlertTicket.id.desc()).first()
        last_assigned_supervisor_id = last_assigned_supervisor.assigned_supervisor_id if last_assigned_supervisor else None
        
        if last_assigned_supervisor_id in eligible_supervisors:
            # Continue from the last assigned supervisor
            last_index = eligible_supervisors.index(last_assigned_supervisor_id)
            next_index = (last_index + 1) % len(eligible_supervisors)
            assigned_supervisor_id = eligible_supervisors[next_index]
        else:
            # Assign the first eligible supervisor
            assigned_supervisor_id = eligible_supervisors[0]

    # Create and save the alert ticket
    alert_ticket = AlertTicket(
        alert_name=alert_name,
        alert_status=alert_status,
        instance=instance,
        severity=severity,
        summary=summary,
        description=description,
        assigned_supervisor_id=assigned_supervisor_id,
        system_username=system_username,
        system_hostname=system_hostname,
        fingerprint=fingerprint,
        runbook_url=runbook_url
    )
    alert_ticket.save()
    logger.info(f"Saving alert ticket: {alert_ticket}")

def log_alert(severity, alert_name, instance, description, summary):
    """
    Logs the alert message with the appropriate log level based on its severity.

    Args:
        severity (str): Severity level of the alert (e.g., critical, warning, info).
        alert_name (str): Name of the alert.
        instance (str): Instance generating the alert.
        description (str): Detailed alert description.
        summary (str): Brief alert summary.
    """
    message = f"Alert: {alert_name}"

    log_method = {
        "critical": logger.error,
        "warning": logger.warning,
        "info": logger.info,
        "debug": logger.debug,
    }.get(severity, logger.info)
    log_method(message)


def get_notification_settings():
    """
    Retrieves the notification settings from the database.

    Returns:
        dict: Dictionary of notification settings.
    """
    return NotificationSettings().to_dict()

def is_enabled(notification_config, setting_key):
    """
    Checks if a particular notification setting is enabled.

    Args:
        notification_config (dict): Notification settings configuration.
        setting_key (str): The key corresponding to the setting.
    
    Returns:
        bool: True if the setting is enabled, False otherwise.
    """
    return notification_config.get(setting_key, False)

def send_slack_alert_wrapper(config, alert_name, instance, severity, description, summary):
    """
    Sends a Slack alert using the provided configuration.

    Args:
        config (dict): Notification configuration.
        alert_name (str), instance (str), severity (str), description (str), summary (str)
    """
    slack_webhook = config.get("slack_webhook_url")
    if slack_webhook:
        send_slack_alert(slack_webhook, alert_name, instance, severity, description, summary)
          

def send_email_alert_wrapper(alert_name, instance, severity, description, summary):
    """
    Sends email alerts to administrators.

    Args:
        alert_name (str), description (str), summary (str)
    """
    admin_emails = get_email_addresses(user_level="admin", receive_email_alerts=True)
    logger.info(f"Sending email alert to {admin_emails}")
    context = {
        "alert_name": alert_name,
        "instance": instance,
        "severity": severity,
        "description": description,
        "summary": summary, 
    }

    login_alert_template = os.path.join(
        ROOT_DIR, "src/templates/email_templates/alert_template.html"
    )
    email_body = render_template_from_file(
        login_alert_template, **context
    )
    if admin_emails:
        send_smtp_email(
            receiver_email=admin_emails,
            subject=f"{alert_name} Alert",
            body=email_body,
            is_html=True,
        )


def send_discord_alert_wrapper(config, alert_name, instance, severity, description, summary):
    """
    Sends a Discord alert using the provided configuration.
    """
    discord_webhook = config.get("discord_webhook_url")
    if discord_webhook:
        send_discord_alert(
            discord_webhook, alert_name, instance, severity, description, summary
        )


def send_teams_alert_wrapper(config, alert_name, instance, severity, description, summary):
    """
    Sends a Microsoft Teams alert using the provided configuration.
    """
    teams_webhook_url = config.get("teams_webhook_url")
    if teams_webhook_url:
        send_teams_alert(
            teams_webhook_url, alert_name, instance, severity, description, summary
        )
   
def send_google_chat_alert_wrapper(config, alert_name, instance, severity, description, summary):
    """
    Sends a Google Chat alert using the provided configuration.
    """

    google_chat_webhook_url = config.get("google_chat_webhook_url")
    if google_chat_webhook_url:
        send_google_chat_alert(
            google_chat_webhook_url, alert_name, instance, severity, description, summary
        )


def notify_alert(alert_name, instance, severity, description, summary):
    """
    Sends notifications for the alert via Slack, email, and Discord.

    Args:
        alert_name (str): Name of the alert.
        instance (str): Instance associated with the alert.
        severity (str): Severity level of the alert.
        description (str): Detailed description of the alert.
        summary (str): Brief summary of the alert.
    """
    notification_config = get_notification_settings()

    if is_enabled(notification_config, "is_email_alert_enabled"):
        send_email_alert_wrapper(alert_name, instance, severity, description, summary)

    if is_enabled(notification_config, "is_slack_alert_enabled"):
        send_slack_alert_wrapper(notification_config, alert_name, instance, severity, description, summary)

    if is_enabled(notification_config, "is_discord_alert_enabled"):
        send_discord_alert_wrapper(notification_config, alert_name, instance, severity, description, summary)

    if is_enabled(notification_config, "is_teams_alert_enabled"):
        send_teams_alert_wrapper(notification_config, alert_name, instance, severity, description, summary)

    if is_enabled(notification_config, "is_google_chat_alert_enabled"):
        send_google_chat_alert_wrapper(notification_config, alert_name, instance, severity, description, summary)


class PDF(fpdf.FPDF):
    def header(self):
        self.set_font("Arial", 'B', 14)
        self.cell(0, 10, "Alert Ticket Report", 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font("Arial", 'B', 12)
        self.set_fill_color(220, 220, 220)  # Light gray background
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(5)

    def chapter_body(self, body):
        self.set_font("Arial", '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_table(self, header, data):
        self.set_font("Arial", 'B', 12)
        self.set_fill_color(200, 200, 200)  # Gray header
        for col in header:
            self.cell(60, 10, col, 1, 0, 'C', 1)
        self.ln()

        self.set_font("Arial", '', 12)
        for row in data:
            for item in row:
                self.cell(60, 10, item, 1)
            self.ln()

    def add_icon(self, icon_path, size=(10, 10)):
        self.image(icon_path, x=None, y=None, w=size[0], h=size[1])

def generate_alert_ticket_pdf(alert, investigation_notes, alert_logs):
    pdf = PDF(format='letter')
    pdf.add_page()

    # Add alert ticket details
    pdf.chapter_title("Alert Information")
    pdf.chapter_body(f"Alert Name: {alert.alert_name}")
    pdf.chapter_body(f"Instance: {alert.instance}")
    pdf.chapter_body(f"Severity: {alert.severity}")
    pdf.chapter_body(f"Description: {alert.description}")
    pdf.chapter_body(f"Summary: {alert.summary}")
    pdf.chapter_body(f"Assigned Investigator: {alert.assigned_user.username if alert.assigned_user else 'Unassigned'}")
    pdf.chapter_body(f"Assigned Supervisor: {alert.assigned_supervisor.username if alert.assigned_supervisor else 'Unassigned'}")
    pdf.chapter_body(f"Created At: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.chapter_body(f"Last Updated At: {alert.updated_at.strftime('%Y-%m-%d %H:%M:%S') if alert.updated_at else 'N/A'}")

    # Add Investigation Notes
    pdf.chapter_title("Investigation Notes")
    notes_data = [(note.created_at.strftime('%Y-%m-%d %H:%M:%S'), note.user.username, note.note) for note in investigation_notes.items]
    pdf.add_table(["Date", "User", "Note"], notes_data)

    # Add Alert Logs
    pdf.chapter_title("Alert Logs")
    logs_data = [(log.created_at.strftime('%Y-%m-%d %H:%M:%S'), log.log) for log in alert_logs.items]
    pdf.add_table(["Date", "Log"], logs_data)

    # Save the PDF
    pdf_file_path = "alert_ticket.pdf"
    pdf.output(pdf_file_path)

    return pdf_file_path

def generate_system_notification(notification_data, user_id=None):
    new_notification = Notification(
        type=notification_data.get('type', 'info'),
        icon=notification_data.get('icon', 'info-circle'),
        title=notification_data['title'],
        message=notification_data['message'],
        is_global=notification_data.get('is_global', False)
    )
    new_notification.save()
    
    if new_notification.is_global:
        # user_notification = UserNotification(user_id=user_id, notification_id=new_notification.id)
        for user in UserProfile.query.all():
            user_notification = UserNotification(user_id=user.id, notification_id=new_notification.id)
            user_notification.save()
    else:
        if not user_id:
            user_id = current_user.id
        user_notification = UserNotification(user_id=user_id, notification_id=new_notification.id)
    user_notification.save()