# BrightData SDK Refactoring Plan

## Overview

Reorganize the BrightData SDK to clearly separate the three main services while keeping auto-detection at the root level.

## Proposed Structure

```
brightdata/
├── __init__.py                    # Main package exports
├── auto.py                        # Auto-detection (generic, works across all services)
├── models.py                      # Shared data models (ScrapeResult, etc.)
├── catalog.py                     # Catalog functionality
├── webunlocker.py                 # Web Unlocker (rename from brightdata_web_unlocker.py)
│
├── browserapi/                    # Browser API module
│   ├── __init__.py               # Exports BrowserAPI
│   ├── browser_api.py            # Main BrowserAPI class (keep original name)
│   ├── browserapi_engine.py      # BrowserapiEngine (keep original name)
│   ├── browser_pool.py           # BrowserPool (keep original name)
│   ├── browser_config.py         # BrowserConfig (keep original name)
│   ├── playwright_session.py     # PlaywrightSession (keep original name)
│   └── browser_api_variants/     # Keep variants folder as-is
│
├── webscraper_api/               # Web Scraper API module
│   ├── __init__.py              # Exports base scraper and registry
│   ├── base_specialized_scraper.py  # Keep original name
│   ├── registry.py              # Registry system
│   ├── engine.py                # Engine
│   ├── scrapers/                # All ready-made scrapers (rename from ready_scrapers)
│   │   ├── __init__.py
│   │   ├── amazon/              # Keep folder structure
│   │   │   ├── __init__.py
│   │   │   └── scraper.py
│   │   ├── linkedin/
│   │   │   ├── __init__.py
│   │   │   └── scraper.py
│   │   └── ...                  # Other scrapers
│   ├── planned_scrapers/        # Keep as-is
│   └── utils/                   # Scraper-specific utilities
│       ├── __init__.py
│       ├── poll.py
│       ├── async_poll.py
│       └── ...
│
└── deprecated/                   # Old/deprecated files
```

## Key Refactoring Tasks

### 1. File Moves and Renames

```bash
# Rename Web Unlocker
mv brightdata/brightdata_web_unlocker.py brightdata/webunlocker.py

# Create browserapi folder and move files
mkdir brightdata/browserapi
mv brightdata/browser_api.py brightdata/browserapi/
mv brightdata/browserapi_engine.py brightdata/browserapi/
mv brightdata/browser_pool.py brightdata/browserapi/
mv brightdata/browser_config.py brightdata/browserapi/
mv brightdata/playwright_session.py brightdata/browserapi/
mv brightdata/browser_api_variants/ brightdata/browserapi/

# Create webscraper_api folder and move files
mkdir brightdata/webscraper_api
mv brightdata/base_specialized_scraper.py brightdata/webscraper_api/
mv brightdata/registry.py brightdata/webscraper_api/
mv brightdata/engine.py brightdata/webscraper_api/
mv brightdata/ready_scrapers brightdata/webscraper_api/scrapers
mv brightdata/planned_scrapers brightdata/webscraper_api/
mv brightdata/utils brightdata/webscraper_api/

# Move deprecated files
mkdir brightdata/deprecated
mv brightdata/old_*.py brightdata/deprecated/
```

### 2. Import Updates

#### brightdata/__init__.py
```python
# Old imports
from .brightdata_web_unlocker import BrightdataWebUnlocker
from .base_specialized_scraper import BrightdataBaseSpecializedScraper
from .auto import scrape_url, scrape_url_async, scrape_urls, scrape_urls_async
from .browser_api import BrowserAPI

# New imports
from .webunlocker import WebUnlocker
from .browserapi import BrowserAPI
from .webscraper_api import BaseSpecializedScraper
from .auto import scrape_url, scrape_url_async, scrape_urls, scrape_urls_async
```

#### brightdata/browserapi/__init__.py
```python
from .browser_api import BrowserAPI
from .browser_pool import BrowserPool
from .browser_config import BrowserConfig

__all__ = ['BrowserAPI', 'BrowserPool', 'BrowserConfig']
```

#### brightdata/webscraper_api/__init__.py
```python
from .base_specialized_scraper import BrightdataBaseSpecializedScraper
from .registry import register, get_scraper_for
from .engine import get_engine

# Import all scrapers to trigger registration
from .scrapers import *

__all__ = ['BrightdataBaseSpecializedScraper', 'register', 'get_scraper_for']
```

### 3. Update Internal Imports

#### In auto.py
```python
# Old
from brightdata.browser_api import BrowserAPI
from brightdata.browser_pool import BrowserPool
from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
from brightdata.registry import get_scraper_for

# New
from brightdata.browserapi import BrowserAPI, BrowserPool
from brightdata.webunlocker import WebUnlocker
from brightdata.webscraper_api import get_scraper_for
```

#### In scrapers (e.g., amazon/scraper.py)
```python
# Old
from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# New
from brightdata.webscraper_api import BrightdataBaseSpecializedScraper, register
```

### 4. Class Renames

- `BrightdataWebUnlocker` → `WebUnlocker` (simpler, cleaner)
- Keep `BrightdataBaseSpecializedScraper` as-is (or optionally shorten to `BaseSpecializedScraper`)

### 5. Update Tests

All test imports need to be updated:
```python
# Old
from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
from brightdata.browser_api import BrowserAPI
from brightdata.ready_scrapers.amazon.scraper import AmazonScraper

# New
from brightdata.webunlocker import WebUnlocker
from brightdata.browserapi import BrowserAPI
from brightdata.webscraper_api.scrapers.amazon import AmazonScraper
```

### 6. Update Documentation

- README.md examples
- Docstrings
- Any documentation that references old paths

## Benefits

1. **Clear Service Separation**: Each BrightData service has its own module
2. **Cleaner Imports**: More intuitive import paths
3. **Better Organization**: Related code grouped together
4. **Maintains Compatibility**: Can add compatibility imports in __init__.py
5. **Auto Stays Generic**: Auto-detection remains at root level, available to all

## Migration Strategy

1. Create new structure alongside old
2. Update imports to use new paths
3. Test everything works
4. Add deprecation warnings to old imports
5. Eventually remove old structure

## Backwards Compatibility

Add temporary compatibility imports in `brightdata/__init__.py`:
```python
# Backwards compatibility
BrightdataWebUnlocker = WebUnlocker  # Alias old name
```