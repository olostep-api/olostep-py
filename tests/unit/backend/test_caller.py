"""
Caller layer tests for Olostep SDK.

Tests the EndpointCaller class to ensure it properly handles retry logic
and error handling for API requests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from olostep.backend.api_endpoints import EndpointContract
from olostep.backend.caller import EndpointCaller
from olostep.backend.transport_protocol import RawAPIRequest, RawAPIResponse
from olostep.errors import Olostep_APIConnectionError
from olostep.retry_strategy import RetryStrategy


@pytest.mark.unit
class TestEndpointCallerRetryLogic:
    """Test retry logic with exponential backoff for connection errors."""

    @pytest.fixture
    def mock_transport(self) -> AsyncMock:
        """Create mock transport for testing."""
        transport = AsyncMock()
        # max_duration is a synchronous method, not async
        transport.max_duration = MagicMock(return_value=0.0)
        return transport

    @pytest.fixture
    def caller(self, mock_transport: AsyncMock) -> EndpointCaller:
        """Create caller instance with mock transport."""
        return EndpointCaller(
            transport=mock_transport, 
            base_url="https://api.test.com", 
            api_key="test_key",
            retry_strategy=RetryStrategy(max_retries=3)
        )
    

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

        # Create a simple contract for testing
        class TestResponse(BaseModel):
            success: bool
        
        contract = EndpointContract(
            key=("test", "endpoint"),
            name="Test Endpoint",
            description="Test endpoint for unit testing",
            method="GET",
            path="/test",
            response_model=TestResponse
        )

        result = await caller._invoke(contract)

        assert isinstance(result, TestResponse)
        assert result.success is True
        # Verify transport.request was called with a RawAPIRequest
        assert mock_transport.request.called
        call_args = mock_transport.request.call_args[0][0]
        assert isinstance(call_args, RawAPIRequest)
        assert call_args.method == "GET"
        assert call_args.url == "https://api.test.com/test"

    @pytest.mark.asyncio
    async def test_connection_error_propagated(
        self, caller: EndpointCaller, mock_transport: AsyncMock
    ) -> None:
        """Test that connection errors are propagated from transport."""
        mock_transport.request.side_effect = Olostep_APIConnectionError()

        # Create a simple contract for testing
        contract = EndpointContract(
            key=("test", "endpoint"),
            name="Test Endpoint",
            description="Test endpoint for unit testing",
            method="GET",
            path="/test",
            response_model=None
        )

        with pytest.raises(Olostep_APIConnectionError):
            await caller._invoke(contract)

        mock_transport.request.assert_called_once()