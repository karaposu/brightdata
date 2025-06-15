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

    # ─────────────────────── Sync “smart router” ────────────────────────
    def collect_by_url(
        self,
        urls: Sequence[str],
        *,
        include_comments: bool = False,
    ) -> Dict[str, str]:
        profiles, posts, reels, comments = [], [], [], []

        for u in urls:
            p = urlparse(u).path.lower()
            if "/reel/" in p:
                (comments if include_comments else reels).append(u)
            elif "/p/" in p:
                (comments if include_comments else posts).append(u)
            else:
                profiles.append(u)

        result: Dict[str, str] = {}
        if profiles:
            result["profiles"] = self.profiles__collect_by_url(profiles)
        if posts:
            result["posts"] = self.posts__collect_by_url(posts)
        if reels:
            result["reels"] = self.reels__collect_by_url(reels)
        if comments:
            payload = [
                {"url": u, "days_back": "", "load_all_replies": False, "comment_limit": ""}
                for u in comments
            ]
            result["comments"] = self.comments__collect_by_url(payload)

        return result

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
    async def collect_by_url_async(
        self,
        urls: Sequence[str],
        *,
        include_comments: bool = False,
    ) -> Dict[str, str]:
        profiles, posts, reels, comments = [], [], [], []
        for u in urls:
            p = urlparse(u).path.lower()
            if "/reel/" in p:
                (comments if include_comments else reels).append(u)
            elif "/p/" in p:
                (comments if include_comments else posts).append(u)
            else:
                profiles.append(u)

        tasks: Dict[str, asyncio.Task[str]] = {}
        if profiles:
            tasks["profiles"] = asyncio.create_task(
                self._trigger_async(
                    [{"url": u} for u in profiles],
                    dataset_id=_DATASET["profiles"],
                )
            )
        if posts:
            tasks["posts"] = asyncio.create_task(
                self._trigger_async(
                    [{"url": u} for u in posts],
                    dataset_id=_DATASET["posts"],
                )
            )
        if reels:
            tasks["reels"] = asyncio.create_task(
                self._trigger_async(
                    [{"url": u} for u in reels],
                    dataset_id=_DATASET["reels"],
                )
            )
        if comments:
            payload = [
                {"url": u, "days_back": "", "load_all_replies": False, "comment_limit": ""}
                for u in comments
            ]
            tasks["comments"] = asyncio.create_task(
                self._trigger_async(payload, dataset_id=_DATASET["comments"])
            )

        snaps = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), snaps))

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
