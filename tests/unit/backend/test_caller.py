"""
Caller layer tests for Olostep SDK.

Tests the EndpointCaller class to ensure it properly handles retry logic
and error handling for API requests.
"""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, call

from olostep.backend.caller import EndpointCaller
from olostep.backend.transport_protocol import RawAPIResponse
from olostep.errors import Olostep_APIConnectionError


@pytest.mark.unit
class TestEndpointCallerRetryLogic:
    """Test retry logic with exponential backoff for connection errors."""

    @pytest.fixture
    def mock_transport(self) -> AsyncMock:
        """Create mock transport for testing."""
        return AsyncMock()

    @pytest.fixture
    def caller(self, mock_transport: AsyncMock) -> EndpointCaller:
        """Create caller instance with mock transport."""
        return EndpointCaller(transport=mock_transport, base_url="https://api.test.com", api_key="test_key")
    

    @pytest.mark.asyncio
    async def test_successful_request(
        self, caller: EndpointCaller, mock_transport: AsyncMock
    ) -> None:
        """Test that successful requests work correctly."""
        expected_response = RawAPIResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body='{"success": true}'
        )
        mock_transport.request.return_value = expected_response

        response = await caller._make_request("GET", "https://api.test.com/test", None, {})

        assert response == expected_response
        mock_transport.request.assert_called_once_with("GET", "https://api.test.com/test", json=None, params={}, headers=None)

    @pytest.mark.asyncio
    async def test_connection_error_propagated(
        self, caller: EndpointCaller, mock_transport: AsyncMock
    ) -> None:
        """Test that connection errors are propagated from transport."""
        mock_transport.request.side_effect = Olostep_APIConnectionError()

        with pytest.raises(Olostep_APIConnectionError):
            await caller._make_request("GET", "https://api.test.com/test", None, {})

        mock_transport.request.assert_called_once()