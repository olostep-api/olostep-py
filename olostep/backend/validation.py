"""
Olostep API Models (Pydantic validation layer).

Models are organized by:
1. Common/Shared models (enums, base types)
2. Endpoint-specific models grouped by endpoint
3. Each endpoint group: config → request → response
"""

from __future__ import annotations

import json
from typing import Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# =============================================================================
# COMMON/SHARED MODELS
# =============================================================================

class Country(str, Enum):
    """Country codes for geolocation."""
    US = "US"
    CA = "CA"
    IT = "IT"
    IN = "IN"
    GB = "GB"
    JP = "JP"
    MX = "MX"
    AU = "AU"
    ID = "ID"
    UA = "UA"
    RU = "RU"
    RANDOM = "RANDOM"

class Format(str, Enum):
    """Output formats for scraping."""
    HTML = "html"
    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"
    RAW_PDF = "raw_pdf"

class RetrieveFormat(str, Enum):
    """Output formats for retrieve content endpoint."""
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"

class Status(str, Enum):
    """Common status values."""
    IN_PROGRESS = "in_progress"  # API returns this for active batches
    COMPLETED = "completed"      # API returns this when batch is done

class RemoveCssSelectorsMode(str, Enum):
    """Modes for CSS selector removal."""
    DEFAULT = "default"
    NONE = "none"

class RemoveCssSelectorsConfig(BaseModel):
    """Configuration for CSS selector removal.
    
    Supports three modes:
    - default: Uses predefined selectors ['nav','footer','script','style','noscript','svg',[role=alert],[role=banner],[role=dialog],[role=alertdialog],[role=region][aria-label*=skip i],[aria-modal=true]]
    - none: Don't remove any selectors
    - array: Custom array of selectors (JSON stringified)
    """
    mode: RemoveCssSelectorsMode | None = None
    custom_selectors: list[str] | None = None
    
    @field_validator('custom_selectors', mode='before')
    @classmethod
    def validate_custom_selectors(cls, v):
        """Validate custom selectors if provided."""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("custom_selectors must be a list of strings")
            if not all(isinstance(selector, str) for selector in v):
                raise ValueError("All custom selectors must be strings")
        return v
    
    @model_validator(mode='after')
    def validate_configuration(self):
        """Validate that either mode OR custom_selectors is provided, not both."""
        has_mode = self.mode is not None
        has_custom = self.custom_selectors is not None
        
        if has_mode and has_custom:
            raise ValueError("Cannot specify both mode and custom_selectors. Use either mode OR custom_selectors.")
        
        return self
    
    def to_api_value(self) -> str | None:
        """Convert to the format expected by the API."""
        if self.mode is not None:
            return self.mode.value
        elif self.custom_selectors is not None:
            return json.dumps(self.custom_selectors)
        return None
    
    @classmethod
    def from_api_value(cls, value: str | None) -> 'RemoveCssSelectorsConfig':
        """Create from API value."""
        if value is None:
            return cls()
        
        if value in [mode.value for mode in RemoveCssSelectorsMode]:
            return cls(mode=RemoveCssSelectorsMode(value))
        
        # Try to parse as JSON array
        try:
            selectors = json.loads(value)
            if isinstance(selectors, list) and all(isinstance(s, str) for s in selectors):
                return cls(custom_selectors=selectors)
        except (json.JSONDecodeError, TypeError):
            pass
        
        raise ValueError(f"Invalid remove_css_selectors value: {value}")

# =============================================================================
# SCRAPES API MODELS
# =============================================================================

# Scrapes - Config Models
class ActionType(str, Enum):
    """Types of actions that can be performed on a page."""
    WAIT = "wait"
    CLICK = "click"
    FILL_INPUT = "fill_input"
    SCROLL = "scroll"

