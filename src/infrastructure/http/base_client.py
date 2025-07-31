# cython: language_level=3
import requests
from typing import Optional, Dict, Any, Union


class APIError(Exception):
    """Base exception for API-related errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Any] = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class RequestError(APIError):
    """Exception raised for errors in the request"""
    pass


class ResponseError(APIError):
    """Exception raised for errors in the response"""
    pass


class BaseAPIClient:
    """Base API client for making HTTP requests"""

    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.timeout = timeout

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def request(self, method: str, endpoint: str, timeout: int, **kwargs) -> requests.Response:
        url = self._build_url(endpoint)
        request_headers = {**self.headers, **kwargs.pop('headers', {})}
        # if timeout is not None override the default timeout
        if timeout is None:
            timeout = self.timeout

        try:
            response = requests.request(
                method,
                url,
                headers=request_headers,
                timeout=timeout,
                **kwargs
            )

            # Raise an exception for error status codes
            response.raise_for_status()

            return response

        except requests.exceptions.RequestException as e:
            # Handle request errors (network issues, timeouts, etc.)
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            raise RequestError(f"Error making request: {str(e)}", status_code=status_code)

        except ValueError as e:
            # Handle JSON parsing errors
            raise ResponseError(f"Invalid JSON response: {str(e)}")
