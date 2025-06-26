from abc import ABC, abstractmethod

from src.infrastructure.http.base_client import BaseAPIClient


class RequestStrategy(ABC):
    """ Abstract base class for request strategies. """
    @abstractmethod
    def execute(self, client: BaseAPIClient, endpoint: str, timeout: int, **kwargs):
        raise NotImplementedError("Subclasses must implement this method.")


class GetRequest(RequestStrategy):
    """ Strategy for GET requests. """
    def execute(self, client: BaseAPIClient, endpoint: str, timeout: int, **kwargs):
        return client.request("GET", endpoint, timeout, params=kwargs.get('params'))


class PostRequest(RequestStrategy):
    """ Strategy for POST requests. """
    def execute(self, client: BaseAPIClient, endpoint: str, timeout: int, **kwargs):
        return client.request("POST", endpoint, timeout, json=kwargs.get('data'))


class PutRequest(RequestStrategy):
    """ Strategy for PUT requests. """
    def execute(self, client: BaseAPIClient, endpoint: str, timeout: int, **kwargs):
        return client.request("PUT", endpoint, timeout, son=kwargs.get('data'))
    

class DeleteRequest(RequestStrategy):
    """ Strategy for DELETE requests. """
    def execute(self, client: BaseAPIClient, endpoint: str, timeout: int, **kwargs):
        return client.request("DELETE", endpoint, timeout, params=kwargs.get('params'))
