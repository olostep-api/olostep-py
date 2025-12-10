from __future__ import annotations

from typing import Any

from ..backend.transport import HttpxTransport
from ..backend.transport_protocol import Transport
from ..backend.caller import EndpointCaller
from ..frontend.scrape_menu import ScrapeMenu
from ..frontend.batch_menu import BatchMenu
from ..frontend.crawl_menu import CrawlMenu
from ..frontend.sitemap_menu import SitemapMenu
from ..frontend.retrieve_menu import RetrieveMenu
from ..frontend.answers_menu import AnswersMenu
from ..config import BASE_API_URL, API_KEY_ENV


class OlostepClient:
    """
    Default async client that wires the transport, caller, and namespaced frontend.
    This is the main client for the Olostep SDK.

    The client supports two usage patterns:

    1. **Context Manager (Recommended for one-off usage):**
       Automatically handles resource cleanup when exiting the context.

       ```python
       async with OlostepClient(api_key="your-api-key") as client:
           result = await client.scrape.url(
               url_to_scrape="https://example.com",
               formats=["html", "markdown"]
           )
       # Transport is automatically closed here
       ```

    2. **Explicit Close (For long-lived services):**
       Requires manual resource cleanup using the close() method.

       ```python
       client = OlostepClient(api_key="your-api-key")
       try:
           result = await client.scrape.url(
               url_to_scrape="https://example.com",
               formats=["html", "markdown"]
           )
       finally:
           await client.close()  # Manually close the transport
       ```

    For most use cases, prefer the context manager pattern as it ensures
    proper resource cleanup and is less error-prone.
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
        self._transport: Transport = transport or HttpxTransport(self._api_key)
        self._caller = EndpointCaller(self._transport, self._base_url, self._api_key)

        # Menu items
        self.scrape = ScrapeMenu(self._caller)
        self.batch = BatchMenu(self._caller)
        self.crawl = CrawlMenu(self._caller)
        self.sitemap = SitemapMenu(self._caller)
        self.retrieve = RetrieveMenu(self._caller)
        self.answers = AnswersMenu(self._caller)


    async def __aenter__(self) -> "OlostepClient":
        return self

    async def close(self) -> None:
        """
        Close the underlying transport connection.

        This method closes the HTTP transport and releases associated resources.
        Only needed if not using the client as an async context manager.

        For one-off usage, prefer the context manager pattern:

            async with OlostepClient(api_key="...") as client:
                result = await client.scrape.url("https://example.com")

        For long-lived services, use explicit close:

            client = OlostepClient(api_key="...")
            try:
                result = await client.scrape.url("https://example.com")
            finally:
                await client.close()
        """
        await self._transport.close()

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        await self.close()
