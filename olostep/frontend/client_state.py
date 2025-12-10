"""
Stateful client objects for the Typed UI.

This layer provides quality-of-life wrappers that hold minimal client-side state
(e.g., ids, cursors, original request hints) and expose ergonomic shorthand
methods for follow-up operations (info, items/pages, next, retrieve). It also
presents response data via friendly properties and readable string
representations, while leaving all IO validation to the backend (Pydantic) and
all transport logic to the EndpointCaller.
"""

from __future__ import annotations

from typing import Any, Iterator

from ..api_endpoints import CONTRACTS
from ..backend.caller import EndpointCaller
from ..frontend.typed_dict.types import MapCreateKw
from ..backend.validation import (
    CreateScrapeResponse,
    GetScrapeResponse,
    RetrieveResponse,
    BatchCreateResponse,
    BatchInfoResponse,
    BatchItemsResponse,
    BatchItemsResponseListItem,
    CreateCrawlResponse,
    CrawlInfoResponse,
    CrawlPagesResponse,
    CrawlPagesResponseListItem,
    MapResponse,
)


class ScrapeResult:
    def __init__(self, response: CreateScrapeResponse | GetScrapeResponse | RetrieveResponse) -> None:
        self._response = response
        # Create/Get have nested result; RetrieveResponse is the result
        self._results = getattr(response, "result", response)

    def __repr__(self) -> str:
        keys = [
            k
            for k in ("html_content", "markdown_content", "text_content", "json_content")
            if getattr(self._results, k, None)
        ]
        return f"ScrapeResult(id={self.id!r}, available={keys})"

    def __str__(self) -> str:
        html_len = len(self.html_content) if self.html_content else 0
        md_len = len(self.markdown_content) if self.markdown_content else 0
        txt_len = len(self.text_content) if self.text_content else 0
        return (
            f"ScrapeResult(id={self.id}, html={html_len}B, md={md_len}B, text={txt_len}B, "
            f"json={'yes' if bool(self.json_content) else 'no'})"
        )

    @property
    def id(self) -> str:
        return getattr(self._response, "id", "") or ""

    @property
    def html_content(self) -> str:
        return getattr(self._results, "html_content", "") or ""

    @property
    def markdown_content(self) -> str:
        return getattr(self._results, "markdown_content", "") or ""

    @property
    def text_content(self) -> str:
        return getattr(self._results, "text_content", "") or ""

    @property
    def json_content(self) -> dict[str, Any]:
        jc = getattr(self._results, "json_content", None)
        return jc if isinstance(jc, dict) else {}

    @property
    def links_on_page(self) -> list[str]:
        return getattr(self._results, "links_on_page", None) or []

    @property
    def html_hosted_url(self) -> str:
        return getattr(self._results, "html_hosted_url", "") or ""

    @property
    def markdown_hosted_url(self) -> str:
        return getattr(self._results, "markdown_hosted_url", "") or ""

    @property
    def json_hosted_url(self) -> str:
        return getattr(self._results, "json_hosted_url", "") or ""

    @property
    def size_exceeded(self) -> bool:
        return bool(getattr(self._results, "size_exceeded", False))


class BatchItem:
    def __init__(self, caller: EndpointCaller, item: BatchItemsResponseListItem) -> None:
        self._caller = caller
        self._item = item

    def __repr__(self) -> str:
        return f"BatchItem(url={self.url!r}, retrieve_id={self.retrieve_id!r}, custom_id={self.custom_id!r})"

    def __str__(self) -> str:
        return f"BatchItem {self.custom_id or '-'} -> {self.url} ({self.retrieve_id})"

    @property
    def url(self) -> str:
        return self._item.url

    @property
    def retrieve_id(self) -> str:
        return self._item.retrieve_id

    @property
    def custom_id(self) -> str:
        return self._item.custom_id or ""

    async def retrieve(self, formats: list[Any]) -> ScrapeResult:
        c = CONTRACTS[("retrieve", "get")]
        data: RetrieveResponse = await self._caller.invoke(c, args={"retrieve_id": self._item.retrieve_id, "formats": formats})
        return ScrapeResult(data)


