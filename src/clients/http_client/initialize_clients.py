"""
Centralized API client registration module.
This module registers all API clients used by the application.
"""
from src.clients.http_client.api_registry import APIClientRegistry
from src.config.config_loader import configuration_settings

METADATA_URL = configuration_settings.get("aws.metadata", "METADATA_URL")
PROMETHEUS_BASE_URL = configuration_settings.get("monitoring.prometheus", "BASE_URL", fallback="http://localhost:9090")
ALERTMANAGER_BASE_URL = configuration_settings.get("monitoring.alertmanager", "BASE_URL", fallback="http://localhost:9093")

# Register all clients at module import time
def register_all_clients():
    """Register all API clients used in the application."""
    APIClientRegistry.register_client(
        api_name="prometheus",
        base_url=PROMETHEUS_BASE_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )

    #METADATA_URL = configuration_settings.get("aws.metadata", "METADATA_URL")
    APIClientRegistry.register_client(
        api_name="aws_metadata",
        base_url=METADATA_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )

    # http://localhost:9093
    APIClientRegistry.register_client(
        api_name="alertmanager",
        base_url=ALERTMANAGER_BASE_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )
