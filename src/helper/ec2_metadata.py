# cython: language_level=3
import requests

from functools import lru_cache

from src.helper.logger import get_logger
from src.config.config_loader import configuration_settings
from src.clients.http_client.client import HttpClient

logger = get_logger(__name__)

CACHE_EXPIRATION = configuration_settings.getint("metrics.settings", "CACHE_EXPIRATION")
DIVIDE_BY_1024 = configuration_settings.getboolean("metrics.settings", "DIVIDE_BY_1024")
METADATA_URL = configuration_settings.get("aws.metadata", "METADATA_URL")
TOKEN_TTL_SECONDS = configuration_settings.getint("aws.metadata", "TOKEN_TTL_SECONDS", fallback=21600)  # Default to 6 hours
TOKEN_URL = configuration_settings.get("aws.metadata", "TOKEN_URL")

CONVERSION_FACTOR_MB = 1024**2 if DIVIDE_BY_1024 else 1000**2
CONVERSION_FACTOR_GB = 1024**3 if DIVIDE_BY_1024 else 1000**3

aws_client =  HttpClient("aws_metadata")

@lru_cache(maxsize=1)
def get_instance_metadata():
    """
    Retrieve all available metadata about the current EC2 instance.

    Returns:
        dict: A dictionary containing all instance metadata.
    """
    metadata = {}

    try:
        logger.info("Fetching instance metadata")
        # Get a session token for IMDSv2
        token_response = requests.put(
            TOKEN_URL,
            headers={
                "X-aws-ec2-metadata-token-ttl-seconds": str(TOKEN_TTL_SECONDS)
            },  # Token valid for 6 hours
        )
        token_response.raise_for_status()
        token = token_response.text

        # Get all metadata categories
        response = requests.get(METADATA_URL, headers={"X-aws-ec2-metadata-token": token})
        response.raise_for_status()  # Raise an error for bad responses

        # List all metadata keys
        keys = response.text.splitlines()

        for key in keys:
            # Fetch each piece of metadata
            full_url = f"{METADATA_URL}{key}"
            value_response = requests.get(
                full_url, headers={"X-aws-ec2-metadata-token": token}
            )
            metadata[key] = value_response.text

        return metadata

    except requests.RequestException as e:
        print(f"Error fetching instance metadata: {e}")
        return {}


