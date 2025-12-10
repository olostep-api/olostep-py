# Olostep Python SDK (official)

Olostep provides a **programmatic layer to access and interact with the web**.  
Fetch clean, ready-to-use data for your AI from any website in **1–5 seconds**, and scale up to **100K parallel requests in minutes**. You can:  

- **Scrape** websites with various output formats incl. structured data.
- **Batch** scrape hundreds of websites
- **Crawl** websites
- Create massive **sitemaps** in seconds
  
[Get a free API key here](https://www.olostep.com/?utm_source=python_readme)

## Python SDK vs API

The Olostep Python SDK offers features and ergonomics beyond the [REST API](https://docs.olostep.com):  

It streamlines web data access with a type-safe, stateful, and ergonomic experience not available in the REST API.


- **Discoverable and predictable interface**: Dot-notation namespaces, stateful return objects (IDs, cursors), convenience methods and rich `__repr__`s.
- **Async-first, Sync-friendly**: The SDK is async by default (but also provides a sync facade) This allows you async performance over an otherwise high latency sync API.
- **Type Safety & Input Coercion**: The client uses Pydantic to validate inputs and coerce them where possible. It also provides you with full type hints. It also catches errors before the request is being sent to the API (can be disabled).
- **Elegant Pagination**: `async for x in y.(batch_size=10):` for `batch` and `crawl` and `sitemap` handles all pagination.
- **Wait Methods**: `.wait_till_done()` for `batch` and `crawl` workflows.
- **Automatic retries**, improved errors and connection handling for high latency and throughput. 
- **Python 3.11+**.



## Quick start


```bash
$ pip install olostep
```

```python
""" 
The quickstart uses the async/await interface as it's the default and generally preferred. 
* If you need a blocking interface scroll to the end of this codeblock.
* If you want to see the full interfaces scroll to the next section.
"""

from olostep import OlostepClient

# Provide the API key either via passing in the 'api_key' parameter or
# by setting the OLOSTEP_API_KEY environment variable

# RESOURCE MANAGEMENT
# ===================
# The SDK supports two usage patterns for resource management:

# 1. Context Manager (Recommended for one-off usage):
#    Automatically handles resource cleanup
async with OlostepClient(api_key="YOUR_REAL_KEY") as client:
    scrape_result = await client.scrape.create(url_to_scrape="https://example.com")
# Transport is automatically closed here

# 2. Explicit Close (For long-lived services):
#    Requires manual resource cleanup
client = OlostepClient(api_key="YOUR_REAL_KEY")
try:
    scrape_result = await client.scrape.create(url_to_scrape="https://example.com")
finally:
    await client.close()  # Manually close the transport



# MINIMAL SCRAPE EXAMPLE

scrape_result = await client.scrape.create(url_to_scrape="https://example.com")
# -> ScrapeResult(id='scrape_123', available=['html_content', 'markdown_content'])



# MINIMAL BATCH EXAMPLE

batch = await client.batch.start(urls=["https://site1.com", "https://site2.com"])
# -> Batch(id='batch_123', urls=2)

# waits for all the batch jobs to finish, then starts fetching the results in batches
async for item in batch.items():
    content = await item.retrieve(["html"])
    print(f"{item.url}: {len(content.html_content)} bytes")



# MINIMAL CRAWL EXAMPLE

crawl = await client.crawl.start(start_url="https://example.com", max_pages=100)
# -> Crawl(id='crawl_123', urls=100)


async for page in crawl.pages():
    content = await page.retrieve(["html"])
    print(f"{page.url}: {len(content.html_content)} bytes")



# SYNC (FACADE) CLIENT
# this client is just a wrapper around the async client.
# The interface is the same, just don't use await.
# If you can use the OlostepClient instead, do so.
from olostep import SyncOlostepClient

# RESOURCE MANAGEMENT FOR SYNC CLIENT
# ===================================
# The sync client supports two usage patterns:

# 1. Direct Usage (Recommended for one-off calls):
#    No explicit resource management needed
client = SyncOlostepClient(api_key="YOUR_REAL_KEY")
scrape_result = client.scrape.create(url_to_scrape="https://example.com")
# No explicit close needed

# 2. Explicit Close (For long-lived services):
#    Call close() for consistency (currently a no-op)
client = SyncOlostepClient(api_key="YOUR_REAL_KEY")
try:
    scrape_result = client.scrape.create(url_to_scrape="https://example.com")
finally:
    client.close()  # No-op. For future compatibility

# -> ScrapeResult(id='scrape_123', available=['html_content', 'markdown_content'])
```

## API Design

The SDK provides a clean, Pythonic interface organized into logical namespaces. Each operation returns stateful objects with ergonomic methods for follow-up operations.


#### Scraping
```python
from olostep import OlostepClient
from olostep import Country, FillInputAction, Format, LLMExtract, LinksOnPage, ScreenSize, Transformer, WaitAction

client = OlostepClient(api_key="YOUR_REAL_KEY")


# Minimal: Just scrape a URL
result = await client.scrape.create(url_to_scrape="https://example.com")
# ScrapeResult(id='scrape_123', available=['html_content', 'markdown_content'])

# Maximal: Full control over scraping behavior
result = await client.scrape.create(
    url_to_scrape="https://example.com",
    wait_before_scraping=3000,
    formats=[Format.HTML, Format.MARKDOWN],
    remove_css_selectors=["script", ".popup"],
    actions=[
        WaitAction(milliseconds=1500), 
        FillInputAction(selector="searchbox", value="olostep")
    ],
    country=Country.US,
    transformer=Transformer("postlight"),
    remove_images=True,
    remove_class_names=["ad"],
    parser="VALID_PARSER", #check website for valid parsers
    llm_extract=LLMExtract(schema="YOUR_SCHEMA"),
    links_on_page=LinksOnPage(
        absolute_links=False, 
        query_to_order_links_by='cars', 
        include_links=["/events/**", "/offers/**"],
        exclude_links=[".pdf"]
    ),
    screen_size=ScreenSize(screen_width=1920, screen_height=1080),
    metadata={"custom": "sidecart_data"} # Not supported yet
)
```

#### Batch Processing
```python
from olostep import OlostepClient
from olostep import BatchItem, Country

client = OlostepClient(api_key="YOUR_REAL_KEY")


# Minimal: Process a list of URLs
batch = await client.batch.start(urls=["https://site1.com", "https://site2.com"])
# Batch(id='batch_123', urls=2)

# Maximal: Advanced batch with custom IDs and options
batch = await client.batch.start(
    urls=[
        BatchItem(url="https://www.google.com/search?q=olostep"),
        BatchItem(url="https://www.google.com/search?q=olostep+api", custom_id="news_2")
    ],
    country=Country.US,
    parser_id="@olostep/google-search"
)

# This is optional but you can check on the process of your batch at any time with:
info = await batch.info()  
# -> BatchInfo(id='batch_123', status='in_progress', completed=1/2, age=2h ago)

# Also optional: Wait for completion.
# Pass in `check_every_n_secs=` to change interval, default 10 
await batch.wait_till_done()


# Note: batch.items() automatically checks if the batch is completed before starting to return elements (can be disabled by passing in `wait_for_completion=False`)
async for item in batch.items(batch_size=10):
    content = await item.retrieve(["html", "json"]) # json from the parser
    print(f"{item.custom_id}: {len(content.html_content)} bytes")

# Alternative: Direct API access (stateless)
async for item in client.batch.items(batch_id='a_batch_id', batch_size=10):
    content = await item.retrieve(["html", "json"])
    print(f"{item.custom_id}: {len(content.html_content)} bytes")
```

#### Web Crawling
```python
# Minimal: Crawl a site with default settings
crawl = await client.crawl.start(start_url="https://example.com", max_pages=100)
# Crawl(id='crawl_123', urls=100)

# Maximal: Advanced crawling with filters and limits
crawl = await client.crawl.start(
    start_url="https://example.com",
    max_pages=1000,
    max_depth=3,
    include_urls=["/articles/**", "/news/**"],
    exclude_urls=["/ads/**", "/tracking/**"],
    include_external=False,
    include_subdomain=True,
    search_query="hot shingles",
    top_n=50
)

# This is optional but you can check on the process of your crawl at any time with:
info = await crawl.info()  # CrawlInfo(id='crawl_123', status='in_progress', pages_count=42, age=15m ago)

# Also optional: Wait for completion.
# Pass in `check_every_n_secs=` to change interval, default 10 
await crawl.wait_till_done()

# Note: crawl.pages automatically checks if the batch is completed before starting to return elements (can be disabled by passing in `wait_for_completion=False`)
async for page in crawl.pages():
    content = await page.retrieve(["html"])
    print(f"{page.url}: {len(content.html_content)} bytes")

# Alternative: Direct API access (stateless)
async for page in client.crawl.pages(crawl_id='a_crawl_id'):
    content = await page.retrieve(["html"])
    print(f"{page.url}: {len(content.html_content)} bytes")

```

#### Site Mapping
```python
# Minimal: Extract all links from a site
sitemap = await client.sitemap.create(url_to_map="https://example.com")
# Sitemap(id='map_123', urls_count=150, has_more=True)

# Maximal: Advanced link extraction with filters
sitemap = await client.sitemap.create(
    url_to_map="https://example.com",
    search_query="documentation",
    top_n=500,
    include_subdomain=True,
    include_urls=["/docs/**", "/api/**"],
    exclude_urls=["/admin/**", "/private/**"]
)

# Seamless iteration over all URLs (auto-pagination)
all_urls = []
async for url in sitemap.urls(): # async generator
    print(f"Found URL: {url}")
    all_urls.append(url) 
# Note: This can yield tens of thousands of URLs. If you can don't 
#       create a list but use the generator as such.


```

#### Data Retrieval
```python
# Notes: 
#   * You should generally not need to use this endpoint as the other endpoints generate stateful return objects that can retrieve content.
#   * Not all formats are available all the time

# Minimal: Get content by retrieve ID
result = await client.retrieve.get(retrieve_id="ret_123")
# ScrapeResult(id='ret_123', available=[...])

# Maximal: Get multiple formats
result = await client.retrieve.get(retrieve_id="ret_123", formats=["html", "markdown", "text", "json"])
# ScrapeResult(id='ret_123', available=['html_content', 'markdown_content', 'text_content', 'json_content'])



```


### Method Shorthands

The SDK provides convenient shorthand methods for common operations:

```python
# Method naming convention:
await client.scrape.create(url_to_scrape="https://example.com")   # explicit method
await client.batch.start(urls=["url1", "url2"])                  # explicit method
await client.crawl.start(start_url="https://example.com")         # explicit method
await client.sitemap.create(url_to_map="https://example.com")     # explicit method
await client.retrieve.get(retrieve_id="ret_123")                  # explicit method
```

### Smart Input Coercion

The SDK intelligently handles various input formats for maximum convenience:

```python
# Formats: string, list, or enum
await client.scrape.create(url_to_scrape="https://example.com", formats="html")
await client.scrape.create(url_to_scrape="https://example.com", formats=["html", "markdown"])


# Countries: case-insensitive strings or enums
await client.scrape.create(url_to_scrape="https://example.com", country="us")
await client.scrape.create(url_to_scrape="https://example.com", country=Country.US)

# Lists: single values or lists
await client.batch.start(urls="https://example.com")    # Single URL
await client.batch.start(urls=["https://a.com", "https://b.com"])  # Multiple URLs
```

  

### Logging & Error Handling

The SDK root logger is predictably called `olostep`. Granular sub-loggers exist.  
The recommended log level is `INFO` or higher.
`DEBUG` really means debug and is very detailed.


Handling the error behavior of the API can quite complex. The SDK handles error detection for you and returns the following errors:

Our exception hierarchy:
```
* Olostep_BaseError -------------------------------------- <- Catch base class for all errors
  x Olostep_APIConnectionError --------------------------- <- No connection to the API
  x OlostepServerError_BaseError ------------------------- <- Server-issued errors (still detected in client ofc)
    + OlostepServerError_TemporaryIssue
      - OlostepServerError_NetworkBusy
      - OlostepServerError_InternalNetworkIssue
    + OlostepServerError_RequestUnprocessable
      - OlostepServerError_ParserNotFound
      - OlostepServerError_OutOfResources
    + OlostepServerError_BlacklistedDomain
    + OlostepServerError_FeatureApprovalRequired
    + OlostepServerError_AuthFailed
    + OlostepServerError_CreditsExhausted
    + OlostepServerError_InvalidEndpointCalled
    + OlostepServerError_ResourceNotFound
    + OlostepServerError_NoResultInResponse
    + OlostepServerError_UnknownIssue
  x OlostepClientError_BaseError ------------------------- <- Client-issued errors
    + OlostepClientError_RequestValidationFailed
    + OlostepClientError_ResponseValidationFailed
    + OlostepClientError_NoAPIKey
    + OlostepClientError_AsyncContext
    + OlostepClientError_BetaFeatureAccessRequired
    + OlostepClientError_Timeout

```