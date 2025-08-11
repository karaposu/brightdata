#!/usr/bin/env python3
"""
brightdata.scrapers.tiktok.scraper
========================================
Unified helper for Bright Data’s TikTok datasets (profiles, posts, fast-API
variants, comments).  Every call runs with ``sync_mode=async`` and therefore
returns a **snapshot-id** right away; use the *poll* helpers provided by the
base class to obtain the rows.

# python -m brightdata.webscraper_api.scrapers.tiktok.scraper
"""

from __future__ import annotations
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, DefaultDict
from urllib.parse import urlparse
import asyncio

from brightdata.webscraper_api.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.webscraper_api.registry import register

# ───────────────────────────── dataset-IDs ────────────────────────────────
_DATASET = {
    # “classic” datasets
    "profiles":             "gd_l1villgoiiidt09ci",
    "posts":                "gd_lu702nij2f790tmv9h",
    "posts_discover_url":   "gd_lu702nij2f790tmv9h",
    "comments":             "gd_lkf2st302ap89utw5k",
    # fast-API variants
    "posts_fast":                   "gd_lkf2st302ap89utw5k",
    "posts_profile_fast":           "gd_m7n5v2gq296pex2f5m",
    "posts_search_fast":            "gd_m7n5v2gq296pex2f5m",
    "posts_by_url_fast_api":        "gd_m736hjp71lejc5dc0l",
    "posts_by_search_url_fast_api": "gd_m7n5ixlw1gc4no56kx",
}

