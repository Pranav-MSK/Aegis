import time
import json
import requests
from typing import Dict, Any

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
            timeout=10,
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
