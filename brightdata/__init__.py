# this is brightdata/__init__.py

from .web_unlocker import WebUnlocker
from .webscraper_api import BrightdataBaseSpecializedScraper
# from .auto import scrape_url, trigger_scrape_url, trigger_scrape_url_with_fallback
from .auto import scrape_url, scrape_url_async, scrape_urls, scrape_urls_async
from .auto import crawl_single_url, crawl_website, crawl_single_url_async, crawl_website_async
from .browserapi import BrowserAPI
from .crawlerapi import CrawlerAPI, crawl_url, crawl_domain