class BatchItems:
    def __init__(self, caller: EndpointCaller, response: BatchItemsResponse) -> None:
        self._caller = caller
        self._response = response

    def __repr__(self) -> str:
        return f"BatchItems(batch_id={self._response.batch_id!r}, items_count={self.items_count}, cursor={self._response.cursor!r})"

    def __str__(self) -> str:
        return f"BatchItems: {self.items_count} items (cursor={'set' if self._response.cursor is not None else 'none'})"

    def __iter__(self) -> Iterator[BatchItem]:
        return iter(self.items)

    def __dir__(self) -> list[str]:
        return [n for n in super().__dir__() if n != "items"]

    @property
    def items(self) -> list[BatchItem]:
        return [BatchItem(self._caller, i) for i in self._response.items]

    @property
    def items_count(self) -> int:
        return self._response.items_count

    async def next(self, *, status: str | None = None, limit: int | None = None) -> BatchItems | None:
        if self._response.cursor is None:
            return None
        c = CONTRACTS[("batch", "items")]
        args: dict[str, Any] = {"batch_id": self._response.batch_id, "cursor": self._response.cursor}
        if status is not None:
            args["status"] = status
        if limit is not None:
            args["limit"] = limit
        data: BatchItemsResponse = await self._caller.invoke(c, args=args)
        return BatchItems(self._caller, data)


class BatchInfo:
    def __init__(self, response: BatchInfoResponse) -> None:
        self._response = response

    def __repr__(self) -> str:
        return f"BatchInfo(status={self.status!r}, completed={self.completed_urls}/{self.total_urls})"

    def __str__(self) -> str:
        return f"BatchInfo: status={self.status}, progress={self.completed_urls}/{self.total_urls}"

    @property
    def status(self) -> str:
        return self._response.status

    @property
    def total_urls(self) -> int:
        return self._response.total_urls

    @property
    def completed_urls(self) -> int:
        return self._response.completed_urls


class Batch:
    def __init__(self, caller: EndpointCaller, response: BatchCreateResponse) -> None:
        self._caller = caller
        self._response = response

    def __repr__(self) -> str:
        return (
            f"Batch(id={self.id!r}, status={self.status!r}, "
            f"completed={self.completed_urls}/{self.total_urls})"
        )

    def __str__(self) -> str:
        return f"Batch {self.id} [{self.status}] {self.completed_urls}/{self.total_urls}"

    @property
    def id(self) -> str:
        return self._response.id

    @property
    def status(self) -> str:
        return str(self._response.status)

    @property
    def created(self) -> int:
        return self._response.created

    @property
    def total_urls(self) -> int:
        return self._response.total_urls

    @property
    def completed_urls(self) -> int:
        return self._response.completed_urls

    async def info(self) -> BatchInfo:
        c = CONTRACTS[("batch", "info")]
        data: BatchInfoResponse = await self._caller.invoke(c, args={"batch_id": self.id})
        return BatchInfo(data)

    async def items(self, *, status: str | None = None, cursor: int | None = None, limit: int | None = None) -> BatchItems:
        c = CONTRACTS[("batch", "items")]
        args: dict[str, Any] = {"batch_id": self.id}
        if status is not None:
            args["status"] = status
        if cursor is not None:
            args["cursor"] = cursor
        if limit is not None:
            args["limit"] = limit
        data: BatchItemsResponse = await self._caller.invoke(c, args=args)
        return BatchItems(self._caller, data)


class CrawlPage:
    def __init__(self, caller: EndpointCaller, item: CrawlPagesResponseListItem) -> None:
        self._caller = caller
        self._item = item

    def __repr__(self) -> str:
        return f"CrawlPage(url={self.url!r}, retrieve_id={self.retrieve_id!r}, external={self.is_external})"

    def __str__(self) -> str:
        return f"CrawlPage {self.url} ({'external' if self.is_external else 'internal'})"

    @property
    def url(self) -> str:
        return self._item.url

    @property
    def retrieve_id(self) -> str:
        return self._item.retrieve_id

    @property
    def is_external(self) -> bool:
        return bool(self._item.is_external)

    async def retrieve(self, formats: list[Any]) -> ScrapeResult:
        c = CONTRACTS[("retrieve", "get")]
        data: RetrieveResponse = await self._caller.invoke(c, args={"retrieve_id": self._item.retrieve_id, "formats": formats})
        return ScrapeResult(data)


