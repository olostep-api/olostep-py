"""
Olostep API Endpoints Documentation.

This module serves as comprehensive documentation in code for the Olostep API.
It contains all endpoint definitions, URL patterns, request/response formats,
and usage examples for each API endpoint.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal
from ..models.request import (
    # Scrapes
    ScrapeUrlRequest,
    # Batches
    BatchStartRequest,
    BatchItemsRequest,
    # Crawls
    CrawlStartRequest,
    CrawlPagesRequest,
    # Maps
    MapCreateRequest,
    # Retrieve
    RetrieveGetRequest,
    # Answers
    AnswersRequest,
    AnswersGetRequest,
)
from ..models.response import (
    # Scrapes
    CreateScrapeResponse,
    GetScrapeResponse,
    # Batches
    BatchCreateResponse,
    BatchInfoResponse,
    BatchItemsResponse,
    # Crawls
    CreateCrawlResponse,
    CrawlInfoResponse,
    CrawlPagesResponse,
    # Maps
    MapResponse,
    # Retrieve
    RetrieveResponse,
    # Answers
    AnswersResponse,
)

Method = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]


@dataclass(frozen=True)
class EndpointContract:
    """Single source of truth for an API endpoint.

    Holds HTTP details and the concrete Pydantic v2 request/response models.
    Frontends remain Pydantic-free and use these contracts only through the backend caller.
    """

    # Stable registry key exposed to frontends as namespaces/methods
    key: tuple[str, str]

    # Human docs
    name: str
    description: str

    # HTTP details
    method: Method
    path: str  # e.g., "/scrapes" or "/scrapes/{scrape_id}"

    # IO models (backend validation only)
    request_model: type[Any] | None = None
    response_model: type[Any] | None = None

    # Optional examples for docs/SDK help
    examples: list[dict[str, Any]] = field(default_factory=list)

    def formatted_path(
        self,
        path_params: dict[str, Any] | None = None,
    ) -> str:
        path_params = path_params or {}
        formatted_path = self.path.format(**path_params)
        formatted_path = formatted_path.rstrip('/')
        formatted_path = formatted_path.lstrip('/')
        return formatted_path

    @property
    def path_parameters(self) -> list[str]:
        return re.findall(r"{([^}]+)}", self.path)


# =============================================================================
# SCRAPES
# =============================================================================

SCRAPE_URL = EndpointContract(
    key=("scrape", "url"),
    name="Create Scrape",
    description="Create a new web scraping job to extract content from a URL",
    method="POST",
    path="/scrapes",
    request_model=ScrapeUrlRequest,
    response_model=CreateScrapeResponse,
    examples=[
        {
            "description": "Basic HTML scrape",
            "request": {"url_to_scrape": "https://example.com", "formats": ["html"]},
        },
        {
            "description": "Multi-format scrape with configuration",
            "request": {
                "url_to_scrape": "https://example.com",
                "formats": ["html", "markdown", "text"],
                "country": "US",
                "remove_images": True,
                "wait_before_scraping": 2000,
            },
        },
    ],
)

SCRAPE_GET = EndpointContract(
    key=("scrape", "get"),
    name="Get Scrape",
    description="Retrieve the results of a completed scraping job",
    method="GET",
    path="/scrapes/{scrape_id}",
    request_model=None,
    response_model=GetScrapeResponse,
    examples=[
        {"description": "Retrieve scrape results", "path_params": {"scrape_id": "scrape_12345"}},
    ],
)


# =============================================================================
# BATCHES
# =============================================================================

BATCH_START = EndpointContract(
    key=("batch", "start"),
    name="Create Batch",
    description="Create a batch scraping job to process multiple URLs",
    method="POST",
    path="/batches",
    request_model=BatchStartRequest,
    response_model=BatchCreateResponse,
    examples=[
        {
            "description": "Basic batch creation",
            "request": {
                "items": [
                    {"url": "https://example1.com", "custom_id": "item1"},
                    {"url": "https://example2.com", "custom_id": "item2"},
                ]
            },
        },
        {
            "description": "Batch with configuration",
            "request": {
                "items": [{"url": "https://example.com", "custom_id": "test"}],
                "country": "US",
                "parser": {"id": "default"},
            },
        },
    ],
)

BATCH_INFO = EndpointContract(
    key=("batch", "info"),
    name="Get Batch Info",
    description="Retrieve information about a batch scraping job",
    method="GET",
    path="/batches/{batch_id}",
    request_model=None,
    response_model=BatchInfoResponse,
    examples=[
        {"description": "Get batch status", "path_params": {"batch_id": "batch_12345"}},
    ],
)

BATCH_ITEMS = EndpointContract(
    key=("batch", "items"),
    name="Get Batch Items",
    description="Retrieve the results of individual items in a batch",
    method="GET",
    path="/batches/{batch_id}/items",
    request_model=BatchItemsRequest,
    response_model=BatchItemsResponse,
    examples=[
        {
            "description": "Get all completed items",
            "path_params": {"batch_id": "batch_12345"},
            "query_params": {"status": "completed"},
        },
        {
            "description": "Get items with pagination",
            "path_params": {"batch_id": "batch_12345"},
            "query_params": {"limit": 10, "cursor": 0},
        },
    ],
)


# =============================================================================
# CRAWLS
# =============================================================================

CRAWL_START = EndpointContract(
    key=("crawl", "start"),
    name="Create Crawl",
    description="Create a web crawling job to discover and scrape linked pages",
    method="POST",
    path="/crawls",
    request_model=CrawlStartRequest,
    response_model=CreateCrawlResponse,
    examples=[
        {
            "description": "Basic crawl creation",
            "request": {"start_url": "https://example.com", "max_pages": 10, "follow_links": True},
        }
    ],
)

CRAWL_INFO = EndpointContract(
    key=("crawl", "info"),
    name="Get Crawl Info",
    description="Retrieve information about a web crawling job",
    method="GET",
    path="/crawls/{crawl_id}",
    request_model=None,
    response_model=CrawlInfoResponse,
    examples=[
        {"description": "Get crawl status", "path_params": {"crawl_id": "crawl_12345"}},
    ],
)

CRAWL_PAGES = EndpointContract(
    key=("crawl", "pages"),
    name="Get Crawl Pages",
    description="Retrieve the pages discovered during a crawl",
    method="GET",
    path="/crawls/{crawl_id}/pages",
    request_model=CrawlPagesRequest,
    response_model=CrawlPagesResponse,
    examples=[
        {"description": "Get all crawled pages", "path_params": {"crawl_id": "crawl_12345"}},
        {
            "description": "Get pages with pagination",
            "path_params": {"crawl_id": "crawl_12345"},
            "query_params": {"limit": 20, "cursor": 0},
        },
    ],
)


# =============================================================================
# MAPS
# =============================================================================

MAP_CREATE = EndpointContract(
    key=("map", "create"),
    name="Create Map",
    description="Extract links from a website",
    method="POST",
    path="/maps",
    request_model=MapCreateRequest,
    response_model=MapResponse,
    examples=[
        {"description": "Basic link extraction", "request": {"url": "https://example.com"}},
        {
            "description": "Link extraction with filtering",
            "request": {
                "url": "https://example.com",
                "search_query": "blog",
                "top_n": 10,
                "include_urls": ["/blog/**"],
                "exclude_urls": ["/admin/**"],
            },
        },
    ],
)


# =============================================================================
# RETRIEVE
# =============================================================================

RETRIEVE_GET = EndpointContract(
    key=("retrieve", "get"),
    name="Retrieve Content",
    description="Retrieve content by its unique identifier with specified formats",
    method="GET",
    path="/retrieve",
    request_model=RetrieveGetRequest,
    response_model=RetrieveResponse,
    examples=[
        {
            "description": "Retrieve content by ID with formats",
            "query_params": {"retrieve_id": "retrieve_12345", "formats": ["html", "markdown", "json"]},
        }
    ],
)


# =============================================================================
# ANSWERS
# =============================================================================

ANSWERS_CREATE = EndpointContract(
    key=("answers", "create"),
    name="Create Answer",
    description="Generate an answer for a given task with optional JSON format specification",
    method="POST",
    path="/answers",
    request_model=AnswersRequest,
    response_model=AnswersResponse,
    examples=[
        {
            "description": "Basic task answering",
            "request": {"task": "What is the capital of France?"},
        },
        {
            "description": "Task with JSON format specification",
            "request": {
                "task": "Extract all product names and prices from the webpage",
                "json_format": {
                    "products": [
                        {
                            "name": "",
                            "price": ""
                        }
                    ]
                }
            },
        },
    ],
)

ANSWERS_GET = EndpointContract(
    key=("answers", "get"),
    name="Get Answer",
    description="Retrieve the results of a completed answer generation job",
    method="GET",
    path="/answers/{answer_id}",
    request_model=AnswersGetRequest,
    response_model=AnswersResponse,
    examples=[
        {"description": "Retrieve answer results", "path_params": {"answer_id": "answer_12345"}},
    ],
)


# =============================================================================
# REGISTRY
# =============================================================================

CONTRACTS: dict[tuple[str, str], EndpointContract] = {
    c.key: c
    for c in [
        SCRAPE_URL,
        SCRAPE_GET,
        BATCH_START,
        BATCH_INFO,
        BATCH_ITEMS,
        CRAWL_START,
        CRAWL_INFO,
        CRAWL_PAGES,
        MAP_CREATE,
        RETRIEVE_GET,
        ANSWERS_CREATE,
        ANSWERS_GET,
    ]
}

