#!/usr/bin/env python3
"""
brightdata.scrapers.digikey.scraper
-----------------------------------------

Wrapper for Bright Data’s Digi-Key product dataset.

Implemented endpoints
~~~~~~~~~~~~~~~~~~~~~
* **collect_by_url** – scrape specific product pages
* **discover_by_category** – crawl category pages for new parts

All calls run with `sync_mode=async` and therefore return a **snapshot-id**
immediately.  Block with::

    res = scraper.poll_until_ready(snapshot_id)

or in an `async` context::

    res = await scraper.poll_until_ready_async(snapshot_id)
"""
from __future__ import annotations

from typing import List, Sequence, Dict, Optional

from brightdata.webscraper_api.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.webscraper_api.registry import register
import asyncio


@register("digikey")
class DigikeyScraper(BrightdataBaseSpecializedScraper):
    """
    High-level client for Bright Data’s Digi-Key dataset.

    >>> from brightdata.webscraper_api.scrapers.digikey import DigikeyScraper
    >>> s   = DigikeyScraper()
    >>> sid = s.collect_by_url(
    ...     "https://www.digikey.com/en/products/detail/STMicroelectronics/STM32F407VGT6/2747117"
    ... )
    >>> rows = s.poll_until_ready(sid).data
    """

    _DATASET_ID = "gd_lj74waf72416ro0k65"

    # ───────────────────────── constructor ───────────────────────────
    def __init__(self, bearer_token: Optional[str] = None, **kw):
        super().__init__(self._DATASET_ID, bearer_token, **kw)
     
    # ─────────────────────── collect_by_url (sync) ───────────────────
    # def collect_by_url(self, urls: Sequence[str]) -> str:
    #     payload = [{"url": u} for u in urls]
    #     return self.trigger(payload, dataset_id=self._DATASET_ID)
    
    def collect_by_url(self, url: str) -> str:
        """
        Trigger a Bright Data job for exactly one URL and return its snapshot_id.
        """
        payload = [{"url": url}]
        return self.trigger(payload, dataset_id=self._DATASET_ID)

    # ───────────────────── collect_by_url (async) ────────────────────
    # async def collect_by_url_async(self, urls: Sequence[str]) -> str:
    #     payload = [{"url": u} for u in urls]
    #     return await self._trigger_async(payload, dataset_id=self._DATASET_ID)

    async def collect_by_url_async(self, url: str) -> str:
        """
        Trigger a Bright Data job for exactly one URL and return its snapshot_id.
        """
        payload = [{"url": url}]
        return await self._trigger_async(payload, dataset_id=self._DATASET_ID)

    # ───────────────────── discover_by_category (sync) ───────────────
    def discover_by_category(self, category_urls: Sequence[str]) -> str:
        payload = [{"category_url": url} for url in category_urls]
        return self.trigger(
            payload,
            dataset_id=self._DATASET_ID,
            extra_params={"type": "discover_new", "discover_by": "category"},
        )

    # ───────────────────── discover_by_category (async) ──────────────
    async def discover_by_category_async(self, category_urls: Sequence[str]) -> str:
        payload = [{"category_url": url} for url in category_urls]
        return await self._trigger_async(
            payload,
            dataset_id=self._DATASET_ID,
            extra_params={"type": "discover_new", "discover_by": "category"},
        )
