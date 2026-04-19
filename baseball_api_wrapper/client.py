"""
MLB Stats API Client
====================
A Python wrapper for the official MLB Stats API (https://statsapi.mlb.com).

This module provides a low-level HTTP client that handles request construction,
error handling, and response parsing for the MLB Stats API.
"""

import requests
from typing import Any, Dict, Optional


class MLBStatsAPIError(Exception):
    """Raised when the MLB Stats API returns an error response."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"MLB Stats API error {status_code}: {message}")


class MLBStatsClient:
    """
    Low-level HTTP client for the MLB Stats API.

    Handles base URL configuration, session management, and common
    request/response logic. Higher-level endpoint wrappers build on
    top of this class.

    Args:
        base_url: The root URL of the Stats API. Defaults to the
                  official production endpoint.
        timeout:  Request timeout in seconds. Defaults to 10.

    Example::

        client = MLBStatsClient()
        data = client.get("/api/v1/teams", params={"season": "2024", "sportId": 1})
    """

    DEFAULT_BASE_URL = "https://statsapi.mlb.com"

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a GET request against the Stats API.

        Args:
            path:   API path, e.g. ``"/api/v1/teams"``.
            params: Optional dictionary of query-string parameters.

        Returns:
            Parsed JSON response as a Python dictionary.

        Raises:
            MLBStatsAPIError: If the server returns a non-2xx status code.
            requests.RequestException: On network-level failures.
        """
        url = f"{self.base_url}{path}"
        response = self._session.get(url, params=params, timeout=self.timeout)

        if not response.ok:
            raise MLBStatsAPIError(response.status_code, response.text)

        return response.json()

    def close(self):
        """Close the underlying HTTP session, freeing connection-pool resources."""
        self._session.close()

    # Support use as a context manager
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
