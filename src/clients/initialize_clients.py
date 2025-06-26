"""
Centralized API client registration module.
This module registers all API clients used by the application.
"""
from src.clients.api_registry import APIClientRegistry

# Register all clients at module import time
def register_all_clients():
    """Register all API clients used in the application."""
    PROMETHEUS_BASE_URL = "http://localhost:9090"

    APIClientRegistry.register_client(
        api_name="prometheus",
        base_url=PROMETHEUS_BASE_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )
