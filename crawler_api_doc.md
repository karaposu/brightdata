# BrightData Crawler API Documentation

## Overview

The BrightData Crawler API is a powerful web crawling and content extraction service that can transform any website into structured, LLM-ready data. It provides two main operations: collecting specific URLs and discovering entire domains.

**Dataset ID:** `gd_m6gjtfmeh43we6cqc`  
**Base URL:** `https://api.brightdata.com/datasets/v3`

## Key Features

- **Multiple Output Formats**: Markdown, HTML, plain text, JSON-LD
- **Domain Discovery**: Automatically crawl and map entire websites
- **Smart Filtering**: Include/exclude patterns for precise crawling
- **LLM-Optimized**: Clean markdown output perfect for AI training
- **Depth Control**: Limit crawl depth for targeted extraction
- **Sitemap Support**: Can utilize or ignore sitemap.xml

## API Endpoints

### 1. Trigger Endpoint
**POST** `https://api.brightdata.com/datasets/v3/trigger`

Initiates a crawl operation and returns a snapshot ID for polling.

**Headers:**
```
Authorization: Bearer <your_token>
Content-Type: application/json
```

**Query Parameters:**
```
dataset_id: gd_m6gjtfmeh43we6cqc
include_errors: true/false
```

## Operations

### Operation 1: Collect by URL

Collects content from specific URLs you provide.

**Request Body:**
```json
[
  {
    "url": "https://example.com/page1"
  },
  {
    "url": "https://example.com/page2"
  }
]
```

**Parameters per URL:**
- `url` (required): The URL to collect

**Use Cases:**
- Collecting specific pages
- Batch processing known URLs
- Targeted content extraction

### Operation 2: Discover by Domain

Crawls an entire domain to discover and extract all pages.

**Request Body:**
```json
[
  {
    "url": "https://example.com",
    "filter": "/blog/*",
    "exclude_filter": "/admin/*",
    "depth": 3,
    "ignore_sitemap": false
  }
]
```

**Parameters:**
- `url` (required): The domain to crawl
- `filter` (optional): Include only URLs matching this pattern
- `exclude_filter` (optional): Exclude URLs matching this pattern
- `depth` (optional): Maximum crawl depth from the starting URL
- `ignore_sitemap` (optional): Whether to ignore sitemap.xml (boolean)

**Additional Query Parameters for Discover:**
```
type: discover_new
discover_by: domain_url
```

**Use Cases:**
- Site mapping and analysis
- Full website backup
- Content migration
- Training data collection

## Response Structure

### Initial Response

Both operations return a snapshot ID immediately:

```json
{
  "snapshot_id": "s_abc123xyz789"
}
```

### Polling for Results

**GET** `https://api.brightdata.com/datasets/v3/progress/{snapshot_id}`

Returns the status of your crawl:

```json
{
  "status": "running|ready|failed",
  "snapshot_id": "s_abc123xyz789",
  "dataset_id": "gd_m6gjtfmeh43we6cqc",
  "records": 10,
  "errors": 0,
  "collection_duration": 5094
}
```

### Retrieving Data

**GET** `https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json`

## Data Structure

Each crawled page returns the following structure:

```json
{
  "url": "https://example.com/page",
  "markdown": "# Page Title\n\nContent in markdown format...",
  "html2text": "PAGE TITLE\n\nContent in plain text...",
  "page_html": "<!DOCTYPE html><html>...</html>",
  "page_title": "Page Title",
  "ld_json": null,
  "timestamp": "2025-08-26T14:33:20.142Z",
  "input": {
    "url": "https://example.com/page"
  },
  "discovery_input": {
    "url": "https://example.com",
    "filter": "/blog/*",
    "exclude_filter": "/admin/*"
  }
}
```

### Field Descriptions

| Field | Type | Description | Availability |
|-------|------|-------------|--------------|
| `url` | string | The URL of the crawled page | Always |
| `markdown` | string | Content in Markdown format with preserved formatting | ~95% |
| `html2text` | string | Plain text with all HTML stripped | ~90% |
| `page_html` | string | Complete HTML source code | ~95% |
| `page_title` | string/null | HTML title tag content | ~70% |
| `ld_json` | object/null | JSON-LD structured data (schema.org) | ~5% |
| `timestamp` | string | ISO timestamp of when page was crawled | Always |
| `input` | object | Original request parameters | Always |
| `discovery_input` | object | Discovery parameters (only in discover operations) | Discover only |

## Parameter Patterns

### Filter Patterns

Filters use glob-style pattern matching:

- `/blog/*` - All URLs under /blog/
- `*/page-*.html` - All HTML pages with "page-" prefix
- `/category/*/product/*` - Nested path matching
- `*.pdf` - All PDF files

### Exclude Patterns

Same syntax as filters but for exclusion:

- `/admin/*` - Skip admin pages
- `*/private/*` - Skip private directories
- `*.zip` - Skip ZIP files

### Depth Control

Depth represents how many levels deep from the starting URL to crawl:

- `depth: 0` - Only the exact URL
- `depth: 1` - URL + all directly linked pages
- `depth: 2` - URL + linked pages + their linked pages
- `depth: null` - No limit (crawl entire domain)

## Best Practices

### 1. Optimal Polling Intervals

- **Collect operations**: Poll every 5-10 seconds
- **Discover operations**: Poll every 10-20 seconds
- **Large domains**: Consider 30-60 second intervals

### 2. Timeout Recommendations

- **Single URL**: 60-120 seconds
- **Batch collect (5-10 URLs)**: 180 seconds
- **Small domain discover**: 300 seconds
- **Large domain discover**: 600-1200 seconds

### 3. Filter Strategies

**Focused Crawling:**
```json
{
  "filter": "/docs/*",
  "exclude_filter": "/docs/archive/*"
}
```

**Avoid Media Files:**
```json
{
  "exclude_filter": "*.jpg|*.png|*.mp4|*.pdf"
}
```

**Language-Specific:**
```json
{
  "filter": "/en/*",
  "exclude_filter": "/*/drafts/*"
}
```

### 4. Depth Optimization

- **Documentation sites**: `depth: 2-3` usually sufficient
- **E-commerce**: `depth: 3-4` for category/product structure
- **Blogs**: `depth: 2` for posts and comments
- **Corporate sites**: `depth: 2` for main content

## Use Cases

### 1. LLM Training Data Collection

```json
{
  "url": "https://docs.example.com",
  "filter": "/api/*",
  "depth": 3
}
```
Output: Clean markdown perfect for training

### 2. Website Migration

```json
{
  "url": "https://oldsite.com",
  "depth": null,
  "ignore_sitemap": false
}
```
Output: Complete site structure with all content

### 3. Competitive Analysis

```json
{
  "url": "https://competitor.com",
  "filter": "/products/*",
  "exclude_filter": "*/reviews/*",
  "depth": 2
}
```
Output: Product pages without review clutter

### 4. Documentation Extraction

```json
{
  "url": "https://docs.service.com",
  "filter": "/v3/*",
  "exclude_filter": "*/changelog/*",
  "depth": 4
}
```
Output: Current version docs only

## Rate Limits & Costs

- **Concurrent requests**: Recommended max 5-10
- **Pages per minute**: Varies by site complexity
- **Cost model**: Per-page pricing (check BrightData dashboard)

## Error Handling

Common status codes and their meanings:

| Status | Meaning | Action |
|--------|---------|--------|
| `ready` | Crawl complete | Retrieve data |
| `running` | Still crawling | Continue polling |
| `failed` | Crawl failed | Check error details |
| `timeout` | Took too long | Retry with smaller scope |

## Advanced Features

### Sitemap Utilization

When `ignore_sitemap: false` (default), the crawler:
1. Checks for sitemap.xml
2. Uses it to discover URLs efficiently
3. Respects sitemap priorities
4. Falls back to link discovery if no sitemap

### Content Deduplication

The API automatically:
- Detects duplicate content
- Canonicalizes URLs
- Removes redundant pages
- Maintains unique content only

### JavaScript Rendering

The crawler handles:
- SPAs (Single Page Applications)
- Dynamic content loading
- JavaScript-generated links
- AJAX-loaded content

## Output Format Examples

### Markdown (Best for LLMs)
```markdown
# Example Page

This is the main content with **formatting preserved**.

## Section Header

- Bullet points maintained
- Links converted to [markdown links](url)
- Tables converted to markdown tables
```

### HTML2Text (Plain Text)
```
EXAMPLE PAGE

This is the main content with formatting preserved.

SECTION HEADER

* Bullet points maintained
* Links converted to markdown links [url]
* Tables converted to markdown tables
```

### Page HTML (Complete Source)
Full HTML including scripts, styles, and all tags.

## Comparison with Other BrightData Services

| Feature | Crawler API | Web Scraper API | Browser API | Web Unlocker |
|---------|------------|----------------|-------------|--------------|
| Purpose | Crawl & extract | Structured data | Automation | Proxy service |
| Output | Multiple formats | JSON only | HTML | HTML |
| Discovery | Yes | No | No | No |
| JavaScript | Yes | Yes | Yes | Partial |
| Filtering | Advanced | Limited | No | No |
| Best for | LLM data, migration | Specific sites | Complex interaction | Simple HTML |

## Limitations

1. **URL Limits**: Recommended max 10,000 pages per crawl
2. **Depth Limits**: Practical max depth is 5-6 levels
3. **File Types**: Focuses on HTML, may skip binaries
4. **Rate Limiting**: Respects robots.txt and rate limits
5. **Authentication**: No support for logged-in areas

## Tips for Success

1. **Start Small**: Test with limited depth/filters first
2. **Use Filters**: More precise = faster & cheaper
3. **Monitor Progress**: Poll regularly to catch issues early
4. **Save Snapshots**: Store snapshot IDs for re-retrieval
5. **Batch Wisely**: Group related URLs in single requests

## Example Workflows

### Simple Collection
```python
# 1. Trigger collection
POST /trigger with URLs

# 2. Get snapshot_id
{"snapshot_id": "s_xxx"}

# 3. Poll until ready
GET /progress/s_xxx

# 4. Retrieve data
GET /snapshot/s_xxx?format=json
```

### Domain Discovery
```python
# 1. Trigger discovery with filters
POST /trigger with domain + filters

# 2. Poll (longer timeout)
GET /progress/s_xxx (every 20s)

# 3. Process pages
Parse markdown for LLM training
```

## Support

- **Documentation**: This document
- **Dataset ID**: `gd_m6gjtfmeh43we6cqc`
- **API Base**: `https://api.brightdata.com/datasets/v3`
- **Authentication**: Bearer token in header