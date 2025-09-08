from __future__ import annotations

from typing import Any

from ..backend.transport import AiohttpTransport, Transport
from ..backend.caller import EndpointCaller
from ..frontend.typed_dict.sdk import TypedDictFrontend
from ..config import BASE_API_URL, API_KEY_ENV


class AsyncOlostepClient:
    """
    Thin async client that wires the transport, caller, and namespaced frontend.

    Usage:
        async with AsyncOlostepClient(api_key=...) as c:
            res = await c.scrape.url(url_to_scrape="https://example.com", formats=[...])
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        transport: Transport | None = None,
    ) -> None:
        self._api_key: str = (api_key or API_KEY_ENV or "").strip()
        self._base_url: str = (base_url or BASE_API_URL).rstrip("/")
        # Allow custom transport for tests (e.g., FakeTransportSmart). If not provided, use real HTTP.
        if transport is None and not self._api_key:
            raise ValueError("API key is required when using the real HTTP transport")
        self._transport: Transport = transport or AiohttpTransport(self._api_key)
        self._caller = EndpointCaller(self._transport, self._base_url, self._api_key)
        self._ui = TypedDictFrontend(self._caller)

        # Expose namespaces directly
        self.scrape = self._ui.scrape
        self.batch = self._ui.batch
        self.crawl = self._ui.crawl
        self.map = self._ui.map
        self.retrieve = self._ui.retrieve

    async def close(self) -> None:
        closer = getattr(self._transport, "close", None)
        if callable(closer):
            await closer()  # type: ignore[misc]

    async def __aenter__(self) -> "AsyncOlostepClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        await self.close()
