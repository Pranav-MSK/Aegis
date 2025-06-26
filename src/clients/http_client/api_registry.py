from typing import Dict, Optional
from src.clients.http_client.base_client import BaseAPIClient


class APIClientRegistry:
    """Registry for managing API clients"""
    
    _clients: Dict[str, BaseAPIClient] = {}

    @classmethod
    def register_client(cls, api_name: str, base_url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> BaseAPIClient:
        if api_name in cls._clients:
            return cls._clients[api_name]
        
        client = BaseAPIClient(base_url=base_url, headers=headers, timeout=timeout)
        cls._clients[api_name] = client
        return client

    @classmethod
    def get_client(cls, api_name: str) -> BaseAPIClient:
        if api_name not in cls._clients:
            raise ValueError(f"Client '{api_name}' is not registered.")
        
        return cls._clients[api_name]
    
    @classmethod
    def remove_client(cls, api_name: str) -> None:
        if api_name not in cls._clients:
            raise ValueError(f"Client '{api_name}' is not registered.")
        
        del cls._clients[api_name]