class ScrollDirection(str, Enum):
    """Scroll directions."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

class ScreenType(str, Enum):
    """Screen type presets."""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    DEFAULT = "default"

class WaitAction(BaseModel):
    """Wait action configuration."""
    type: ActionType = ActionType.WAIT
    milliseconds: int

class ClickAction(BaseModel):
    """Click action configuration."""
    type: ActionType = ActionType.CLICK
    selector: str

class FillInputAction(BaseModel):
    """Fill input action configuration."""
    type: ActionType = ActionType.FILL_INPUT
    selector: str
    value: str

class ScrollAction(BaseModel):
    """Scroll action configuration."""
    type: ActionType = ActionType.SCROLL
    direction: ScrollDirection
    amount: int

# Union type for all actions
Action = WaitAction | ClickAction | FillInputAction | ScrollAction

class ParserType(str, Enum):
    """Available parser types for Olostep search API."""
    # Technically there's more but this is beta and i don't want to spend more time on it. 
    # These are the ones once can care about.
    GOOGLE_SHORTS = "google-shorts"
    GOOGLE_VIDEOS = "google-videos"
    GOOGLE_SHOPPING = "google-shopping"
    GOOGLE_NEWS = "google-news"
    GOOGLE_MAPS = "google-maps"
    GOOGLE_AI_OVERVIEW = "google-ai-overview"
    GOOGLE_ADVANCED_SEARCH = "google-advanced-search"
    GOOGLE_SEARCH = "google-search"

class ParserConfig(BaseModel):
    """Parser configuration."""
    id: str = "default"
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_parser_id(cls, v):
        """Validate parser ID format."""
        if v == "default":
            return v
        
        # Check if it's a valid parser type
        if v in [parser.value for parser in ParserType]:
            return f"@olostep/{v}"
        
        # If it already has the @olostep/ prefix, validate the suffix
        if v.startswith("@olostep/"):
            suffix = v[9:]  # Remove "@olostep/"
            if suffix in [parser.value for parser in ParserType]:
                return v
        
        # Allow custom parser IDs
        return v
    
    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Custom serialization to handle default parser."""
        kwargs["exclude_none"] = True
        data = super().model_dump(**kwargs)
        
        # If the parser ID is "default", exclude it entirely
        if data.get("id") == "default":
            return {}
        
        return data

class LLMExtractConfig(BaseModel):
    """LLM extraction configuration."""
    extraction_schema: dict[str, Any] = Field(alias="schema")

class LinksOnPageConfig(BaseModel):
    """
    Configuration for extracting links from a scraped page.

    With this option, you can get all the links present on the page you scrape.

    Note: The behavior for conflicting include_links and exclude_links patterns is undefined and may change in future versions.
    If both are provided and a link matches both, the result is not guaranteed. 
    Similarly, if query_to_order_links_by is provided but no links match, the ordering is undefined.

    Attributes
    ----------
    absolute_links : bool, default True
        When True, returns complete URLs (e.g., 'https://example.com/page') instead of relative paths (e.g., '/page').
        If False, relative paths are returned as-is. If the page uses unusual base tags or JavaScript navigation, results may be unpredictable.

    query_to_order_links_by : str | None
        Orders the returned links by their similarity to the provided query text, prioritizing the most relevant matches first.
        If not provided, links are returned in the order found on the page. If the query is provided but no links are similar, the ordering is undefined.

    include_links : list[str] | None
        Filter extracted links using glob patterns. Use patterns like ".pdf" to match file extensions, "/blog/" for specific paths, or full URLs like "https://example.com/".
        Supports wildcards (*), character classes ([a-z]), and alternation ({pattern1,pattern2}).
        If not provided, all links are included unless excluded by exclude_links.

    exclude_links : list[str] | None
        Filter extracted links using glob patterns. Use patterns like ".pdf" to match file extensions, "/blog/" for specific paths, or full URLs like "https://example.com/".
        Supports wildcards (*), character classes ([a-z]), and alternation ({pattern1,pattern2}).
        If not provided, no links are excluded unless filtered by include_links.

    Undefined Behavior
    -----------------
    - If a link matches both include_links and exclude_links, the result is undefined.
    - If query_to_order_links_by is provided but no links match, the returned order is undefined.
    - If the page contains malformed or JavaScript-generated links, extraction may be incomplete or inconsistent.
    """
    absolute_links: bool = True
    query_to_order_links_by: str | None = None
    include_links: list[str] | None = None
    exclude_links: list[str] | None = None

