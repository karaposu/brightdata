#!/usr/bin/env python3
"""
brightdata.ready_scrapers.tiktok.scraper
========================================

High-level wrapper around Bright Data’s **TikTok** datasets.

Implemented methods
---------------------
  • profiles__collect_by_url  
  • profiles__discover_by_search_url  
  • posts__collect_by_url  
  • posts__discover_by_keyword  
  • posts__discover_by_profile_url  
  • posts__discover_by_url  
  • posts_by_url_fast_api__collect_by_url  
  • posts_by_profile_fast_api__collect_by_url  
  • posts_by_search_url_fast_api__collect_by_url  
  • comments__collect_by_url  
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence, Union, DefaultDict
from collections import defaultdict
from urllib.parse import urlparse

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# --------------------------------------------------------------------------- #
# Static Bright-Data dataset-IDs
# --------------------------------------------------------------------------- #
_DATASET = {
    "comments":                         "gd_lkf2st302ap89utw5k",
    "posts_fast":                       "gd_lkf2st302ap89utw5k",
    "posts_profile_fast":               "gd_m7n5v2gq296pex2f5m",
    "posts_search_fast":                "gd_m7n5v2gq296pex2f5m",
    "profiles":                         "gd_l1villgoiiidt09ci",
    "posts":                            "gd_lu702nij2f790tmv9h",
    # newly added for the missing endpoints:
    "posts_discover_url":               "gd_lu702nij2f790tmv9h",
    "posts_by_url_fast_api":            "gd_m736hjp71lejc5dc0l",
    "posts_by_search_url_fast_api":     "gd_m7n5ixlw1gc4no56kx",
}


@register("tiktok")
class TikTokScraper(BrightdataBaseSpecializedScraper):
    """
    ---
    agent_id: tiktok
    title: TikTokScraper
    desc: |
      Unified client for Bright Data’s TikTok endpoints.  All methods
      run in async mode and immediately return a snapshot-id string.
    example: |
      from brightdata.ready_scrapers.tiktok import TikTokScraper
      s = TikTokScraper()
      snap = s.collect_comments_by_url([
          "https://www.tiktok.com/@heymrcat/video/7216019547806092550"
      ])
      # → 's_abcdef12345'
    ---
    """

    def __init__(self, bearer_token: Optional[str] = None, **kw):
        """
        Initialize TikTokScraper.

        Parameters
        ----------
        bearer_token : str, optional
            Bright Data API token.  If omitted, reads BRIGHTDATA_TOKEN
            from the environment (.env supported).
        **kw :
            Extra keyword-arguments forwarded to the base class.
        """
        super().__init__(_DATASET["profiles"], bearer_token, **kw)

    # ────────────────────────────────────────────────────────────────────
    # Generic dispatcher
    # ────────────────────────────────────────────────────────────────────
    def collect_by_url(
        self,
        urls: Sequence[str],
        include_comments: bool = False,
    ) -> Dict[str, str]:
        """
        Dispatch URLs to the appropriate “collect by URL” endpoint:
          - profile links  → profiles__collect_by_url()
          - video links    → posts__collect_by_url()  or comments__collect_by_url()

        Parameters
        ----------
        urls : sequence[str]
            TikTok URLs (profiles `/@name` or posts `/@name/video/<id>`)
        include_comments : bool
            If True, video URLs go to comments__collect_by_url()
            (otherwise to posts__collect_by_url()).

        Returns
        -------
        dict[str, str]
            Mapping of bucket name → snapshot-id, e.g.
            ```
            {
              "profiles": "s_abc…",
              "posts":    "s_def…",
              "comments": "s_ghi…"   # only if include_comments=True
            }
            ```

        Raises
        ------
        ValueError
            If any URL doesn’t look like a profile or video.
        """
        buckets: dict[str, List[str]] = defaultdict(list)
        for u in urls:
            path = urlparse(u).path or ""
            if path.startswith("/@"):
                buckets["profiles"].append(u)
            elif "/video/" in path:
                key = "comments" if include_comments else "posts"
                buckets[key].append(u)
            else:
                raise ValueError(f"Unrecognised TikTok URL: {u}")

        result: Dict[str, str] = {}
        if buckets.get("profiles"):
            result["profiles"] = self.profiles__collect_by_url(buckets["profiles"])
        if buckets.get("posts"):
            result["posts"] = self.posts__collect_by_url(buckets["posts"])
        if buckets.get("comments"):
            result["comments"] = self.comments__collect_by_url(buckets["comments"])
        return result

    # ────────────────────────────────────────────────────────────────────
    # 1. Profiles
    # ────────────────────────────────────────────────────────────────────
    def profiles__collect_by_url(self, profile_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: profiles__collect_by_url
        desc: Scrape TikTok profile metadata (followers, bio, stats).
        params:
          profile_urls:
            type: list[str]
            desc: Profile URLs, e.g. "https://www.tiktok.com/@username".
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.profiles__collect_by_url([
            "https://www.tiktok.com/@fofimdmell"
          ])
        ---
        """
        payload = [{"url": u, "country": ""} for u in profile_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["profiles"],
            extra_params={"sync_mode": "async"},
        )

    def profiles__discover_by_search_url(self, queries: Sequence[Dict[str, str]]) -> str:
        """
        ---
        endpoint: profiles__discover_by_search_url
        desc: Discover TikTok profiles from search/explore URLs.
        params:
          queries:
            type: list[dict]
            desc: |
              Each dict must contain:
                - search_url: explore or search URL
                - country: ISO-2 code or empty
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.profiles__discover_by_search_url([
            {"search_url": "https://www.tiktok.com/explore?lang=en", "country": "US"}
          ])
        ---
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["profiles"],
            extra_params={
                "sync_mode":   "async",
                "type":        "discover_new",
                "discover_by": "search_url",
            },
        )

    # ────────────────────────────────────────────────────────────────────
    # 2. Posts (fast-api variant)
    # ────────────────────────────────────────────────────────────────────
    def posts__collect_by_url(self, post_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: posts__collect_by_url
        desc: Fast-API variant to scrape one or many TikTok post objects.
        params:
          post_urls:
            type: list[str]
            desc: TikTok post URLs (must contain `/video/`).
        returns:
          type: str
          desc: snapshot_id – poll until ready to retrieve post JSON.
        example: |
          snap = scraper.posts__collect_by_url([
            "https://www.tiktok.com/@user/video/1234567890"
          ])
        ---
        """
        payload = [{"url": u} for u in post_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts_fast"],
            extra_params={"sync_mode": "async"},
        )

    def posts__discover_by_keyword(self, keywords: Sequence[str]) -> str:
        """
        ---
        endpoint: posts__discover_by_keyword
        desc: Discover posts by hashtag or keyword.
        params:
          keywords:
            type: list[str]
            desc: Use "#tag" for hashtags or plain text for search.
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.posts__discover_by_keyword(["#funnydogs", "dance"])
        ---
        """
        payload = [{"search_keyword": kw, "country": ""} for kw in keywords]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts"],
            extra_params={
                "sync_mode":   "async",
                "type":        "discover_new",
                "discover_by": "keyword",
            },
        )

    def posts__discover_by_profile_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        ---
        endpoint: posts__discover_by_profile_url
        desc: Discover posts via profile URL with filters.
        params:
          queries:
            type: list[dict]
            desc: |
              Each dict may include:
                - url (str): profile link
                - num_of_posts (int): 0 for no limit
                - posts_to_not_include (list[str])
                - what_to_collect (str): "Posts"|"Reposts"|"Posts & Reposts"
                - start_date/end_date ("MM-DD-YYYY")
                - post_type: "Video"|"Image"|"" 
                - country: ISO-2 code or empty
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.posts__discover_by_profile_url([{
            "url":"https://www.tiktok.com/@username",
            "num_of_posts":10,
            "what_to_collect":"Posts & Reposts"
          }])
        ---
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["posts"],
            extra_params={
                "sync_mode":   "async",
                "type":        "discover_new",
                "discover_by": "profile_url",
            },
        )

    def posts__discover_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        ---
        endpoint: posts__discover_by_url
        desc: Discover TikTok feed items (discover/channel/music/explore URLs).
        params:
          queries:
            type: list[dict]
            desc: |
              Each dict must include:
                - url (str): e.g. "https://www.tiktok.com/discover/dog"
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.posts__discover_by_url([{"url":"https://www.tiktok.com/discover/dog"}])
        ---
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["posts_discover_url"],
            extra_params={
                "sync_mode":   "async",
                "type":        "discover_new",
                "discover_by": "url",
            },
        )

    # ────────────────────────────────────────────────────────────────────
    # 3. Fast-API “by URL” family
    # ────────────────────────────────────────────────────────────────────
    def posts_by_url_fast_api__collect_by_url(self, urls: Sequence[str]) -> str:
        """
        ---
        endpoint: posts_by_url_fast_api__collect_by_url
        desc: Fast-API variant to collect arbitrary feed items by URL.
        params:
          urls:
            type: list[str]
            desc: Full TikTok URLs (discover/channel/music/explore).
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.posts_by_url_fast_api__collect_by_url([
            "https://www.tiktok.com/discover/dog1",
            "https://www.tiktok.com/channel/anime",
            "https://www.tiktok.com/music/Some-Track-ID",
            "https://www.tiktok.com/explore?lang=en"
          ])
        ---
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts_by_url_fast_api"],
            extra_params={"sync_mode": "async"},
        )

    def posts_by_profile_fast_api__collect_by_url(self, urls: Sequence[str]) -> str:
        """
        ---
        endpoint: posts_by_profile_fast_api__collect_by_url
        desc: Fast-API variant to collect the latest posts from profiles.
        params:
          urls:
            type: list[str]
            desc: Profile URLs, e.g. "https://www.tiktok.com/@bbc".
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.posts_by_profile_fast_api__collect_by_url([
            "https://www.tiktok.com/@bbc",
            "https://www.tiktok.com/@portalotempo"
          ])
        ---
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts_profile_fast"],
            extra_params={"sync_mode": "async"},
        )

    def posts_by_search_url_fast_api__collect_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        ---
        endpoint: posts_by_search_url_fast_api__collect_by_url
        desc: Fast-API variant to collect feed items from search URLs.
        params:
          queries:
            type: list[dict]
            desc: |
              Each dict may include:
                - url (str): full search URL (with q=…, t=…)
                - num_of_posts (int, optional)
                - country (str, optional)
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.posts_by_search_url_fast_api__collect_by_url([
            {"url":"https://www.tiktok.com/search?lang=en&q=cats&t=…","country":""},
            {"url":"https://www.tiktok.com/search?lang=en&q=dogs&t=…","num_of_posts":10,"country":"US"}
          ])
        ---
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["posts_by_search_url_fast_api"],
            extra_params={"sync_mode": "async"},
        )

    # ────────────────────────────────────────────────────────────────────
    # 4. Comments
    # ────────────────────────────────────────────────────────────────────
    def comments__collect_by_url(self, post_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: comments__collect_by_url
        desc: Retrieve comments for specified TikTok post URLs.
        params:
          post_urls:
            type: list[str]
            desc: Full TikTok post URLs (must contain `/video/`).
        returns:
          type: str
          desc: snapshot_id – poll this until ready to fetch results.
        example: |
          snap = scraper.comments__collect_by_url([
            "https://www.tiktok.com/@heymrcat/video/7216019547806092550"
          ])
        ---
        """
        payload = [{"url": u} for u in post_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["comments"],
            extra_params={"sync_mode": "async"},
        )

    # ────────────────────────────────────────────────────────────────────
    # Internal passthrough
    # ────────────────────────────────────────────────────────────────────
    def _trigger(
        self,
        data: List[Dict[str, Any]],
        *,
        dataset_id: str,
        include_errors: bool = True,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        return super()._trigger(
            data,
            dataset_id=dataset_id,
            include_errors=include_errors,
            extra_params=extra_params,
        )
