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
# Static dataset-ids (taken from the cURL examples you provided)
# --------------------------------------------------------------------------- #
_DATASET = {
    "posts":     "gd_lwxkxvnf1cynvib9co",
    "profiles":  "gd_lwxmeb2u1cniijd7t4",
}

# Register the scraper for both legacy and new host-names
@register(("x"))          # registry matches substrings in the domain
class XScraper(BrightdataBaseSpecializedScraper):
    """
    High-level Bright Data client for X (Twitter) datasets.
    """

    # ------------------------------------------------------------------ #
    # constructor – defaults to the *profiles* dataset for connectivity
    # ------------------------------------------------------------------ #
    def __init__(self, bearer_token: Optional[str] = None, **kw):
        super().__init__(_DATASET["profiles"], bearer_token, **kw)

    # ****************************************************************** #
    # 1.  POSTS  ▸  collect by URL
    # ****************************************************************** #
    def collect_posts_by_url(self, post_urls: Sequence[str]) -> str:
        """
        Scrape **individual posts** (tweets) by URL.

        Parameters
        ----------
        post_urls : sequence[str]
            Links that look like  
            ``https://x.com/<user>/status/<tweet_id>``

        Returns
        -------
        snapshot_id : str
        """
        payload = [{"url": u} for u in post_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts"],
            extra_params={"sync_mode": "async"},
        )

    # ****************************************************************** #
    # 2.  POSTS  ▸  discover by profile URL
    # ****************************************************************** #
    def discover_posts_by_profile_url(self,
                                      queries: Sequence[Dict[str, Any]]) -> str:
        """
        Crawl **many tweets** from one or several profile URLs.

        Each *query* dict may contain:

        ==================  ---------------------------------------------------
        Key                  Meaning / example
        ------------------  ---------------------------------------------------
        ``url``              ``"https://x.com/elonmusk"``
        ``start_date``       ISO-8601 or “YYYY-MM-DD” (`""` ⇒ no lower bound)
        ``end_date``         same (`""` ⇒ no upper bound)
        ==================  ---------------------------------------------------

        Returns
        -------
        snapshot_id : str
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

    # alias – Bright Data sometimes calls exactly the same endpoint
    discover_posts_by_url = discover_posts_by_profile_url  # type: ignore

    # ****************************************************************** #
    # 3.  PROFILES  ▸  collect by URL
    # ****************************************************************** #
    def collect_profiles_by_url(self,
                                profile_urls: Sequence[str],
                                max_posts: int | None = None) -> str:
        """
        Scrape **profile metadata** and (optionally) the most recent tweets.

        Parameters
        ----------
        profile_urls : sequence[str]
            Profile links (``https://x.com/cnn``).
        max_posts : int | None
            How many recent tweets to include per profile.
            ``None`` ⇒ use Bright Data’s default (100).

        Returns
        -------
        snapshot_id : str
        """
        payload = [
            {"url": u, "max_number_of_posts": max_posts or 100}
            for u in profile_urls
        ]
        return self._trigger(
            payload,
            dataset_id=_DATASET["profiles"],
            extra_params={"sync_mode": "async"},
        )

    # ------------------------------------------------------------------ #
    # Internal passthrough
    # ------------------------------------------------------------------ #
    def _trigger(self,
                 data: List[Dict[str, Any]],
                 *,
                 dataset_id: str,
                 include_errors: bool = True,
                 extra_params: Optional[Dict[str, Any]] = None) -> str:
        """
        Thin wrapper that just forwards to the protected base method.
        """
        return super()._trigger(
            data,
            dataset_id=dataset_id,
            include_errors=include_errors,
            extra_params=extra_params,
        )


__all__ = ["XScraper"]