class ScreenSizeConfig(BaseModel):
    """Browser viewport configuration for screenshots.
    
    Supports both preset screen types and custom dimensions:
    - desktop: 1920x1080 pixels
    - mobile: 414x896 pixels  
    - default: 768x1024 pixels
    
    Can also use custom width/height values.
    """
    screen_type: ScreenType | None = None
    screen_width: int | None = None
    screen_height: int | None = None
    
    @field_validator('screen_type', 'screen_width', 'screen_height', mode='before')
    @classmethod
    def validate_screen_config(cls, v, info):
        """Validate screen configuration."""
        if info.field_name == 'screen_type' and v is not None:
            # Validate screen type
            if v not in ScreenType:
                raise ValueError(f"Invalid screen_type: {v}. Must be one of: {list(ScreenType)}")
        
        elif info.field_name in ('screen_width', 'screen_height') and v is not None:
            # Validate dimensions
            if not isinstance(v, int) or v <= 0:
                raise ValueError(f"{info.field_name} must be a positive integer")
            if v > 10000:  # Reasonable max dimension
                raise ValueError(f"{info.field_name} cannot exceed 10000 pixels")
        
        return v
    
    @model_validator(mode='after')
    def validate_screen_config_combination(self):
        """Validate that either screen_type OR custom dimensions are provided, not both."""
        has_screen_type = self.screen_type is not None
        has_custom_dimensions = self.screen_width is not None or self.screen_height is not None
        
        if has_screen_type and has_custom_dimensions:
            raise ValueError("Cannot specify both screen_type and custom dimensions. Use either screen_type OR screen_width/screen_height.")
        
        if has_custom_dimensions and (self.screen_width is None or self.screen_height is None):
            raise ValueError("Both screen_width and screen_height must be provided when using custom dimensions.")
        
        return self