# ───────────────────────────── scraper class ──────────────────────────────
@register("tiktok")
class TikTokScraper(BrightdataBaseSpecializedScraper):
    """High-level TikTok client – wraps eight Bright-Data datasets."""

    # default dataset for quick connectivity checks
    def __init__(self, bearer_token: Optional[str] = None, **kw) -> None:
        super().__init__(_DATASET["profiles"], bearer_token, **kw)

    # ══════════════════════════════════════════════════════════════════════
    # Generic router
    # ══════════════════════════════════════════════════════════════════════

    def collect_by_url(
        self,
        url: str,
        *,
        include_comments: bool = False,
    ) -> str:
        """
        Trigger a TikTok scrape for exactly one URL.
        - /@username → profiles endpoint
        - /video/…   → posts or comments endpoint
        """
        path = (urlparse(url).path or "").lower()

        if path.startswith("/@"):
            # profile page
            return self.profiles__collect_by_url([url])
        elif "/video/" in path:
            if include_comments:
                return self.comments__collect_by_url([url])
            else:
                return self.posts__collect_by_url([url])
        else:
            raise ValueError(f"Unrecognised TikTok URL: {url!r}")
        
    
    async def collect_by_url_async(
        self,
        url: str,
        *,
        include_comments: bool = False,
    ) -> str:
        """
        Async version of collect_by_url.
        """
        path = (urlparse(url).path or "").lower()

        if path.startswith("/@"):
            return await self.profiles__collect_by_url_async([url])
        elif "/video/" in path:
            if include_comments:
                return await self.comments__collect_by_url_async([url])
            else:
                return await self.posts__collect_by_url_async([url])
        else:
            raise ValueError(f"Unrecognised TikTok URL: {url!r}")
        

    # def collect_by_url(
    #     self,
    #     urls: Sequence[str],
    #     *,
    #     include_comments: bool = False,
    # ) -> Dict[str, str]:
    #     buckets: DefaultDict[str, List[str]] = defaultdict(list)

    #     for u in urls:
    #         path = (urlparse(u).path or "").lower()
    #         if path.startswith("/@"):
    #             buckets["profiles"].append(u)
    #         elif "/video/" in path:
    #             buckets["comments" if include_comments else "posts"].append(u)
    #         else:
    #             raise ValueError(f"Unrecognised TikTok URL: {u}")

    #     out: Dict[str, str] = {}
    #     if buckets["profiles"]:
    #         out["profiles"] = self.profiles__collect_by_url(buckets["profiles"])
    #     if buckets["posts"]:
    #         out["posts"] = self.posts__collect_by_url(buckets["posts"])
    #     if buckets["comments"]:
    #         out["comments"] = self.comments__collect_by_url(buckets["comments"])
    #     return out

    # ══════════════════════════════════════════════════════════════════════
    # 1.  PROFILES
    # ══════════════════════════════════════════════════════════════════════
    def profiles__collect_by_url(self, profile_urls: Sequence[str]) -> str:
        payload = [{"url": u, "country": ""} for u in profile_urls]
        return self._trigger(payload, dataset_id=_DATASET["profiles"])

    def profiles__discover_by_search_url(self, queries: Sequence[Dict[str, str]]) -> str:
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["profiles"],
            extra_params={"type": "discover_new", "discover_by": "search_url"},
        )

    # ══════════════════════════════════════════════════════════════════════
    # 2.  POSTS  (fast-API default)
    # ══════════════════════════════════════════════════════════════════════
    def posts__collect_by_url(self, post_urls: Sequence[str]) -> str:
        return self._trigger(
            [{"url": u} for u in post_urls],
            dataset_id=_DATASET["posts_fast"],
        )

    def posts__discover_by_keyword(self, keywords: Sequence[str]) -> str:
        payload = [{"search_keyword": kw, "country": ""} for kw in keywords]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts"],
            extra_params={"type": "discover_new", "discover_by": "keyword"},
        )

    def posts__discover_by_profile_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["posts"],
            extra_params={"type": "discover_new", "discover_by": "profile_url"},
        )

    def posts__discover_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["posts_discover_url"],
            extra_params={"type": "discover_new", "discover_by": "url"},
        )

    # ══════════════════════════════════════════════════════════════════════
    # 3.  Fast-API family
    # ══════════════════════════════════════════════════════════════════════
    def posts_by_url_fast_api__collect_by_url(self, urls: Sequence[str]) -> str:
        return self._trigger(
            [{"url": u} for u in urls],
            dataset_id=_DATASET["posts_by_url_fast_api"],
        )

    def posts_by_profile_fast_api__collect_by_url(self, urls: Sequence[str]) -> str:
        return self._trigger(
            [{"url": u} for u in urls],
            dataset_id=_DATASET["posts_profile_fast"],
        )

    def posts_by_search_url_fast_api__collect_by_url(
        self, queries: Sequence[Dict[str, Any]]
    ) -> str:
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["posts_by_search_url_fast_api"],
        )

    # ══════════════════════════════════════════════════════════════════════
    # 4.  COMMENTS
    # ══════════════════════════════════════════════════════════════════════
    def comments__collect_by_url(self, post_urls: Sequence[str]) -> str:
        return self._trigger(
            [{"url": u} for u in post_urls],
            dataset_id=_DATASET["comments"],
        )

    # ══════════════════════════════════════════════════════════════════════
    # 5.  Async mirrors
    # ══════════════════════════════════════════════════════════════════════
    async def collect_by_url_async(
        self,
        urls: Sequence[str],
        include_comments: bool = False,
    ) -> Dict[str, str]:
        # bucket exactly as in sync path
        buckets: DefaultDict[str, List[str]] = defaultdict(list)
        for u in urls:
            p = (urlparse(u).path or "").lower()
            if p.startswith("/@"):
                buckets["profiles"].append(u)
            elif "/video/" in p:
                buckets["comments" if include_comments else "posts"].append(u)
            else:
                raise ValueError(f"Unrecognised TikTok URL: {u}")

        tasks: Dict[str, asyncio.Task[str]] = {}
        if buckets["profiles"]:
            tasks["profiles"] = asyncio.create_task(
                self._trigger_async(
                    [{"url": u, "country": ""} for u in buckets["profiles"]],
                    dataset_id=_DATASET["profiles"],
                )
            )
        if buckets["posts"]:
            tasks["posts"] = asyncio.create_task(
                self._trigger_async(
                    [{"url": u} for u in buckets["posts"]],
                    dataset_id=_DATASET["posts_fast"],
                )
            )
        if buckets["comments"]:
            tasks["comments"] = asyncio.create_task(
                self._trigger_async(
                    [{"url": u} for u in buckets["comments"]],
                    dataset_id=_DATASET["comments"],
                )
            )

        snaps = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), snaps))

    # ---- one-liner async helpers ----------------------------------------
    async def profiles__collect_by_url_async(self, urls: Sequence[str]) -> str:
        return await self._trigger_async(
            [{"url": u, "country": ""} for u in urls],
            dataset_id=_DATASET["profiles"],
        )

    async def profiles__discover_by_search_url_async(
        self, queries: Sequence[Dict[str, Any]]
    ) -> str:
        return await self._trigger_async(
            list(queries),
            dataset_id=_DATASET["profiles"],
            extra_params={"type": "discover_new", "discover_by": "search_url"},
        )

    async def posts__collect_by_url_async(self, post_urls: Sequence[str]) -> str:
        return await self._trigger_async(
            [{"url": u} for u in post_urls],
            dataset_id=_DATASET["posts_fast"],
        )

    async def posts__discover_by_keyword_async(self, keywords: Sequence[str]) -> str:
        return await self._trigger_async(
            [{"search_keyword": kw, "country": ""} for kw in keywords],
            dataset_id=_DATASET["posts"],
            extra_params={"type": "discover_new", "discover_by": "keyword"},
        )

    async def posts__discover_by_profile_url_async(
        self, queries: Sequence[Dict[str, Any]]
    ) -> str:
        return await self._trigger_async(
            list(queries),
            dataset_id=_DATASET["posts"],
            extra_params={"type": "discover_new", "discover_by": "profile_url"},
        )

    async def posts__discover_by_url_async(
        self, queries: Sequence[Dict[str, Any]]
    ) -> str:
        return await self._trigger_async(
            list(queries),
            dataset_id=_DATASET["posts_discover_url"],
            extra_params={"type": "discover_new", "discover_by": "url"},
        )

    async def posts_by_url_fast_api__collect_by_url_async(
        self, urls: Sequence[str]
    ) -> str:
        return await self._trigger_async(
            [{"url": u} for u in urls],
            dataset_id=_DATASET["posts_by_url_fast_api"],
        )

    async def posts_by_profile_fast_api__collect_by_url_async(
        self, urls: Sequence[str]
    ) -> str:
        return await self._trigger_async(
            [{"url": u} for u in urls],
            dataset_id=_DATASET["posts_profile_fast"],
        )

    async def posts_by_search_url_fast_api__collect_by_url_async(
        self, queries: Sequence[Dict[str, Any]]
    ) -> str:
        return await self._trigger_async(
            list(queries),
            dataset_id=_DATASET["posts_by_search_url_fast_api"],
        )

    async def comments__collect_by_url_async(self, post_urls: Sequence[str]) -> str:
        return await self._trigger_async(
            [{"url": u} for u in post_urls],
            dataset_id=_DATASET["comments"],
        )
