import requests
from typing import Dict, Any, Optional, Union

from src.clients.http_client.api_registry import APIClientRegistry
from src.clients.http_client.request_strategies import GetRequest, PostRequest, PutRequest, DeleteRequest
from src.clients.http_client.base_client import RequestError, ResponseError


class HttpClient:
    """High-level API client for making requests using strategy pattern"""
    
    def __init__(self, api_name: str):
        self.api_name = api_name
        self.client = APIClientRegistry.get_client(api_name)
        self._get_strategy = GetRequest()
        self._post_strategy = PostRequest()
        self._put_strategy = PutRequest()
        self._delete_strategy = DeleteRequest()
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30, **kwargs) -> requests.Response:
        try:
            return self._get_strategy.execute(self.client, endpoint, params=params, timeout=timeout, **kwargs)
        except (RequestError, ResponseError) as e:
            raise
    
    def post(self, endpoint: str, data: Optional[list[dict[str, Any]]] = None, timeout: int = 30, **kwargs) -> requests.Response:
        try:
            return self._post_strategy.execute(self.client, endpoint, data=data, timeout=timeout, **kwargs)
        except (RequestError, ResponseError) as e:
            raise
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, timeout: int = 30, **kwargs) -> requests.Response:
        try:
            return self._put_strategy.execute(self.client, endpoint, data=data, timeout=timeout, **kwargs)
        except (RequestError, ResponseError) as e:
            raise
    
    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30, **kwargs) -> requests.Response:
        try:
            return self._delete_strategy.execute(self.client, endpoint, params=params, timeout=timeout, **kwargs)
        except (RequestError, ResponseError) as e:
            raise
