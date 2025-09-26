"""Transport protocol definition for the Olostep SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class RawAPIRequest:
    """Raw API request containing method, url, query, json, and headers."""
    method: str
    url: str
    query: dict[str, Any] | None
    json: dict[str, Any] | None
    headers: dict[str, str] | None

@dataclass
class RawAPIResponse:
    """Raw API response containing status code, headers, and response text."""
    status_code: int
    headers: dict[str, str]
    body: str


class Transport(Protocol):
    """Protocol defining the interface for HTTP transport implementations."""
    
    async def request(
        self,
        request: RawAPIRequest,
    ) -> RawAPIResponse:
        """
        Make an HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL (with path and query parameters)
            json: JSON payload for request body
            headers: Additional headers
            
        Returns:
            RawAPIResponse containing status_code, headers, and response_text
        """
        ...
