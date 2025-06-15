# this is brightdata/__init__.py

from .brightdata_web_unlocker import BrightdataWebUnlocker
from .base_specialized_scraper import BrightdataBaseSpecializedScraper
# from .auto import scrape_url, trigger_scrape_url, trigger_scrape_url_with_fallback
from .auto import scrape_url, scrape_url_async, scrape_urls, scrape_urls_async
from .browser_api import BrowserAPI

