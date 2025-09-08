from __future__ import annotations

from typing import Any
from typing_extensions import Unpack

from ...api_endpoints import (
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
)
from ...backend.caller import EndpointCaller
from ...frontend.typed_dict.types import (
    ScrapeUrlKw,
    RetrieveKw,
    BatchStartKw,
    BatchInfoKw,
    BatchItemsKw,
    CrawlStartKw,
    CrawlInfoKw,
    CrawlPagesKw,
    MapCreateKw,
)
from ...frontend.client_state import (
    Batch,
    BatchItems,
    Crawl,
    CrawlPages,
    Map,
    ScrapeResult,
)
from ...backend.validation import (
    CreateScrapeResponse,
    GetScrapeResponse,
    BatchCreateResponse,
    BatchInfoResponse,
    BatchItemsResponse,
    CreateCrawlResponse,
    CrawlInfoResponse,
    CrawlPagesResponse,
    MapResponse,
    RetrieveResponse,
)


class _ScrapeNS:
    def __init__(self, caller: EndpointCaller) -> None:
        self._caller = caller

    async def url(self, **kw: Unpack[ScrapeUrlKw]) -> ScrapeResult:
        res: CreateScrapeResponse = await self._caller.invoke(SCRAPE_URL, args=kw, body=kw)
        return ScrapeResult(res)

    async def get(self, scrape_id: str) -> ScrapeResult:
        res: GetScrapeResponse = await self._caller.invoke(SCRAPE_GET, args={"scrape_id": scrape_id})
        return ScrapeResult(res)


class _BatchNS:
    def __init__(self, caller: EndpointCaller) -> None:
        self._caller = caller

    async def start(self, **kw: Unpack[BatchStartKw]) -> Batch:
        res: BatchCreateResponse = await self._caller.invoke(BATCH_START, args=kw, body=kw)
        return Batch(self._caller, res)

    async def info(self, **kw: Unpack[BatchInfoKw]) -> BatchItems:
        # Provide first page state (limit=0) to maintain stateful semantics
        return await self.items(batch_id=kw["batch_id"], limit=0) #todo: check if this is correct

    async def items(self, **kw: Unpack[BatchItemsKw]) -> BatchItems:
        res: BatchItemsResponse = await self._caller.invoke(BATCH_ITEMS, args=kw)
        return BatchItems(self._caller, res)


class _CrawlNS:
    def __init__(self, caller: EndpointCaller) -> None:
        self._caller = caller

    async def start(self, **kw: Unpack[CrawlStartKw]) -> Crawl:
        res: CreateCrawlResponse = await self._caller.invoke(CRAWL_START, args=kw, body=kw)
        return Crawl(self._caller, res)

    async def info(self, **kw: Unpack[CrawlInfoKw]) -> CrawlPages:
        return await self.pages(crawl_id=kw["crawl_id"], limit=0) #todo: check if this is correct

    async def pages(self, **kw: Unpack[CrawlPagesKw]) -> CrawlPages:
        res: CrawlPagesResponse = await self._caller.invoke(CRAWL_PAGES, args=kw)
        return CrawlPages(self._caller, res)


class _MapNS:
    def __init__(self, caller: EndpointCaller) -> None:
        self._caller = caller

    async def create(self, **kw: Unpack[MapCreateKw]) -> Map:
        res: MapResponse = await self._caller.invoke(MAP_CREATE, args=kw, body=kw)
        return Map(self._caller, res, kw)


class _RetrieveNS:
    def __init__(self, caller: EndpointCaller) -> None:
        self._caller = caller

    async def get(self, **kw: Unpack[RetrieveKw]) -> ScrapeResult:
        res: RetrieveResponse = await self._caller.invoke(RETRIEVE_GET, args=kw)
        return ScrapeResult(res)


class TypedDictFrontend:
    def __init__(self, caller: EndpointCaller) -> None:
        self._caller = caller
        self.scrape = _ScrapeNS(caller)
        self.batch = _BatchNS(caller)
        self.crawl = _CrawlNS(caller)
        self.map = _MapNS(caller)
        self.retrieve = _RetrieveNS(caller) 