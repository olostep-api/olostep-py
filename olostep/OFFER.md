# Partnership Proposal: First‑Class Python SDK for Olostep

We propose a trade: we build and maintain a public, first‑class Python SDK for Olostep, and in return receive API access.

## Benefits for you

- Free SDK and ongoing maintenance
- Fully typed Python SDK for fast, low‑friction developer integration
- Coding agents can autonomously integrate the SDK. They can not reliably with web APIs (not even with scraping, believe us, we tried).
- Free integration test suite for your API (single command: `pytest`)
- Continuous API feedback and improvement through real‑world usage and industry/customer insights

## Benefit for us

- Web data is one of the main inputs for our services at scailability.com, so this translates to straight money to us.

## API improvements (see README first)

During integration we observed several opportunities for refinement:
- Unexplained or under‑documented fields (e.g., llm, screenshot, text); not breaking, but clarity drives trust
- Pagination nuances on the `map` endpoint (behavior and shape could be clarified)
- Programmatic access to account credit/spend via the API would enable automated ops and alerting

We’re happy to share and collaborate on more points like these with you.

## SDK as a selling point

The current SDK mirrors the public docs and exposes endpoints exactly as documented. 

(Note: Read the README.md first if you have not done so, otherwise the following text will make little sense to you.)

To elevate the “programmatic access to the web” experience, we propose optional SDK‑level refinements (no API change required) that turn the SDK into a repository‑style interface over HTTP:

- Treat scraping as an implementation detail; assume data availability or fail fast
- Rename for brevity and Python conventions:
  - `client.scrape.get` → not exposed (retrieval goes via `retrieve`)
  - `client.scrape.url(url_to_scrape)` → `client.scrape(url)`
  - `client.batch.start(items, country, parser_id)` → `client.batch(items, country, parser_id)`
  - `client.crawl.start(start_url, ...)` → `client.crawl(...)`
  - `client.map.create(url, ...)` → `client.sitemap(url, ...)` (avoid reserved `map` in Python)
  - `client.retrieve.get(retrieve_id, formats)` → `client.retrieve(retrieve_id, formats)`
- All beta features emit a warning unless explicitly suppressed
- Search API lives under `client.beta.google` and `client.beta.bing`

This would allow calling code to look like:

```python

async with AsyncOlostepClient(api_key="...") as client:
    # Proposed repository-like SDK
    crawl: CrawlInfo = await client.crawl(
        start_url="https://example.com",
        max_pages=500,
        include_subdomain=True,
        include_urls=["/**"],
    )
    results = []
    crawl_done: bool = await crawl.wait_till_done(check_every_n_secs=30) # new feature in addition to webhook
    if crawl_done:
        pages = await crawl.pages(limit=100)
        while pages:
            for page in pages:  # page: CrawlPage; pages is a CrawlPages object allowing direct iteration
                result = await page.retrieve("html")  # CrawlPage knows how to get the result. accepts strings list of strings (DX)
                print(page.url, page.is_external, len(result.html_content))
                results.append(page)
            pages = await pages.next(limit=100)
```

These changes make the SDK feel like a true “programmatic layer to the web,” with minimal ceremony and excellent editor DX.

## Cooperation models

- Offer 1
  - We generalize and share our internal SDK in a shared GitHub repo
  - You own PyPI setup and publishing
  - We maintain for the duration of a free Scale account

- Offer 2
  - Same as Offer 1, plus: we manage PyPI publishing and Sentry customer error tracking (yours or ours)
  - We maintain for the duration of a fully open account (< 10M requests/month)

## Timeline

- We can deliver a publish‑ready version by end of August ’25 (≈ two weeks)

---

Questions or ideas? Message Fred: fred@hyperlace.io