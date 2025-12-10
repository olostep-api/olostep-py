"""
Synchronous facade over the async Olostep client.

This module provides a synchronous interface to the asynchronous Olostep API client.
It uses the proxy pattern to expose the same dot-notation API as the async client,
but runs all operations in an event loop behind the scenes.

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

PROXY PATTERN EXPLANATION:
=======================

The sync client uses a sophisticated proxy pattern to provide the same API
as the async client:

1. **SyncOlostepClient** - Main sync client class that creates proxy objects
2. **_SyncProxy** - Proxy class that forwards method calls to async client
3. **Event Loop Management** - Automatically handles async/sync conversion

Example of how it works:
- User calls: `client.scrape.url("example.com")`
- `client.scrape` returns a `_SyncProxy` instance
- `client.scrape.url` returns another `_SyncProxy` instance with method docstring
- `client.scrape.url(...)` executes the async method in an event loop
- User gets result synchronously without knowing about async internals
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable

from .async_client import OlostepClient
from ..frontend.scrape_menu import ScrapeMenu
from ..frontend.batch_menu import BatchMenu
from ..frontend.crawl_menu import CrawlMenu
from ..frontend.sitemap_menu import SitemapMenu
from ..frontend.retrieve_menu import RetrieveMenu
from ..frontend.answers_menu import AnswersMenu


class _SyncProxy:
    """
    Proxy class that provides synchronous access to async client methods.

    This class is the core of the proxy pattern implementation. It allows users
    to call async methods using synchronous syntax by automatically handling
    the event loop execution behind the scenes.

    Key Features:
    - Docstring inheritance from async methods
    - Dynamic method resolution
    - Event loop management
    - Transparent async-to-sync conversion

    The proxy works in three phases:
    1. Attribute Access: `client.scrape` → Returns _SyncProxy for scrape endpoint
    2. Method Access: `client.scrape.url` → Returns _SyncProxy with method docstring
    3. Method Call: `client.scrape.url(...)` → Executes async method synchronously
    """

    # Class-level mapping of endpoint names to async classes for docstring inheritance
    # This eliminates code duplication and provides a single source of truth
    # for which async class corresponds to each sync endpoint
    _CLASS_MAP = {
        "scrape": ScrapeMenu,    # Maps to ScrapeMenu async class
        "batch": BatchMenu,      # Maps to BatchMenu async class
        "crawl": CrawlMenu,      # Maps to CrawlMenu async class
        "sitemap": SitemapMenu,  # Maps to SitemapMenu async class
        "retrieve": RetrieveMenu, # Maps to RetrieveMenu async class
        "answers": AnswersMenu,   # Maps to AnswersMenu async class
    }


    def __init__(self, outer: "SyncOlostepClient", endpoint_name: str) -> None:
        """
        Initialize a sync proxy for a specific endpoint.

        The proxy introspects the corresponding async class to determine which
        methods are available and copies docstrings automatically.

        Args:
            outer: Reference back to the main SyncOlostepClient instance
                   Used for accessing API credentials and transport settings
            endpoint_name: Name of the endpoint this proxy represents
                          (e.g., "scrape", "batch", "answers")
        """
        self._outer = outer
        self._endpoint_name = endpoint_name

        # STEP 1: Copy docstring and class identity from the async method class
        # This ensures sync methods have the same comprehensive documentation
        # and appear to be the actual async class when inspected with type() or __class__
        # For example: type(client.scrape).__name__ returns "ScrapeMenu" instead of "_SyncProxy"
        async_class = self._CLASS_MAP.get(self._endpoint_name)
        if async_class:
            # Copy docstring
            if hasattr(async_class, '__doc__') and async_class.__doc__:
                self.__doc__ = async_class.__doc__
            # Store the async class for identity purposes
            self._async_class = async_class

            # STEP 1.5: Introspect the actual async class for public methods
            # Get all public methods (not starting with _) from the async class
            # This ensures we only expose methods that actually exist on the async class
            self._public_methods = [
                name for name in dir(async_class)
                if not name.startswith('_') and callable(getattr(async_class, name, None))
            ]

    def __getattr__(self, name: str) -> "_SyncProxy":
        """
        Handle attribute access on the proxy (e.g., client.scrape.url).

        This method is called when user accesses a method on the endpoint proxy.
        It only allows access to methods that were introspected from the async class,
        preventing exposure of internal Python methods or non-existent methods.

        Args:
            name: Name of the method being accessed (e.g., "url", "create", "get")

        Returns:
            New _SyncProxy instance representing the specific method with inherited docstring

        Raises:
            AttributeError: If the method doesn't exist on the async class
        """
        # Only allow access to methods that actually exist on the async class
        if name not in self._public_methods:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # STEP 2: Create a new proxy for the specific method
        # This maintains the same API structure as the async client
        new_proxy = _SyncProxy(self._outer, self._endpoint_name)

        # STEP 3: Copy method-specific docstring and maintain class identity from async implementation
        # This ensures methods like `client.scrape.url.__doc__` show the correct documentation
        # and `type(client.scrape.url).__name__` returns "ScrapeMenu" instead of "_SyncProxy"
        # All proxies for the same endpoint share the same class identity
        try:
            async_class = self._CLASS_MAP.get(self._endpoint_name)
            if async_class:
                # Store the async class for identity purposes (all proxies share same class)
                new_proxy._async_class = async_class

                # Copy the same public methods list so all proxies have consistent method access
                if hasattr(self, '_public_methods'):
                    new_proxy._public_methods = self._public_methods

                async_method = getattr(async_class, name, None)
                if async_method and hasattr(async_method, '__doc__') and async_method.__doc__:
                    new_proxy.__doc__ = async_method.__doc__
        except Exception:
            pass  # Silently fail if we can't get the docstring or class

        return new_proxy

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Handle method invocation on the proxy (e.g., client.scrape.url(...)).

        This is where the magic happens! When the user calls a method on the proxy,
        this method intercepts the call and executes the corresponding async method
        synchronously using an event loop.

        The execution flow:
        1. Create a resolver function that gets the async method
        2. Pass it to _outer._call() which handles the async execution
        3. Return the result synchronously to the user

        Args:
            *args: Positional arguments to pass to the async method
            **kwargs: Keyword arguments to pass to the async method

        Returns:
            Result of the async method execution (synchronous)
        """
        # STEP 4: Create a resolver function dynamically based on the endpoint name
        # This function will be called with an async client instance and will
        # return the appropriate async method (e.g., c.scrape, c.batch, c.answers)
        def resolver(c):
            return getattr(c, self._endpoint_name)

        # STEP 5: Execute the async method synchronously
        # The _outer._call() method handles all the event loop complexity
        # and returns the result as if it were a normal synchronous call
        return self._outer._call(lambda c: resolver(c)(*args, **kwargs))

    def __dir__(self) -> list[str]:
        """
        Control what methods are shown by IDE autocomplete and dir().

        Returns the public methods that were introspected from the async class.
        This ensures that only the valid methods for this endpoint are
        suggested by IDEs and shown in help systems. Methods are automatically
        discovered by inspecting the corresponding async class.

        Returns:
            List of available method names for this endpoint
        """
        return self._public_methods

    @property
    def __class__(self):
        """
        Override __class__ to return the async class identity.

        This makes isinstance(client.scrape, ScrapeMenu) return True,
        while maintaining all proxy functionality.

        Returns:
            The async class that this proxy represents
        """
        return self._async_class if hasattr(self, '_async_class') else _SyncProxy

    def __repr__(self) -> str:
        """
        Return a string representation that shows the actual async class name.

        This makes repr(client.scrape) show "ScrapeMenu" instead of "_SyncProxy",
        which is more intuitive for users.

        Returns:
            String representation using the async class name
        """
        if hasattr(self, '_async_class'):
            return f"{self._async_class.__name__}[SyncProxy]()"
        return "_SyncProxy()"


