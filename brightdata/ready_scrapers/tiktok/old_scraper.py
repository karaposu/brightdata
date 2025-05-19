"""
brightdata.ready_scrapers.tiktok.scraper
========================================

High-level wrapper around Bright Data’s **TikTok** datasets.

Implemented endpoints
---------------------

==============================  Dataset-ID                           Method
------------------------------  -----------------------------------  --------------------------------------------
tiktok_comments__collect_by_url «gd_lkf2st302ap89utw5k»              collect_comments_by_url()
tiktok_posts_by_url_fast_api    «gd_lkf2st302ap89utw5k»              collect_posts_by_url_fast()
tiktok_posts_by_profile_fast…   «gd_m7n5v2gq296pex2f5m»              collect_posts_by_profile_fast()
tiktok_posts_by_search_url…     «gd_m7n5v2gq296pex2f5m»              collect_posts_by_search_url_fast()
tiktok_profiles__collect_by_url «gd_l1villgoiiidt09ci»               collect_profiles_by_url()
tiktok_profiles__discover…      «gd_l1villgoiiidt09ci»               discover_profiles_by_search_url()
tiktok_posts__collect_by_url    «gd_lu702nij2f790tmv9h»              collect_posts_by_url()
tiktok_posts__discover_*        «gd_lu702nij2f790tmv9h»              discover_posts_by_keyword() / discover_posts_by_profile_url()
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence
from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# --------------------------------------------------------------------------- #
# Static dataset-IDs (taken from the examples you supplied)
# --------------------------------------------------------------------------- #
_DATASET = {
    "comments":             "gd_lkf2st302ap89utw5k",
    "posts_fast":           "gd_lkf2st302ap89utw5k",   # same as comments
    "posts_profile_fast":   "gd_m7n5v2gq296pex2f5m",
    "posts_search_fast":    "gd_m7n5v2gq296pex2f5m",   # same dataset – diff URLs
    "profiles":             "gd_l1villgoiiidt09ci",
    "posts":                "gd_lu702nij2f790tmv9h",
}

# Register just the *domain keyword*; registry maps every “tiktok.com” URL
@register("tiktok")
class TikTokScraper(BrightdataBaseSpecializedScraper):
    """
    Ready-made Bright Data client for the various TikTok datasets.
    """

    # ──────────────────────────────────────────────────────────────
    # ctor – default to the profiles dataset for connectivity tests
    # ──────────────────────────────────────────────────────────────
    def __init__(self, bearer_token: Optional[str] = None, **kw):
        super().__init__(_DATASET["profiles"], bearer_token, **kw)

    # ********************************************************************** #
    # 1.  COMMENTS
    # ********************************************************************** #
    def collect_comments_by_url(self, post_urls: Sequence[str]) -> str:
        """
        Retrieve **comments** for the specified post / reel URLs.

        Parameters
        ----------
        post_urls : sequence[str]
            Must each point directly at an individual TikTok post
            (``.../video/<id>``).

        Returns
        -------
        snapshot_id : str
        """
        payload = [{"url": u} for u in post_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["comments"],
            extra_params={"sync_mode": "async"},
        )

    # ********************************************************************** #
    # 2.  FAST POST ENDPOINTS
    # ********************************************************************** #
    def collect_posts_by_url_fast(self, post_urls: Sequence[str]) -> str:
        """
        **Fast-API** variant – scrape one or many individual posts.

        Same payload as :py:meth:`collect_comments_by_url` but returns the
        *post* object(s) instead of the comment thread.
        """
        payload = [{"url": u} for u in post_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts_fast"],
            extra_params={"sync_mode": "async"},
        )

    def collect_posts_by_profile_fast(self, profile_urls: Sequence[str]) -> str:
        """
        Collect the **latest posts** from each *profile URL* via the *fast API*.

        Bright Data crawls the first N posts shown on the profile page.

        Parameters
        ----------
        profile_urls : sequence[str]
            ``https://www.tiktok.com/@<username>`` links.

        Returns
        -------
        snapshot_id : str
        """
        payload = [{"url": u} for u in profile_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts_profile_fast"],
            extra_params={"sync_mode": "async"},
        )

    def collect_posts_by_search_url_fast(self, search_urls: Sequence[str]) -> str:
        """
        Crawl result feeds returned by TikTok’s **search URLs** (fast API).

        Parameters
        ----------
        search_urls : sequence[str]
            e.g. ``https://www.tiktok.com/search?q=music``

        Returns
        -------
        snapshot_id : str
        """
        payload = [{"url": u} for u in search_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts_search_fast"],
            extra_params={"sync_mode": "async"},
        )

    # ********************************************************************** #
    # 3.  PROFILES
    # ********************************************************************** #
    def collect_profiles_by_url(self, profile_urls: Sequence[str]) -> str:
        """
        Scrape **profile metadata** (followers, bio, stats …).

        Payload accepts an optional ``country`` key per object, leave empty
        for *auto*:

        ``[{"url": ".../@bbc", "country": ""}, ...]``
        """
        payload = [{"url": u, "country": ""} for u in profile_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["profiles"],
            extra_params={"sync_mode": "async"},
        )

    def discover_profiles_by_search_url(self, queries: Sequence[Dict[str, str]]) -> str:
        """
        Discover profiles from **search URLs**.

        Each dict must contain:

        ===========  =======================================================
        Key          Explanation
        -----------  -------------------------------------------------------
        ``search_url``  Full TikTok explore / search URL
        ``country``     ISO-2 country (``"US"``) or empty string
        ===========  =======================================================

        Example
        -------
        ``{"search_url": "https://www.tiktok.com/explore?lang=en", "country": "US"}``
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

    # ********************************************************************** #
    # 4.  STANDARD POST DATASET
    # ********************************************************************** #
    def collect_posts_by_url(self, post_urls: Sequence[str]) -> str:
        """
        Standard (non-fast) **collect posts by URL** endpoint.

        Accepts an optional ``country`` key per object – left empty here.
        """
        payload = [{"url": u, "country": ""} for u in post_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts"],
            extra_params={"sync_mode": "async"},
        )

    # ------------------------------------------------------------------ #
    def discover_posts_by_keyword(self, keywords: Sequence[str]) -> str:
        """
        Discover posts by **keyword / hashtag**.

        Parameters
        ----------
        keywords : sequence[str]
            Use ``"#artist"`` for hashtags or plain words for general search.

        Returns
        -------
        snapshot_id : str
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

    def discover_posts_by_profile_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        Discover posts by **profile URL**.

        Payload fields
        --------------
        ===============  ------------------------------------------------------------------
        ``url``          profile link (required)
        ``num_of_posts`` integer – 0 ⇒ no limit
        ``posts_to_not_include`` list[str] of post-IDs to skip
        ``what_to_collect`` ``"Posts"`` \| ``"Reposts"`` \| ``"Posts & Reposts"``
        ``start_date``   “MM-DD-YYYY” or empty
        ``end_date``     same
        ``post_type``    ``"Video"`` \| ``"Image"`` \| ``""`` (both)
        ``country``      ISO-2 code or empty
        ===============  ------------------------------------------------------------------

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

    # alias – Bright Data’s docs also call it “discover_by_url”
    discover_posts_by_url = discover_posts_by_profile_url  # type: ignore

    # ------------------------------------------------------------------ #
    # Internal passthrough
    # ------------------------------------------------------------------ #
    def _trigger(  # noqa: D401 – see base class
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


__all__ = ["TikTokScraper"]
