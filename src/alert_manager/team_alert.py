# cython: language_level=3
import requests
import json
from src.helper.logger import get_logger

logger = get_logger(__name__)


def send_teams_alert(webhook_url, alert_instance):
    """
    Sends a Prometheus alert to a Microsoft Teams channel using a webhook.

    Parameters:
    webhook_url (str): The webhook URL of the Teams channel.
    alert_name (str): The name of the alert (e.g., CPU usage high).
    instance (str): The instance where the alert occurred (e.g., the hostname or IP).
    severity (str): The severity level of the alert (e.g., critical, warning).
    description (str): Detailed description of the alert.
    summary (str): A brief summary of the alert (default is 'Prometheus Alert').
    """

    # Define the message payload
    message_payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": alert_instance.summary,
        "themeColor": "FF0000" if alert_instance.severity.lower() == "critical" else "FFD700",  # Red for critical, Yellow for others
        "sections": [{
            "activityTitle": f"**Alert: {alert_instance.alert_name}**",
            "facts": [
                {"name": "Instance:", "value": alert_instance.instance},
                {"name": "Severity:", "value": alert_instance.severity},
                {"name": "Description:", "value": alert_instance.description}
            ],
            "text": alert_instance.description,
            "markdown": True
        }]
    }

    # Send the POST request to the webhook URL
    response = requests.post(
        webhook_url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(message_payload),
        timeout=10
    )

    # Check if the request was successful
    if response.status_code == 200:
        logger.info(f"Alert sent successfully to Microsoft Teams!")
    else:
        logger.error(f"Failed to send alert. Status code: {response.status_code}")
        logger.error(f"Response: {response.text}")
