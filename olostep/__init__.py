# Core clients
from .clients.async_client import OlostepClient
from .clients.sync_client import SyncOlostepClient

# Configuration
from .retry_strategy import RetryStrategy

# Stateful result objects
from .frontend.client_state import ScrapeResult, BatchItemResult, CrawlPage, Crawl, CrawlInfo, Sitemap

# Type system
from .models.request import (
    Format,
    Country,
    RetrieveFormat,
    WaitAction,
    ClickAction,
    FillInputAction,
    ScrollAction,
    Parser,
    LLMExtract,
    LinksOnPage,
    ScreenSize,
    Transformer,
)

# Error hierarchy
from . import errors

__version__ = "0.10.0"

# Get all error classes dynamically
_error_classes = [name for name in dir(errors) if not name.startswith('_') and name.endswith('Error')]

__all__ = [
    # Clients
    "OlostepClient",
    "SyncOlostepClient",
    # Configuration
    "RetryStrategy",
    # Result objects
    "ScrapeResult",
    "BatchItemResult",
    "CrawlPage",
    "Crawl",
    "CrawlInfo",
    "Sitemap",
    # Types
    "Format",
    "Country",
    "RetrieveFormat",
    "WaitAction",
    "ClickAction",
    "FillInputAction",
    "ScrollAction",
    "Parser",
    "LLMExtract",
    "LinksOnPage",
    "ScreenSize",
    "Transformer",
    # Error classes
    *_error_classes,
    # Version
    "__version__",
]