# Scrapes - Request Models
class CreateScrapeRequest(BaseModel):
    """Request to create a new scrape."""
    model_config = ConfigDict(extra='forbid')
    
    url_to_scrape: str
    wait_before_scraping: int | None = None
    formats: list[Format] | None = None
    remove_css_selectors: RemoveCssSelectorsConfig | None = None
    actions: list[Action] | None = None
    country: Country | None = None
    transformer: str | None = None
    remove_images: bool = False
    remove_class_names: list[str] | None = None
    parser: ParserConfig | None = None
    llm_extract: LLMExtractConfig | None = None
    links_on_page: LinksOnPageConfig | None = None
    screen_size: ScreenSizeConfig | None = None
    metadata: dict[str, Any] | None = None # Docs mention that this is not yet supported
    
    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Custom serialization to handle special fields."""
        kwargs["exclude_none"] = True
        data = super().model_dump(**kwargs)
        
        # Convert RemoveCssSelectorsConfig to API format
        if 'remove_css_selectors' in data and isinstance(self.remove_css_selectors, RemoveCssSelectorsConfig):
            data['remove_css_selectors'] = self.remove_css_selectors.to_api_value()
        
        # Handle ParserConfig serialization
        if 'parser' in data and isinstance(self.parser, ParserConfig):
            parser_data = self.parser.model_dump()
            if parser_data:  # Only include if not empty
                data['parser'] = parser_data
            else:
                del data['parser']  # Remove if empty
        
        return data

# Unified result model for both create/get scrape responses.
# Fields are optional when the corresponding content was not requested,
# not generated, or offloaded to hosted URLs due to size constraints.
class ScrapeResult(BaseModel):
    model_config = ConfigDict(extra='forbid')

    html_content: str | None = None
    markdown_content: str | None = None
    text_content: str | None = None
    json_content: dict[str, Any] | None = None

    # Not documented, but they are there
    screenshot_hosted_url: str | None = None # Beta feature
    llm_extract: dict[str, Any] | None = None
    network_calls: list[dict[str, Any]] | None = None

    links_on_page: list[str] | None = None
    page_metadata: dict[str, Any] | None = None

    html_hosted_url: str | None = None
    markdown_hosted_url: str | None = None
    json_hosted_url: str | None = None
    text_hosted_url: str | None = None

    size_exceeded: bool | None = None

# Scrapes - Response Models
class CreateScrapeResponse(BaseModel):
    """Response from POST /scrapes (create scrape)."""
    model_config = ConfigDict(extra='forbid')
    id: str
    object: str = "scrape"
    created: int
    metadata: dict[str, Any] | None = None
    retrieve_id: str | None = None
    url_to_scrape: str
    result: ScrapeResult

class GetScrapeResponse(BaseModel):
    """Response from GET /scrapes/{id} (get scrape)."""
    model_config = ConfigDict(extra='forbid')
    id: str
    object: str = "scrape"
    created: int
    metadata: dict[str, Any] | None = None # user defined metadata
    retrieve_id: str | None = None
    url_to_scrape: str
    result: ScrapeResult

# =============================================================================
# BATCHES API MODELS
# =============================================================================

# Batches - Config Models
class CreateBatchRequestItem(BaseModel):
    """Individual item in a batch."""
    url: str
    custom_id: str | None = None


class CreateBatchRequest(BaseModel):
    """Request to create a new batch."""
    model_config = ConfigDict(extra='forbid')
    
    items: list[CreateBatchRequestItem]
    country: Country | None = None
    parser: ParserConfig | None = None

    @field_validator("items")
    @classmethod
    def items_must_not_be_empty(cls, v: list[CreateBatchRequestItem]) -> list[CreateBatchRequestItem]:
        if not v:
            raise ValueError("items must not be empty")
        return v
    
    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Custom serialization to remove empty keys."""
        kwargs["exclude_none"] = True
        data = super().model_dump(**kwargs)
        
        # Handle ParserConfig serialization
        if 'parser' in data and isinstance(self.parser, ParserConfig):
            parser_data = self.parser.model_dump()
            if parser_data:  # Only include if not empty
                data['parser'] = parser_data
            else:
                del data['parser']  # Remove if empty
        
        return data

# Batches - Response Models
class BatchCreateResponse(BaseModel):
    """Response from POST /batches (create batch)."""
    model_config = ConfigDict(extra='forbid')
    
    id: str
    object: str = "batch"
    status: Status
    created: int # unix timestamp
    total_urls: int
    completed_urls: int
    parser: ParserConfig
    country: Country


class BatchInfoResponse(BaseModel):
    """Response from GET /batches/{id} (get batch info)."""
    model_config = ConfigDict(extra='forbid')
    
    id: str
    batch_id: str
    object: str = "batch"
    status: Status
    created: int
    total_urls: int
    completed_urls: int
    number_retried: int
    parser: str
    start_date: str


class BatchItemsResponseListItem(BaseModel):
    """Basic batch item info from GET /batches/{id}/items."""
    custom_id: str | None = None
    retrieve_id: str
    url: str


class BatchItemsResponse(BaseModel):
    """Response from get batch items."""
    model_config = ConfigDict(extra='forbid')
    
    batch_id: str
    object: str = "batch"
    status: Status
    items: list[BatchItemsResponseListItem]
    items_count: int
    cursor: int | None = None

# =============================================================================
# CRAWLS API MODELS
# =============================================================================

