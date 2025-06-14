# cython: language_level=3
import json
import requests
from datetime import datetime
from src.helper.logger import get_logger

logger = get_logger(__name__)

def send_slack_alert(webhook_url, alert_instance):
    """
    Sends a formatted notification message to a Slack channel via webhook.
    
    Parameters:
    webhook_url (str): The Slack incoming webhook URL.
    alert_name (str): The name of the alert.
    instance (str): The instance related to the alert.
    severity (str): The severity level of the alert.
    description (str): A detailed description of the alert.
    summary (str): Summary of the alert. Default is "Prometheus Alert".
    color (str): Color of the message attachment.
    username (str): Username of the bot sending the message.
    icon_emoji (str): Emoji icon to show in Slack.
    """

    # Build the payload
    color_dict = {
        "critical": "#ee1b1b", # Red
        "warning": "#eeee1b", # Yellow
        "info": "#16d119" # Green
    }
    
    payload = {
        "username": "SystemGuard Alert",
        "attachments": [
            {
                "fallback": alert_instance.alert_name,
                "color": color_dict.get(alert_instance.severity, "gray"),
                "title": alert_instance.alert_name,
                "text": alert_instance.summary,
                "fields": [
                    {"title": "Instance", "value": alert_instance.instance, "short": True},
                    {"title": "Severity", "value": alert_instance.severity, "short": True},
                    {"title": "Description", "value": alert_instance.description, "short": False},
                ],
                "footer": "System Metrics",
                "ts": f"{datetime.now().timestamp()} UTC"
            }
        ]
    }
    
    # Send the POST request to the Slack webhook URL
    response = requests.post(webhook_url, 
                             data=json.dumps(payload), 
                             headers={'Content-Type': 'application/json'},
                             timeout=10)
    
    # Check the response status
    if response.status_code != 200:
        raise Exception(f"Request to Slack failed with status code {response.status_code}, response: {response.text}")
    
    logger.info(f"Alert sent to Slack: {alert_instance.alert_name}") 
