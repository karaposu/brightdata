#!/usr/bin/env python3
"""
brightdata.ready_scrapers.x.scraper
===================================

Unofficial wrapper around Bright Data’s **X / Twitter** datasets.

Implemented endpoints
---------------------

===============================  Dataset-ID                           Method
-------------------------------  -----------------------------------  -----------------------------------------------
x_posts__collect_by_url          «gd_lwxkxvnf1cynvib9co»              collect_posts_by_url()
x_posts__discover_by_profile_url «gd_lwxkxvnf1cynvib9co»              discover_posts_by_profile_url()
x_profiles__collect_by_url       «gd_lwxmeb2u1cniijd7t4»              collect_profiles_by_url()

All calls run in *async* mode – they return a **snapshot-id** string immediately.
Use any poll helper (`poll_until_ready`, `fetch_snapshot_async`, …) to retrieve
the final rows.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# --------------------------------------------------------------------------- #
# Static Bright-Data dataset-IDs (copied from your examples)
# --------------------------------------------------------------------------- #
_DATASET = {
    "posts":    "gd_lwxkxvnf1cynvib9co",
    "profiles": "gd_lwxmeb2u1cniijd7t4",
}


@register("x")
class XScraper(BrightdataBaseSpecializedScraper):
    """
    ---
    agent_id: x
    title: XScraper
    desc: |
      Unified client for Bright Data’s X (formerly Twitter) “collect by URL”
      and “discover by profile” endpoints.  All methods run in async mode
      and immediately return a snapshot-id.
    example: |
      from brightdata.ready_scrapers.x import XScraper
      s = XScraper()
      snap = s.collect_posts_by_url([
        "https://x.com/FabrizioRomano/status/1683559267524136962"
      ])
      # → 's_abcdef12345'
    ---
    """

    def __init__(self, bearer_token: Optional[str] = None, **kw):
        """
        Initialize XScraper.

        Parameters
        ----------
        bearer_token : str, optional
            Bright Data API token.  If omitted, reads BRIGHTDATA_TOKEN
            from the environment (.env is honoured).
        **kw :
            Extra keyword-arguments forwarded to the base class.
        """
        super().__init__(_DATASET["profiles"], bearer_token, **kw)

    def collect_posts_by_url(self, post_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: collect_posts_by_url
        desc: Scrape individual X/Twitter posts (tweets) by URL.
        params:
          post_urls:
            type: list[str]
            desc: |
              Full status URLs, e.g.
              "https://x.com/<user>/status/<tweet_id>"
        returns:
          type: str
          desc: snapshot_id – poll this until ready to fetch the tweet data.
        example: |
          snap = scraper.collect_posts_by_url([
            "https://x.com/CNN/status/1796673270344810776"
          ])
        ---
        """
        payload = [{"url": u} for u in post_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts"],
            extra_params={"sync_mode": "async"},
        )

    def discover_posts_by_profile_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        ---
        endpoint: discover_posts_by_profile_url
        desc: Crawl multiple tweets from one or more profile URLs.
        params:
          queries:
            type: list[dict]
            desc: |
              Each dict may contain:
                - url (str): profile link, e.g. "https://x.com/elonmusk"
                - start_date (str): ISO-8601 or "YYYY-MM-DD" (empty for no lower bound)
                - end_date (str): ISO-8601 or "YYYY-MM-DD" (empty for no upper bound)
        returns:
          type: str
          desc: snapshot_id – poll until ready to retrieve all tweets.
        example: |
          snap = scraper.discover_posts_by_profile_url([
            {"url":"https://x.com/elonmusk","start_date":"2023-01-01","end_date":""}
          ])
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

    # alias for the same endpoint
    discover_posts_by_url = discover_posts_by_profile_url  # type: ignore

    def collect_profiles_by_url(
        self,
        profile_urls: Sequence[str],
        max_posts: Optional[int] = None,
    ) -> str:
        """
        ---
        endpoint: collect_profiles_by_url
        desc: Scrape profile metadata and optionally the most recent tweets.
        params:
          profile_urls:
            type: list[str]
            desc: Profile links, e.g. "https://x.com/cnn"
          max_posts:
            type: int | null
            desc: |
              Maximum number of recent tweets to include per profile.
              Null or omitted → Bright Data’s default.
        returns:
          type: str
          desc: snapshot_id – poll to fetch profile data (and tweets).
        example: |
          snap = scraper.collect_profiles_by_url(
            ["https://x.com/fabrizioromano"], max_posts=10
          )
        ---
        """
        payload = [
            {"url": u, "max_number_of_posts": max_posts if max_posts is not None else ""}
            for u in profile_urls
        ]
        return self._trigger(
            payload,
            dataset_id=_DATASET["profiles"],
            extra_params={"sync_mode": "async"},
        )

    def _trigger(
        self,
        data: List[Dict[str, Any]],
        *,
        dataset_id: str,
        include_errors: bool = True,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Thin passthrough to the base class trigger method.
        """
        return super()._trigger(
            data,
            dataset_id=dataset_id,
            include_errors=include_errors,
            extra_params=extra_params,
        )


__all__ = ["XScraper"]
