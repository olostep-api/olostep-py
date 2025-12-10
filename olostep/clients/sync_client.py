"""
Synchronous facade over the async Olostep client.

Runs async methods in an event loop and exposes the same dot-notation namespaces.
Use this when you need synchronous access to the Olostep API.

The sync client supports two usage patterns:

1. **Direct Usage (Recommended for one-off calls):**
   No explicit resource management needed since each operation creates
   a new async client internally.

   ```python
   client = SyncOlostepClient(api_key="your-api-key")
   result = client.scrape.url(
       url_to_scrape="https://example.com",
       formats=["html", "markdown"]
   )
   # No explicit close needed
   ```

2. **Explicit Close (For long-lived services):**
   Call close() for consistency, though currently a no-op.

   ```python
   client = SyncOlostepClient(api_key="your-api-key")
   try:
       result = client.scrape.url(
           url_to_scrape="https://example.com",
           formats=["html", "markdown"]
       )
   finally:
       client.close()  # For future compatibility
   ```

For most use cases, the direct usage pattern is sufficient since each
operation is self-contained and resources are cleaned up automatically.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable

from .async_client import OlostepClient


class _SyncProxy:
    def __init__(self, outer: "SyncOlostepClient", resolver: Callable[[OlostepClient], Any], dir_list: list[str] | None = None) -> None:
        self._outer = outer
        self._resolver = resolver
        self._dir_list = dir_list or []

    def __getattr__(self, name: str) -> "_SyncProxy":
        return _SyncProxy(self._outer, lambda c: getattr(self._resolver(c), name))

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._outer._call(lambda c: self._resolver(c)(*args, **kwargs))

    def __dir__(self) -> list[str]:
        return self._dir_list


class SyncOlostepClient:
    def __init__(
        self, 
        api_key: str | None = None, 
        base_url: str | None = None,
        *,
        transport: Any = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._transport = transport
        # Proxies mirroring async namespaces
        self.scrape = _SyncProxy(self, lambda c: c.scrape, dir_list=["url", "get"])
        self.batch = _SyncProxy(self, lambda c: c.batch, dir_list=["start", "info", "items"])
        self.crawl = _SyncProxy(self, lambda c: c.crawl, dir_list=["start", "info", "pages"])
        self.sitemap = _SyncProxy(self, lambda c: c.sitemap, dir_list=["create"])
        self.retrieve = _SyncProxy(self, lambda c: c.retrieve, dir_list=["get"])

    def __dir__(self) -> list[str]:
        return ["scrape", "batch", "crawl", "sitemap", "retrieve"]

    def close(self) -> None:
        """
        Close any shared resources used by the sync client.

        Currently a no-op since each operation creates a new async client,
        but provided for future compatibility if connection pooling or caching
        is implemented.

        For one-off usage, no explicit close is needed:

            client = SyncOlostepClient(api_key="...")
            result = client.scrape.url("https://example.com")

        For long-lived services where you want to ensure cleanup:

            client = SyncOlostepClient(api_key="...")
            try:
                result = client.scrape.url("https://example.com")
            finally:
                client.close()
        """
        pass

    def _run(self, coro: Any) -> Any:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        else:
            # Already in an event loop: run in a worker thread
            import threading
            result: dict[str, Any] = {}

            def _runner() -> None:
                result["value"] = asyncio.run(coro)

            t = threading.Thread(target=_runner, daemon=True)
            t.start()
            t.join()
            return result["value"]

    def _call(self, func: Callable[[OlostepClient], Any]) -> Any:
        async def _inner():
            async with OlostepClient(
                api_key=self._api_key, 
                base_url=self._base_url,
                transport=self._transport,
            ) as c:
                return await func(c)
        return self._run(_inner()) 