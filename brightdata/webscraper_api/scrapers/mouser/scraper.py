#!/usr/bin/env python3
"""
brightdata.scrapers.mouser.scraper
----------------------------------------

Unofficial wrapper for Bright Data’s *Mouser product page* dataset.

Endpoints implemented
~~~~~~~~~~~~~~~~~~~~~
* **collect_by_url** – scrape specific product URLs (snapshot-id returned)
* **discover_by_category** *(future stub)* – placeholder for category crawls

All calls run in **async mode** (`sync_mode=async`) and therefore return
*immediately* with a snapshot-id.  Block with::

    result = scraper.poll_until_ready(snapshot_id)

or, in an async context::

    result = await scraper.poll_until_ready_async(snapshot_id)

# python -m brightdata.webscraper_api.scrapers.mouser.scraper
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence, Optional

from brightdata.webscraper_api.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.webscraper_api.registry import register
import asyncio

# Bright-Data dataset id (taken from their API docs)
MIN_POLL_TIMEOUT: int = 3600   # seconds  (6 minutes)
_DATASET_COLLECT_BY_URL = "gd_lfjty8942ogxzhmp8t"


@register("mouser")
class MouserScraper(BrightdataBaseSpecializedScraper):
    """
    Ready-made client for Bright Data’s Mouser dataset.

    >>> from brightdata.webscraper_api.scrapers.mouser import MouserScraper
    >>> s     = MouserScraper()
    >>> sid   = s.collect_by_url(["https://www.mouser.com/ProductDetail/ABRACON/ABM8-147456MHZ-D1X-T"])
    >>> rows  = s.poll_until_ready(sid).data
    """

    # ───────────────────────── constructor ───────────────────────────
    def __init__(self, bearer_token: Optional[str] = None, **kw):
        super().__init__(_DATASET_COLLECT_BY_URL, bearer_token, **kw)

    def collect_by_url(self, url: str) -> str:
        """
        Trigger product-detail scraping for exactly one Mouser URL.
        Returns the snapshot_id.
        """
        payload = [{"url": url}]
        return self.trigger(payload, dataset_id=_DATASET_COLLECT_BY_URL)
    
    async def collect_by_url_async(self, url: str) -> str:
        """
        Async version: trigger product-detail scraping for exactly one Mouser URL.
        Returns the snapshot_id.
        """
        payload = [{"url": url}]
        return await self._trigger_async(payload, dataset_id=_DATASET_COLLECT_BY_URL)

    # ─────────────────── discover_by_category (stub) ─────────────────
    def discover_by_category(self, category_urls: Sequence[str]) -> str:
        """
        Placeholder for a future category-crawl dataset.
        Currently triggers the same *collect* dataset but marks type=discover.
        """
        payload = [{"category_url": u} for u in category_urls]
        return self.trigger(
            payload,
            dataset_id=_DATASET_COLLECT_BY_URL,
            extra_params={"type": "discover_new", "discover_by": "category"},
        )

    async def discover_by_category_async(self, category_urls: Sequence[str]) -> str:
        payload = [{"category_url": u} for u in category_urls]
        return await self._trigger_async(
            payload,
            dataset_id=_DATASET_COLLECT_BY_URL,
            extra_params={"type": "discover_new", "discover_by": "category"},
        )