# Crawls - Request Models
class CreateCrawlRequest(BaseModel):
    """Request to create a new crawl."""
    model_config = ConfigDict(extra='forbid')
    
    start_url: str
    max_pages: int
    include_urls: list[str] = ["/**"]
    exclude_urls: list[str] | None = None
    max_depth: int | None = None
    include_external: bool = False
    include_subdomain: bool = False
    search_query: str | None = None
    top_n: int | None = None
    webhook_url: str | None = None
    
    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Custom serialization to remove empty keys."""
        kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)

# Crawls - Response Models
class CreateCrawlResponse(BaseModel):
    """Response from POST /v1/crawls (create crawl)."""
    model_config = ConfigDict(extra='forbid')
    
    id: str
    object: str = "crawl"
    status: Status
    created: int
    start_date: str
    start_url: str
    max_pages: int
    max_depth: int | None = None
    exclude_urls: list[str] | None = None
    include_urls: list[str]
    include_external: bool
    search_query: str | None = None
    top_n: int | None = None
    current_depth: int | None = None
    pages_count: int
    webhook_url: str | None = None

# For GET /v1/crawls/{id}
class CrawlInfoResponse(CreateCrawlResponse):
    """Response from GET /v1/crawls/{id} (crawl info)."""
    pass

class CrawlPagesResponseListItem(BaseModel):
    """Item returned by GET /v1/crawls/{crawl_id}/pages."""
    id: str
    retrieve_id: str
    url: str
    is_external: bool

class CrawlPagesResponseMetadata(BaseModel):
    """Metadata for crawl pages response."""
    external_urls: list[str]
    failed_urls: list[str]

    model_config = ConfigDict(extra='allow')

class CrawlPagesResponse(BaseModel):
    """Response from get crawl pages."""
    model_config = ConfigDict(extra='forbid')

    crawl_id: str
    object: str = "crawl"
    status: Status
    search_query: str | None = None
    pages_count: int
    pages: list[CrawlPagesResponseListItem]
    metadata: CrawlPagesResponseMetadata
    cursor: int | None = None

# =============================================================================
# MAPS API MODELS
# =============================================================================

# Maps - Request Models
class CreateMapRequest(BaseModel):
    """Request to create a new map (extract links from a website).
    
    The maps endpoint extracts links from a single website using glob syntax patterns.
    
    Filter Behavior:
    - include_urls: Only URLs matching these patterns will be returned
    - exclude_urls: Excluded URLs will supersede included URLs
    - Subpaths of allowed paths are included (e.g., if /sport/** is included, 
      /sport/cricket/** will also be included even if not explicitly listed)
    - Redundant patterns are handled gracefully (e.g., /sport/** and /sport/football/** 
      where football is already covered by the broader sport pattern)
    - Exclude filters work best when combined with include filters rather than used alone
    - When using exclude filters only, add include_urls=["/**"] to explicitly include all URLs
      (this matches the default behavior and prevents 404 errors)
    """
    model_config = ConfigDict(extra='forbid')
    
    url: str
    search_query: str | None = None
    top_n: int | None = None
    include_subdomain: bool = True
    include_urls: list[str] | None = None
    exclude_urls: list[str] | None = None
    cursor: str | None = None
    
    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Custom serialization to remove empty keys."""
        kwargs["exclude_none"] = True
        data = super().model_dump(**kwargs)
        
        # Handle ParserConfig serialization (if we had one, but we don't need it)
        return data

# Maps - Response Models
class MapResponse(BaseModel):
    """Response from create map (link extraction)."""
    model_config = ConfigDict(extra='forbid')
    
    urls_count: int
    urls: list[str]
    id: str | None = None
    cursor: str | None = None # according to the docs, this is the cursor is set if the response contains more then 100k urls / 10MB

# =============================================================================
# RETRIEVE API MODELS
# =============================================================================

class RetrieveRequest(BaseModel):
    """Request for GET /v1/retrieve (query params)."""
    model_config = ConfigDict(extra='forbid')
    retrieve_id: str
    formats: list[RetrieveFormat]

class RetrieveResponse(BaseModel):
    """Response from retrieve content (GET /v1/retrieve)."""
    model_config = ConfigDict(extra='forbid')

    html_content: str | None = None
    markdown_content: str | None = None
    json_content: str | None = None
    html_hosted_url: str | None = None
    markdown_hosted_url: str | None = None
    json_hosted_url: str | None = None
    size_exceeded: bool = False 

    success: bool | None = None # not documented, but it's here
    network_calls: Any | None = None # not documented, but it's here 