# Olostep Python SDK (official)

Olostep provides a programmatic layer to access and interact with the web.
Fetch clean, ready-to-use data for your AI from any website in **1–5 seconds**, and scale up to **100K parallel requests in minutes**
[Get a free API key here](https://www.olostep.com/?utm_source=python_readme)

## Python SDK
— Clean, namespaced Python SDK that returns ergonomic, stateful objects for instant follow-ups. Strict I/O validation. Python 3.11+.

Developer benefits:
- Dot-notation namespaces with discoverable methods and great editor autocomplete
- Stateful return objects (IDs, cursors) with convenience methods (`next()`, `items()`, `pages()`, `retrieve()`)
- Async-first with a sync facade; swappable transports (real HTTP or schema-driven fake)
- You work with simple, predictable objects and types.
- Behind the scenes Pydantic validation for high assurance RX / TX. (Catch errors before you hit the API)

## Quick start

```bash
$ pip install olostep
```

```python
from olostep import AsyncOlostepClient, OlostepClient

# Async (recommended)
client = AsyncOlostepClient(api_key="YOUR_REAL_KEY")  # or set OLOSTEP_API_KEY and omit api_key
# Sync facade (same API, blocking)
client = OlostepClient(api_key="YOUR_REAL_KEY")  # or set OLOSTEP_API_KEY and omit api_key

# or use as a context manager to preserve the session:
async with AsyncOlostepClient(api_key="...") as client:
    ...
# Or again the sync facade
with OlostepClient(api_key="YOUR_REAL_KEY") as client:
    ...
```

## API | SDK operations

```python
from typing import Any
from olostep import AsyncOlostepClient, OlostepClient
from olostep.backend.validation import Format, Country, RetrieveFormat

# scrape
await client.scrape.url(url_to_scrape, formats, parser_id, country, wait_before_scraping, remove_css_selectors, actions, transformer, remove_images, remove_class_names, links_on_page, screen_size, metadata)  # -> ScrapeResult
await client.scrape.get(scrape_id)  # -> ScrapeResult

# batch
await client.batch.start(items, country, parser_id)  # -> Batch
await client.batch.info(batch_id)  # -> BatchItems
await client.batch.items(batch_id, status, cursor, limit)  # -> BatchItems

# crawl
await client.crawl.start(start_url, max_pages, include_urls, exclude_urls, max_depth, include_external, include_subdomain, search_query, top_n, webhook_url)  # -> Crawl
await client.crawl.info(crawl_id)  # -> CrawlPages
await client.crawl.pages(crawl_id, cursor, limit, search_query)  # -> CrawlPages

# map
await client.map.create(url, search_query, top_n, include_subdomain, include_urls, exclude_urls, cursor)  # -> Map

# retrieve
await client.retrieve.get(retrieve_id, formats)  # -> ScrapeResult

# Sync client has the same call shapes, without `await`.
```

## Developer experience

### Input coercion
- Methods accept friendly inputs and coerce to the right shapes.
- Examples:
  - formats can be "html" or ["html", "markdown"] or [Format.HTML, Format.MARKDOWN]
  - Enums accept case-insensitive strings when obvious, or their typed counterparts
  - Lists accept a single value or a list interchangeably for convenience
  - URL convenience: accepts bare domains (e.g., "www.website.com"), trims stray punctuation, and auto-adds scheme when missing

### Output handles (stateful, strongly-typed)
- You get stateful client objects (aka handle objects) with readable reprs and convenience methods.

- **ScrapeResult** — `__repr__() -> ScrapeResult(id='scrape_123', available=['html_content','markdown_content','text_content'])`
  - .id -> str
  - .html_content -> str
  - .markdown_content -> str
  - .text_content -> str
  - .json_content -> dict[str, Any]

- **Batch** — `__repr__() -> Batch(id='batch_123', status='in_progress', completed=3/10)`
  - info() -> BatchInfo
  - items(status: str | None, cursor: int | None, limit: int | None) -> BatchItems

- **BatchInfo** — `__repr__() -> BatchInfo(status='in_progress', completed=3/10)`
  - status -> str
  - total_urls -> int
  - completed_urls -> int

- **BatchItems** — `__repr__() -> BatchItems(batch_id='batch_123', items_count=10, cursor=1)`
  - .items -> list[BatchItem]
  - next(status: str | None, limit: int | None) -> BatchItems | None

- **BatchItem** — `__repr__() -> BatchItem(url='https://a', retrieve_id='ret_1', custom_id='foo')`
  - retrieve(formats: list[RetrieveFormat]) -> ScrapeResult

- **Crawl** — `__repr__() -> Crawl(id='crawl_123', status='in_progress', pages_count=42)`
  - info() -> CrawlInfo
  - pages(cursor: int | None, limit: int | None, search_query: str | None) -> CrawlPages

- **CrawlInfo** — `__repr__() -> CrawlInfo(status='in_progress', pages_count=42)`
  - status -> str
  - pages_count -> int

- **CrawlPages** — `__repr__() -> CrawlPages(crawl_id='crawl_123', pages_count=20, cursor=1)`
  - .pages -> list[CrawlPage]
  - next(limit: int | None) -> CrawlPages | None

- **CrawlPage** — `__repr__() -> CrawlPage(url='https://p1', retrieve_id='ret_1', external=False)`
  - retrieve(formats: list[RetrieveFormat]) -> ScrapeResult

- **Map** — `__repr__() -> Map(id='map_1', urls_count=1000, cursor='next_1')`
  - next() -> Map | None

## Examples

### Scrape a page
```python
from olostep import AsyncOlostepClient

async with AsyncOlostepClient(api_key="...") as client:
    s = await client.scrape.url(
        url_to_scrape="https://example.com",
        formats=["html", "markdown"],  # string coercion works
        country="US",                   # enum coercion works
    )
    print(s)                # ScrapeResult(...)
    print(len(s.html_content), len(s.markdown_content))
```

### Batch workflow
```python
from olostep import AsyncOlostepClient

async with AsyncOlostepClient(api_key="...") as client:
    b = await client.batch.start(items=[{"url": "https://a"}, {"url": "https://b"}])
    items = await b.items(limit=50)
    for it in items.items:
        r = await it.retrieve(["html"])  # accepts strings or RetrieveFormat
        print(it.custom_id, len(r.html_content))

    nxt = await items.next(limit=50)
    if nxt:
        print("next page of items:", len(nxt.items))
```

### Crawl pages and iterate
```python
from olostep import AsyncOlostepClient

async with AsyncOlostepClient(api_key="...") as client:
    c = await client.crawl.start(start_url="https://example.com", max_pages=25)
    pages = await c.pages(limit=100)
    while pages:
        for p in pages.pages:
            sr = await p.retrieve(["html"])  # convenience retrieve
            print(p.url, p.is_external, len(sr.html_content))
        pages = await pages.next(limit=100)
```

### Map a site (link extraction)
```python
from olostep import AsyncOlostepClient

async with AsyncOlostepClient(api_key="...") as client:
    m = await client.map.create(
        url="https://example.com",
        include_subdomain=True,
        include_urls=["/**"],
    )
    print(m.urls_count, len(m.urls))
    nxt = await m.next()
    if nxt:
        print("more urls:", nxt.cursor)
```

### Retrieve by id
```python
from olostep import AsyncOlostepClient

async with AsyncOlostepClient(api_key="...") as client:
    sr = await client.retrieve.get(retrieve_id="ret_123", formats=["html", "markdown"])  # coercion works
    print(len(sr.html_content))

# Sync facade mirrors the same flows without 'await'.
```

### Status progress (batch) with tqdm
```python
import asyncio
from tqdm import tqdm
from olostep import AsyncOlostepClient

async with AsyncOlostepClient(api_key="...") as client:
    # Coercion: items can be a list of strings
    b = await client.batch.start(items=["https://a.com.", "www.website.com"])  # -> Batch

    # Initial info to get total
    info = await client.batch.info(batch_id=b.id)
    total = info.total_urls
    done = 0

    with tqdm(total=total, desc="Batch progress") as bar:
        while True:
            await asyncio.sleep(1.5)
            info = await client.batch.info(batch_id=b.id)
            bar.update(max(0, info.completed_urls - done))
            done = info.completed_urls
            if info.completed_urls >= total:
                break
```

### Status progress (crawl) with tqdm
```python
import asyncio
from tqdm import tqdm
from olostep import AsyncOlostepClient

async with AsyncOlostepClient(api_key="...") as client:
    c = await client.crawl.start(start_url="https://example.com", max_pages=100000)  # -> Crawl

    # Use the requested max_pages as the bar total
    max_pages = 100000
    done = 0

    with tqdm(total=max_pages, desc="Crawl pages") as bar:
        while True:
            await asyncio.sleep(2.0)
            info = await c.info()  # -> CrawlInfo
            bar.update(max(0, info.pages_count - done))
            done = info.pages_count
            if info.status == "completed" or done >= max_pages:
                break
``` 