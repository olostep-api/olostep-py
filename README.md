<div align="center">
  <img src="https://www.olostep.com/images/olostep-logo-cropped.svg" alt="Olostep Logo" width="150"/>
  <br>

  <h2>Olostep Python SDK</h2>

✨ [Get a free API key](https://www.olostep.com/?utm_source=python_sdk_readme) • [Full Documentation](https://docs.olostep.com?utm_source=python_sdk_readme) • [GitHub Issues](https://github.com/olostep-api/olostep-py/issues) ✨

  <br>

  <p><strong>Programmatic web access for AI applications</strong>
  <br>
  Fetch clean, structured data from any website in 1–5 seconds<br>Scale to 100K+ parallel requests with enterprise reliability</p>
  <br>
</div>

---

## Table of Contents

- [Overview](#overview)
- [Why Choose the Python SDK?](#why-choose-the-python-sdk)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Advanced Features](#advanced-features)
- [Error Handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

## Overview

Olostep provides a **programmatic layer to access and interact with the web**.
Fetch clean, ready-to-use data for your AI from any website in **1–5 seconds**, and scale up to **100K parallel requests in minutes**. You can:

- **Scrape** websites with various output formats including structured data
- **Batch** scrape hundreds of websites simultaneously
- **Crawl** websites with intelligent filtering and depth control
- Create massive **sitemaps** in seconds for comprehensive site mapping

## Why Choose the Python SDK?

The Olostep Python SDK offers significant advantages over direct API usage:

| Feature              | SDK Advantage                                 | Direct API              |
| -------------------- | --------------------------------------------- | ----------------------- |
| **Interface**        | Discoverable dot-notation namespaces          | REST endpoints          |
| **Type Safety**      | Full Pydantic validation & type hints         | Manual validation       |
| **State Management** | Stateful return objects with rich `__repr__`s | Manual state tracking   |
| **Error Handling**   | Automatic retries & connection management     | Manual implementation   |
| **Pagination**       | Elegant `async for` loops                     | Manual cursor handling  |
| **Input Coercion**   | Smart type coercion & validation              | Manual data preparation |
| **Performance**      | Async-first with sync facade                  | HTTP request overhead   |

### Key Benefits

- **Developer Experience**: Type-safe, ergonomic Python API with intelligent input handling
- **Production Ready**: Automatic retries, connection pooling, and error recovery
- **AI-Optimized**: Clean, structured data extraction perfect for LLM applications
- **Enterprise Scale**: Handle 100K+ concurrent requests with robust error handling
- **Future-Proof**: Built on modern Python patterns (async/await, type hints, dataclasses)

## Installation

### PyPI (Recommended)

```bash
pip install olostep
```

### From Source

```bash
git clone https://github.com/olostep-api/olostep-py.git
cd olostep-python
pip install -e .
```

### Requirements

- Python 3.11+
- API key from [olostep.com](https://www.olostep.com/?utm_source=python_sdk_readme)

## Quick Start

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
```

### Retry Configuration

Control how the SDK handles transient errors:

```python
from olostep import OlostepClient, RetryStrategy

# Custom retry strategy
retry_strategy = RetryStrategy(
    max_retries=3,
    initial_delay=1.0,
    jitter_min=0.2,
    jitter_max=0.8
)

async with OlostepClient(
    api_key="your-api-key",
    retry_strategy=retry_strategy
) as client:
    result = await client.scrape.create("https://example.com")
```

See [docs/retry_strategy.md](docs/retry_strategy.md) for detailed configuration options.

## Usage Examples

### Basic Web Scraping

```python
import asyncio
from olostep import OlostepClient

async def main():
    async with OlostepClient(api_key="your-api-key") as client:
        # Simple scraping
        result = await client.scrape.create(url_to_scrape="https://example.com")
        print(f"Scraped {len(result.html_content)} characters")

        # Multiple formats
        result = await client.scrape.create(
            url_to_scrape="https://example.com",
            formats=["html", "markdown"]
        )
        print(f"HTML: {len(result.html_content)} chars")
        print(f"Markdown: {len(result.markdown_content)} chars")

asyncio.run(main())
```

### Batch Processing

```python
# Process multiple URLs efficiently
batch = await client.batch.start(
    urls=["https://site1.com", "https://site2.com", "https://site3.com"]
)

# Wait for completion and process results
async for item in batch.items():
    content = await item.retrieve(["html"])
    print(f"Processed {item.url}: {len(content.html_content)} bytes")
```

### Smart Web Crawling

```python
# Crawl with intelligent filtering
crawl = await client.crawl.start(
    start_url="https://example.com",
    max_pages=100,
    include_urls=["/articles/**", "/blog/**"],
    exclude_urls=["/admin/**"]
)

async for page in crawl.pages():
    content = await page.retrieve(["html"])
    print(f"Crawled: {page.url}")
```

### Site Mapping

```python
# Extract all links from a website
sitemap = await client.sitemap.create(url_to_map="https://example.com")

# Get all discovered URLs
urls = []
async for url in sitemap.urls():
    urls.append(url)
    if len(urls) >= 10:  # Limit for demo
        break

print(f"Found {len(urls)} URLs")
```

## API Reference

### Core Clients

#### OlostepClient (Async)

The main async client for high-performance applications.

```python
from olostep import OlostepClient

# Context manager (recommended)
async with OlostepClient(api_key="your-key") as client:
    result = await client.scrape.create(url_to_scrape="https://example.com")

# Explicit resource management
client = OlostepClient(api_key="your-key")
try:
    result = await client.scrape.create(url_to_scrape="https://example.com")
finally:
    await client.close()
```

#### SyncOlostepClient

Synchronous wrapper for blocking applications.

```python
from olostep import SyncOlostepClient

client = SyncOlostepClient(api_key="your-key")
result = client.scrape.create(url_to_scrape="https://example.com")
# No explicit close needed for sync client
```

### Method Structure

The SDK provides a clean, Pythonic interface organized into logical namespaces:

| Namespace  | Purpose               | Key Methods                    |
| ---------- | --------------------- | ------------------------------ |
| `scrape`   | Single URL extraction | `create()`, `get()`            |
| `batch`    | Multi-URL processing  | `start()`, `info()`, `items()` |
| `crawl`    | Website traversal     | `start()`, `pages()`           |
| `sitemap`  | Link extraction       | `create()`, `urls()`           |
| `retrieve` | Content retrieval     | `get()`                        |

Each operation returns stateful objects with ergonomic methods for follow-up operations.

## Advanced Features

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

### Advanced Scraping Options

```python
# Full control over scraping behavior
result = await client.scrape.create(
    url_to_scrape="https://example.com",
    wait_before_scraping=3000,
    formats=[Format.HTML, Format.MARKDOWN],
    remove_css_selectors=["script", ".popup"],
    actions=[
        WaitAction(milliseconds=1500),
        FillInputAction(selector="searchbox", value="olostep")
    ],
    parser="@olostep/google-news",
    country=Country.US,
    remove_images=True
)
```

### Batch Processing with Custom IDs

```python
batch = await client.batch([
    {"url": "https://www.google.com/search?q=olostep", "custom_id": "news_1"},
    {"url": "https://www.google.com/search?q=olostep+api", "custom_id": "news_2"}
],
country=Country.US,
parser_id="@olostep/google-search"
)

# Process results by custom ID
async for item in batch.items():
    if item.custom_id == "news_2":
        content = await item.retrieve(["html"])
        print(f"News search: {len(content.html_content)} bytes")
```

### Intelligent Crawling

```python
# Crawl with intelligent filtering
crawl = await client.crawl.start(
    start_url="https://example.com",
    max_pages=1000,
    max_depth=3,
    include_urls=["/articles/**", "/news/**"],
    exclude_urls=["/ads/**", "/tracking/**"],
    include_external=False,
    include_subdomain=True,
)

async for page in crawl.pages():
    content = await page.retrieve(["html"])
    print(f"Crawled: {page.url}")
```

### Site Mapping with Filters

```python
# Extract all links with advanced filtering
sitemap = await client.sitemap.create(
    url_to_map="https://example.com",
    search_query="documentation",
    top_n=500,
    include_subdomain=True,
    include_urls=["/docs/**", "/api/**"],
    exclude_urls=["/admin/**", "/private/**"]
)

# Get filtered URLs
urls = []
async for url in sitemap.urls():
    urls.append(url)

print(f"Found {len(urls)} relevant URLs")
```

### Content Retrieval

```python
# Get content by retrieve ID
result = await client.retrieve.get(retrieve_id="ret_123")

# Get multiple formats
result = await client.retrieve.get(retrieve_id="ret_123", formats=["html", "markdown", "text", "json"])
```

## Error Handling

### Common Issues

#### Connection Errors

```python
# Enable detailed logging for debugging
import logging
logging.getLogger("olostep").setLevel(logging.DEBUG)

# Check your API key and network connectivity
try:
    result = await client.scrape.create(url_to_scrape="https://example.com")
except OlostepAPIConnectionError as e:
    print(f"Connection failed: {e}")
    # Check your API key and network
```

#### Rate Limiting

```python
# The SDK handles rate limiting automatically with exponential backoff
# Custom backoff for specific use cases:
import asyncio

async def scrape_with_backoff(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.scrape.create(url_to_scrape=url)
        except RateLimitError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise
```

### Getting Help

- [Full Documentation](https://docs.olostep.com)
- [Report Issues](https://github.com/olostep-api/olostep-py/issues/issues)
- [Community Slack](https://join.slack.com/t/olostep-users/shared_invite/zt-2pn2ce0uu-~591qIdhAfJy~LXCWQS5UQ)
- [Support Email](mailto:info@olostep.com)

## Contributing

We love contributions! Here's how you can help improve the Olostep Python SDK:

### Development Setup

```bash
git clone https://github.com/olostep-api/olostep-py/issues.git
cd olostep-python
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/

# DO NOT RUN THE API CONTRACT TEST!
```

### Code Style

```bash
# Format code
ruff format olostep/

# Lint code
ruff check olostep/
mypy olostep/
```

### Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-enhancement`)
3. Make your changes with comprehensive tests
4. Run the full test suite
5. Update documentation for API changes
6. Submit a pull request with a clear description

### Guidelines

- Follow PEP 8 and existing code style
- Add type hints for new functions
- Write comprehensive tests for new functionality
- Update documentation for API changes
- Use conventional commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ by the Olostep team**

</div>
