#!/usr/bin/env python3
"""
brightdata.scrapers.x.scraper
===================================

High-level wrapper around Bright Data’s X / Twitter datasets.
Every sync method calls `self.trigger()` (engine-backed) and returns a
snapshot-ID. Async variants use `self._trigger_async()`.
"""

from __future__ import annotations
import asyncio
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlparse

from brightdata.webscraper_api.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.webscraper_api.registry import register

_DATASET = {
    "posts":    "gd_lwxkxvnf1cynvib9co",
    "profiles": "gd_lwxmeb2u1cniijd7t4",
}


@register(("x"))
class XScraper(BrightdataBaseSpecializedScraper):
    """Unified Bright-Data client for X (Twitter) posts & profiles."""

    def __init__(self, bearer_token: Optional[str] = None, **kw):
        # default dataset is arbitrary – we only need it for test_connection
        super().__init__(_DATASET["profiles"], bearer_token, **kw)

    # ───────────────────────────── smart router ──────────────────────────

    def collect_by_url(self, url: str) -> str:
        """
        Trigger a Twitter scrape for exactly one URL and return its snapshot_id.
        - URLs with "/status/" → posts endpoint
        - everything else    → profiles endpoint
        """
        path = urlparse(url).path or ""
        if "/status/" in path:
            return self.posts__collect_by_url([url])
        else:
            return self.profiles__collect_by_url([url])
        
    # def collect_by_url(self, urls: Sequence[str]) -> Dict[str, str]:
    #     buckets: Dict[str, List[str]] = defaultdict(list)
    #     for u in urls:
    #         if "/status/" in (urlparse(u).path or ""):
    #             buckets["posts"].append(u)
    #         else:
    #             buckets["profiles"].append(u)

    #     out: Dict[str, str] = {}
    #     if buckets["posts"]:
    #         out["posts"] = self.posts__collect_by_url(buckets["posts"])
    #     if buckets["profiles"]:
    #         out["profiles"] = self.profiles__collect_by_url(buckets["profiles"])
    #     return out

    # ───────────────────────────── sync endpoints ───────────────────────
    def posts__collect_by_url(self, post_urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in post_urls]
        return self.trigger(payload, dataset_id=_DATASET["posts"])

    def posts__discover_by_profile_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        return self.trigger(
            list(queries),
            dataset_id=_DATASET["posts"],
            extra_params={"type": "discover_new", "discover_by": "profile_url"},
        )

    def profiles__collect_by_url(
        self,
        profile_urls: Sequence[str],
        max_posts: int | None = None,
    ) -> str:
        payload = [
            {"url": u, "max_number_of_posts": max_posts or 100}
            for u in profile_urls
        ]
        return self.trigger(payload, dataset_id=_DATASET["profiles"])

    # ───────────────────────────── async variants ───────────────────────


    async def collect_by_url_async(self, url: str) -> str:
        """
        Async version of collect_by_url: accept one Tweet or profile URL.
        """
        path = urlparse(url).path or ""
        if "/status/" in path:
            return await self.posts__collect_by_url_async([url])
        else:
            return await self.profiles__collect_by_url_async([url])
        

    async def collect_by_url_async(
        self,
        url: str,
        *,
        max_number_of_posts: Optional[int] = None
    ) -> str:
        """
        Async single-URL collector.

        - If it's a status/Tweet URL, we hit the posts endpoint
        - Otherwise it's a user profile: you can optionally pass
          max_number_of_posts to cap how many recent Tweets to fetch.
        """
        path = urlparse(url).path or ""

        if "/status/" in path:
            # single‐Tweet snapshot
            return await self._trigger_async(
                [{"url": url}],
                dataset_id=_DATASET["posts"]
            )
        else:
            # profile feed snapshot
            payload = [{"url": url}]
            if max_number_of_posts is not None:
                payload[0]["max_number_of_posts"] = max_number_of_posts
            return await self._trigger_async(
                payload,
                dataset_id=_DATASET["profiles"]
            )

    async def posts__collect_by_url_async(self, post_urls: Sequence[str]) -> str:
        return await self._trigger_async(
            [{"url": u} for u in post_urls],
            dataset_id=_DATASET["posts"],
        )

    async def posts__discover_by_profile_url_async(
        self, queries: Sequence[Dict[str, Any]]
    ) -> str:
        return await self._trigger_async(
            list(queries),
            dataset_id=_DATASET["posts"],
            extra_params={"type": "discover_new", "discover_by": "profile_url"},
        )

    async def profiles__collect_by_url_async(
        self,
        profile_urls: Sequence[str],
        max_posts: int | None = None,
    ) -> str:
        payload = [
            {"url": u, "max_number_of_posts": max_posts or 100}
            for u in profile_urls
        ]
        return await self._trigger_async(payload, dataset_id=_DATASET["profiles"])