class CrawlPages:
    def __init__(self, caller: EndpointCaller, response: CrawlPagesResponse) -> None:
        self._caller = caller
        self._response = response

    def __repr__(self) -> str:
        return f"CrawlPages(crawl_id={self._response.crawl_id!r}, pages_count={self.pages_count}, cursor={self._response.cursor!r})"

    def __str__(self) -> str:
        return f"CrawlPages: {self.pages_count} pages (cursor={'set' if self._response.cursor is not None else 'none'})"

    def __iter__(self) -> Iterator[CrawlPage]:
        return iter(self.pages)

    def __dir__(self) -> list[str]:
        return [n for n in super().__dir__() if n != "pages"]

    @property
    def pages(self) -> list[CrawlPage]:
        return [CrawlPage(self._caller, p) for p in self._response.pages]

    @property
    def pages_count(self) -> int:
        return self._response.pages_count

    async def next(self, *, limit: int | None = None) -> CrawlPages | None:
        if self._response.cursor is None:
            return None
        c = CONTRACTS[("crawl", "pages")]
        args: dict[str, Any] = {"crawl_id": self._response.crawl_id, "cursor": self._response.cursor}
        if limit is not None:
            args["limit"] = limit
        data: CrawlPagesResponse = await self._caller.invoke(c, args=args)
        return CrawlPages(self._caller, data)


class CrawlInfo:
    def __init__(self, response: CrawlInfoResponse) -> None:
        self._response = response

    def __repr__(self) -> str:
        return f"CrawlInfo(status={self.status!r}, pages_count={self.pages_count})"

    def __str__(self) -> str:
        return f"CrawlInfo: status={self.status}, pages_count={self.pages_count}"

    @property
    def status(self) -> str:
        return str(self._response.status)

    @property
    def pages_count(self) -> int:
        return self._response.pages_count


class Crawl:
    def __init__(self, caller: EndpointCaller, response: CreateCrawlResponse) -> None:
        self._caller = caller
        self._response = response

    def __repr__(self) -> str:
        return f"Crawl(id={self.id!r}, status={self.status!r}, pages_count={self.pages_count})"

    def __str__(self) -> str:
        return f"Crawl {self.id} [{self.status}] pages_count={self.pages_count}"

    @property
    def id(self) -> str:
        return self._response.id

    @property
    def status(self) -> str:
        return str(self._response.status)

    @property
    def pages_count(self) -> int:
        return self._response.pages_count

    async def info(self) -> CrawlInfo:
        c = CONTRACTS[("crawl", "info")]
        data: CrawlInfoResponse = await self._caller.invoke(c, args={"crawl_id": self.id})
        return CrawlInfo(data)

    async def pages(self, *, cursor: int | None = None, limit: int | None = None, search_query: str | None = None) -> CrawlPages:
        c = CONTRACTS[("crawl", "pages")]
        args: dict[str, Any] = {"crawl_id": self.id}
        if cursor is not None:
            args["cursor"] = cursor
        if limit is not None:
            args["limit"] = limit
        if search_query is not None:
            args["search_query"] = search_query
        data: CrawlPagesResponse = await self._caller.invoke(c, args=args)
        return CrawlPages(self._caller, data)


class Map:
    def __init__(self, caller: EndpointCaller, response: MapResponse, request: MapCreateKw) -> None:
        self._caller = caller
        self._response = response
        self._request = request

    def __repr__(self) -> str:
        return f"Map(id={self.id!r}, urls_count={self.urls_count}, cursor={self.cursor!r})"

    def __str__(self) -> str:
        return f"Map {self.id or '-'} urls_count={self.urls_count} (cursor={'set' if self.cursor else 'none'})"

    @property
    def id(self) -> str:
        return self._response.id or ""

    @property
    def cursor(self) -> str:
        return self._response.cursor or ""

    @property
    def urls(self) -> list[str]:
        return self._response.urls

    @property
    def urls_count(self) -> int:
        return self._response.urls_count

    async def next(self) -> Map | None:
        cur = self._response.cursor
        if cur is None:
            return None
        c = CONTRACTS[("map", "create")]
        req: MapCreateKw = {
            "url": self._request["url"],
            "search_query": self._request.get("search_query"),
            "top_n": self._request.get("top_n"),
            "include_subdomain": self._request.get("include_subdomain", True),
            "include_urls": self._request.get("include_urls"),
            "exclude_urls": self._request.get("exclude_urls"),
            "cursor": cur,
        }
        data: MapResponse = await self._caller.invoke(c, args=req, body=req)
        return Map(self._caller, data, req) 