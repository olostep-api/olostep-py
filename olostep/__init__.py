# Core clients
# Error hierarchy
from . import errors
from .clients.async_client import OlostepClient
from .clients.sync_client import SyncOlostepClient
from .config import VERSION as __version__

# Stateful result objects
from .frontend.client_state import (
    BatchItemResult,
    Crawl,
    CrawlInfo,
    CrawlPage,
    ScrapeResult,
    Sitemap,
)

# Type system
from .models.request import (
    ClickAction,
    Country,
    FillInputAction,
    Format,
    LinksOnPage,
    LLMExtract,
    Parser,
    RetrieveFormat,
    ScreenSize,
    ScrollAction,
    Transformer,
    WaitAction,
)

# Configuration
from .retry_strategy import RetryStrategy

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
