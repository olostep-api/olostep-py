from __future__ import annotations

from typing import Any
from typing_extensions import TypedDict, NotRequired
from ...backend.validation import Format, Country, RetrieveFormat


# =========================
# Scrape
# =========================
class ScrapeUrlKw(TypedDict):
    url_to_scrape: str
    formats: NotRequired[list[Format]]
    parser_id: NotRequired[str]
    country: NotRequired[Country]
    wait_before_scraping: NotRequired[int]
    remove_css_selectors: NotRequired[str | list[str]]
    actions: NotRequired[list[dict[str, Any]]]
    transformer: NotRequired[str]
    remove_images: NotRequired[bool]
    remove_class_names: NotRequired[list[str]]
    links_on_page: NotRequired[dict[str, Any]]
    screen_size: NotRequired[dict[str, Any]]
    metadata: NotRequired[dict[str, Any]]


# =========================
# Retrieve
# =========================
class RetrieveKw(TypedDict):
    retrieve_id: str
    formats: list[RetrieveFormat]


# =========================
# Batch
# =========================
class BatchItemKw(TypedDict):
    url: str
    custom_id: NotRequired[str]


class BatchStartKw(TypedDict):
    items: list[BatchItemKw]
    country: NotRequired[Country]
    parser_id: NotRequired[str]


class BatchInfoKw(TypedDict):
    batch_id: str


class BatchItemsKw(TypedDict):
    batch_id: str
    status: NotRequired[str]
    cursor: NotRequired[int]
    limit: NotRequired[int]


# =========================
# Crawl
# =========================
class CrawlStartKw(TypedDict):
    start_url: str
    max_pages: int
    include_urls: NotRequired[list[str]]
    exclude_urls: NotRequired[list[str]]
    max_depth: NotRequired[int]
    include_external: NotRequired[bool]
    include_subdomain: NotRequired[bool]
    search_query: NotRequired[str]
    top_n: NotRequired[int]
    webhook_url: NotRequired[str]


class CrawlInfoKw(TypedDict):
    crawl_id: str


class CrawlPagesKw(TypedDict):
    crawl_id: str
    cursor: NotRequired[int]
    limit: NotRequired[int]
    search_query: NotRequired[str]


# =========================
# Map
# =========================
class MapCreateKw(TypedDict):
    url: str
    search_query: NotRequired[str]
    top_n: NotRequired[int]
    include_subdomain: NotRequired[bool]
    include_urls: NotRequired[list[str]]
    exclude_urls: NotRequired[list[str]]
    cursor: NotRequired[str] 