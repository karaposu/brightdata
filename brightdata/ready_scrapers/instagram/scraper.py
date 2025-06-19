#!/usr/bin/env python3
"""
brightdata.ready_scrapers.instagram.scraper
===========================================

High-level client for Bright Data’s Instagram endpoints.
All sync methods call `self.trigger(…)` and return a snapshot-ID.
Async methods use `self._trigger_async(…)`.
"""

from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlparse

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# static dataset-IDs
_DATASET = {
    "profiles": "gd_l1vikfch901nx3by4",
    "posts":    "gd_lk5ns7kz21pck8jpis",
    "reels":    "gd_lyclm20il4r5helnj",
    "comments": "gd_ltppn085pokosxh13",
}


@register("instagram")
class InstagramScraper(BrightdataBaseSpecializedScraper):
    """
    Each method returns immediately with a snapshot-ID.
    Call `scraper.poll_until_ready(sid)` or the async twin to get data.
    """

    def __init__(self, bearer_token: Optional[str] = None, **kw):
        super().__init__(_DATASET["profiles"], bearer_token, **kw)

    # ─────────────────────── Sync “smart router for instagram scraper.py” ────────────────────────

    def _classify(self, url: str) -> str:
        """
        Returns one of: "profile", "post", or "reel".
        """
        path = urlparse(url).path.lower()
        if "/reel/" in path:
            return "reel"
        if "/p/" in path:
            return "post"
        return "profile"
    
    
    def collect_by_url(self, url: str) -> str:
        """
        Trigger an Instagram scrape for exactly one URL and return its snapshot-id.

        :param url: a single Instagram URL
        :returns: snapshot-id for that URL
        """
        path = urlparse(url).path.lower()

        if "/reel/" in path:
            # wrap in a list for the underlying endpoint
            return self.reels__collect_by_url([url])
        elif "/p/" in path:
            return self.posts__collect_by_url([url])
        else:
            return self.profiles__collect_by_url([url])
        

   
    # ───────────────────── Sync endpoints ──────────────────────────────
    def profiles__collect_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]
        return self.trigger(payload, dataset_id=_DATASET["profiles"])

    def posts__collect_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]
        return self.trigger(payload, dataset_id=_DATASET["posts"])

    def posts__discover_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        return self.trigger(
            list(queries),
            dataset_id=_DATASET["posts"],
            extra_params={"type": "discover_new", "discover_by": "url"},
        )
     
    def reels__collect_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]
        return self.trigger(payload, dataset_id=_DATASET["reels"])
    
    def reels__discover_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        return self.trigger(
            list(queries),
            dataset_id=_DATASET["reels"],
            extra_params={"type": "discover_new", "discover_by": "url"},
        )

    def reels__discover_by_url_all_reels(self, queries: Sequence[Dict[str, Any]]) -> str:
        return self.trigger(
            list(queries),
            dataset_id=_DATASET["reels"],
            extra_params={"type": "discover_new", "discover_by": "url_all_reels"},
        )
    
    def comments__collect_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        return self.trigger(
            list(queries),
            dataset_id=_DATASET["comments"],
        )

    # ─────────────────── Async variants ────────────────────────────────
    async def collect_by_url_async(self, url: str) -> str:
        """
        Async version: accept one URL, classify it, and dispatch to the right async method.
        """
        path = urlparse(url).path.lower()

        if "/reel/" in path:
            return await self.reels__collect_by_url_async([url])
        elif "/p/" in path:
            return await self.posts__collect_by_url_async([url])
        else:
            return await self.profiles__collect_by_url_async([url])
    

    

    async def profiles__collect_by_url_async(self, urls: Sequence[str]) -> str:
        return await self._trigger_async(
            [{"url": u} for u in urls],
            dataset_id=_DATASET["profiles"],
        )

    async def posts__collect_by_url_async(self, urls: Sequence[str]) -> str:
        return await self._trigger_async(
            [{"url": u} for u in urls],
            dataset_id=_DATASET["posts"],
        )

    async def posts__discover_by_url_async(self, queries: Sequence[Dict[str, Any]]) -> str:
        return await self._trigger_async(
            list(queries),
            dataset_id=_DATASET["posts"],
            extra_params={"type": "discover_new", "discover_by": "url"},
        )

    async def reels__collect_by_url_async(self, urls: Sequence[str]) -> str:
        return await self._trigger_async(
            [{"url": u} for u in urls],
            dataset_id=_DATASET["reels"],
        )

    async def reels__discover_by_url_async(self, queries: Sequence[Dict[str, Any]]) -> str:
        return await self._trigger_async(
            list(queries),
            dataset_id=_DATASET["reels"],
            extra_params={"type": "discover_new", "discover_by": "url"},
        )

    async def reels__discover_by_url_all_reels_async(self, queries: Sequence[Dict[str, Any]]) -> str:
        return await self._trigger_async(
            list(queries),
            dataset_id=_DATASET["reels"],
            extra_params={"type": "discover_new", "discover_by": "url_all_reels"},
        )

    async def comments__collect_by_url_async(self, queries: Sequence[Dict[str, Any]]) -> str:
        return await self._trigger_async(
            list(queries),
            dataset_id=_DATASET["comments"],
        )
