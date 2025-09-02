# Crawler API Implementation Plan

## 1. Understanding of BrightData Package Conventions

### Current Architecture
The BrightData SDK follows these key patterns:

1. **Service Structure**:
   - Each service (WebUnlocker, BrowserAPI, WebScraperAPI) has its own module
   - Services return standardized `ScrapeResult` objects
   - All services can be accessed through the unified `auto.py` interface

2. **Common Patterns**:
   ```python
   # Each service follows this pattern:
   - __init__() with credentials (from env or params)
   - sync methods that return results
   - async methods ending with _async
   - cost calculation built-in
   - error handling that always returns a result object
   ```

3. **Data Flow**:
   ```
   User → auto.py → Service → API → Result Object → User
   ```

### Key Components Analysis

#### ScrapeResult Model (models.py)
- Central data structure for all scraping operations
- Contains timing metadata, cost tracking, success status
- Has `save_data_to_file()` method for persistence
- Fields include: url, status, data, error, snapshot_id, cost, timestamps

#### Service Implementation Patterns

**WebUnlocker** (web_unlocker.py):
- Simple synchronous API calls
- Returns ScrapeResult immediately
- Cost calculation based on requests
- No polling required

**BrowserAPI** (browserapi/browser_api.py):
- Multiple strategies (noop, semaphore, pool)
- Cost based on data transfer (per GiB)
- Returns ScrapeResult with HTML data
- Supports both sync and async

**WebScraperAPI** (webscraper_api/):
- Complex with registry system
- Polling-based (async operations)
- Multiple scrapers registered by domain
- Returns structured data (JSON)

## 2. Crawler API Specifics

### What Makes Crawler API Different

1. **Two Distinct Operations**:
   - **Collect by URL**: Single/multiple URL extraction
   - **Discover by Domain**: Full domain crawling/mapping

2. **Multiple Output Formats**:
   - markdown (LLM-ready)
   - html2text (plain text)
   - page_html (full HTML)
   - ld_json (structured data)
   - page_title

3. **Crawling vs Scraping**:
   - Returns multiple pages/URLs from one request
   - Can filter/exclude URLs during crawl
   - Maps site structure (internal/external links)

## 3. Proposed Data Structure: CrawlResult

```python
@dataclass
class CrawlResult:
    # Core fields
    success: bool
    status: str  # "ready" | "error" | "timeout" | "in_progress"
    operation: str  # "collect" | "discover"
    
    # Input tracking
    input_url: str  # Original URL/domain
    input_urls: Optional[List[str]] = None  # For batch collect
    
    # Results
    pages: Optional[List[Dict[str, Any]]] = None  # List of page data
    total_pages: Optional[int] = None
    
    # Discover-specific
    internal_urls: Optional[List[str]] = None
    external_urls: Optional[List[str]] = None
    sitemap: Optional[Dict[str, Any]] = None
    
    # Metadata
    snapshot_id: Optional[str] = None
    cost: Optional[float] = None
    error: Optional[str] = None
    
    # Timing (following ScrapeResult pattern)
    request_sent_at: Optional[datetime] = None
    snapshot_id_received_at: Optional[datetime] = None
    snapshot_polled_at: List[datetime] = field(default_factory=list)
    data_received_at: Optional[datetime] = None
    
    # Filters applied
    filter: Optional[str] = None
    exclude_filter: Optional[str] = None
    
    # Statistics
    markdown_pages: int = 0
    html_pages: int = 0
    text_pages: int = 0
    json_ld_pages: int = 0
```

## 4. Implementation Plan for crawler_api.py

### Class Structure

```python
class CrawlerAPI:
    DATASET_ID = "gd_m6gjtfmeh43we6cqc"
    COST_PER_PAGE = 0.005  # Estimated, need to confirm
    
    def __init__(self, bearer_token=None):
        # Load from env or params
        
    def collect_by_url(self, urls: Union[str, List[str]], 
                       output_formats: List[str] = None) -> CrawlResult:
        # Collect specific URLs
        
    def discover_by_domain(self, domain: str, 
                           filter: str = None,
                           exclude_filter: str = None) -> CrawlResult:
        # Crawl entire domain
        
    async def collect_by_url_async(self, ...):
        # Async version
        
    async def discover_by_domain_async(self, ...):
        # Async version
        
    def poll_until_ready(self, snapshot_id: str) -> CrawlResult:
        # Poll for results
        
    async def poll_until_ready_async(self, snapshot_id: str) -> CrawlResult:
        # Async polling
```

### Integration Points

1. **With auto.py**:
   - Add crawler detection logic
   - Support fallback to crawler for unknown domains
   - Handle CrawlResult alongside ScrapeResult

2. **With models.py**:
   - Add CrawlResult class
   - Ensure compatibility with existing utilities

3. **Cost Calculation**:
   - Based on number of pages crawled
   - Different rates for collect vs discover?

## 5. Key Decisions Needed

1. **Output Format Selection**:
   - Should we default to all formats or let user choose?
   - How to handle format-specific fields in CrawlResult?

2. **URL vs Domain Detection**:
   - How to automatically detect if user wants collect vs discover?
   - Should `scrape_url()` automatically use crawler for unsupported domains?

3. **Result Structure**:
   - Keep pages as list of dicts or create Page dataclass?
   - How to handle very large crawls (thousands of pages)?

4. **Backward Compatibility**:
   - Should CrawlResult inherit from ScrapeResult?
   - Or keep them separate with a common interface?

## 6. Next Steps

1. ✅ Understand package structure
2. ✅ Design CrawlResult dataclass
3. 🔄 Create crawler_api.py with basic structure
4. ⏳ Implement collect_by_url method
5. ⏳ Implement discover_by_domain method
6. ⏳ Add polling functionality
7. ⏳ Integrate with auto.py
8. ⏳ Add tests
9. ⏳ Update README with Crawler API examples

## 7. Example Usage (Planned)

```python
from brightdata.crawlerapi import CrawlerAPI

# Initialize
crawler = CrawlerAPI()  # uses BRIGHTDATA_TOKEN from env

# Collect specific URLs
result = crawler.collect_by_url([
    "https://example.com/page1",
    "https://example.com/page2"
], output_formats=["markdown", "page_title"])

# Discover entire domain
result = crawler.discover_by_domain(
    "https://example.com",
    filter="/blog/*",
    exclude_filter="*/admin/*"
)

# Access results
for page in result.pages:
    print(f"{page['url']}: {page['page_title']}")
    print(page['markdown'][:500])  # First 500 chars

# Save all pages
result.save_all_pages(dir_="crawl_results/")
```

## 8. Questions for Consideration

1. Should we support streaming results for large crawls?
2. How to handle rate limiting and retries?
3. Should we provide built-in URL filtering utilities?
4. Do we need a separate registry for crawler-compatible domains?
5. How to handle authentication for protected sites?