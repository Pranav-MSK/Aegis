import time
import json
import requests
from typing import Dict, Any

from src.clients.http_client.client import HttpClient

alertmanager_api_client = HttpClient("alertmanager")

def send_test_alert(alert_name, severity, instance):
    # Generate a unique alert name by appending the current timestamp
    unique_alert_name = f"{alert_name}_{int(time.time())}"

    # Create a detailed description for the alert
    description = """If you see this alert, it means that the Alertmanager is functioning correctly. """
    
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
        response = alertmanager_api_client.post(
            endpoint="/api/v2/alerts",
            data=alert_data,
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