class SyncOlostepClient:
    """
    Main synchronous client class that provides the same API as the async client.

    This class creates proxy objects for each endpoint (scrape, batch, crawl, etc.)
    that forward method calls to their async counterparts. The proxies handle
    all the complexity of running async code in event loops transparently.

    Architecture:
    - Each endpoint (scrape, batch, etc.) gets a _SyncProxy instance
    - Proxies inherit docstrings from async classes automatically
    - Method calls are forwarded to async client and executed synchronously
    - Event loop management is handled automatically

    Example:
        client = SyncOlostepClient(api_key="...")
        # client.scrape returns _SyncProxy with ScrapeMenu docstring
        # client.scrape.url returns _SyncProxy with ScrapeMenu.url docstring
        # client.scrape.url(...) executes async method and returns result
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        transport: Any = None,
    ) -> None:
        """
        Initialize the synchronous client.

        Args:
            api_key: API key for authentication (required for real API calls)
            base_url: Base URL for the API (optional, defaults to production)
            transport: Custom transport layer (optional, for testing)
        """
        self._api_key = api_key
        self._base_url = base_url
        self._transport = transport

        # No need for async client - we get docstrings from class definitions directly

        # STEP 6: Create proxies for each endpoint namespace
        # These proxies provide the same dot-notation API as the async client
        # but execute methods synchronously using event loops. Methods are introspected
        # from the actual async classes automatically.
        self.scrape = _SyncProxy(self, "scrape")
        self.batch = _SyncProxy(self, "batch")
        self.crawl = _SyncProxy(self, "crawl")
        self.sitemap = _SyncProxy(self, "sitemap")
        self.retrieve = _SyncProxy(self, "retrieve")
        self.answers = _SyncProxy(self, "answers")

    def __dir__(self) -> list[str]:
        """
        Control what attributes are shown by IDE autocomplete and dir().

        This ensures users see the same endpoint names as the async client.

        Returns:
            List of available endpoint namespaces
        """
        return ["scrape", "batch", "crawl", "sitemap", "retrieve", "answers"]

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
        """
        Execute a coroutine synchronously, handling different event loop contexts.

        This method intelligently handles async execution in various scenarios:
        - If no event loop is running: Creates new loop with asyncio.run()
        - If already in an event loop: Runs in background thread to avoid blocking

        Args:
            coro: The coroutine to execute synchronously

        Returns:
            Result of the coroutine execution
        """
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running - safe to use asyncio.run()
            return asyncio.run(coro)
        else:
            # Already in an event loop - must use threading to avoid blocking
            import threading
            result: dict[str, Any] = {}

            def _runner() -> None:
                """Run the coroutine in a separate event loop thread."""
                result["value"] = asyncio.run(coro)

            # Create and start daemon thread for async execution
            t = threading.Thread(target=_runner, daemon=True)
            t.start()
            t.join()  # Wait for completion
            return result["value"]

    def _call(self, func: Callable[[OlostepClient], Any]) -> Any:
        """
        Execute an async client function synchronously.

        This is the main entry point for all sync client operations. It:
        1. Creates a temporary async client with the provided credentials
        2. Executes the function within an async context manager
        3. Returns the result synchronously

        Args:
            func: Function that takes an async client and returns a coroutine

        Returns:
            Result of the async function execution (synchronous)
        """
        # STEP 7: Create the async function that will be executed
        async def _inner():
            # Use async context manager to ensure proper resource cleanup
            async with OlostepClient(
                api_key=self._api_key,
                base_url=self._base_url,
                transport=self._transport,
            ) as c:
                return await func(c)

        # STEP 8: Execute the async function synchronously
        return self._run(_inner())


# =============================================================================
# PROXY PATTERN SUMMARY
# =============================================================================
#
# COMPLETE EXECUTION FLOW:
# ======================
#
# 1. User creates sync client: `client = SyncOlostepClient(api_key="...")`
# 2. User accesses endpoint: `client.scrape` → Returns _SyncProxy with ScrapeMenu docstring
# 3. User accesses method: `client.scrape.url` → Returns _SyncProxy with url() docstring
# 4. User calls method: `client.scrape.url("example.com")` → Executes async method
# 5. _SyncProxy.__call__() creates resolver function: `lambda c: c.scrape`
# 6. _call() creates async context: `async with OlostepClient(...) as c:`
# 7. _run() executes coroutine: Creates/manages event loop as needed
# 8. Result returned synchronously: User gets result without knowing about async
#
# KEY BENEFITS:
# ============
# - **Transparent:** Users write sync code, async happens automatically
# - **Consistent:** Same API as async client with identical documentation
# - **Thread-safe:** Handles nested event loops correctly
# - **Resource-managed:** Proper cleanup via async context managers
# - **IDE-friendly:** Full autocomplete and type hints
#
# The proxy pattern successfully bridges the gap between sync and async APIs
# while maintaining the full feature set and developer experience of both! 