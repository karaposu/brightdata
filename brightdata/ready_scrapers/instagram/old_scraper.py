"""
brightdata.ready_scrapers.instagram.scraper
===========================================

Unofficial wrapper around Bright Data’s **Instagram** datasets.

Implemented endpoints
---------------------
* collect_profiles_by_url  → ``instagram_profiles__collect_by_url``
* collect_posts_by_url     → ``instagram_posts__collect_by_url``
* discover_posts_by_url    → ``instagram_posts__discover_by_url``
* collect_comments_by_url  → ``instagram_comments__collect_by_url``
* discover_reels_by_url    → ``instagram_reels__discover_by_url``
* discover_reels_all_by_url→ ``instagram_reels__discover_by_url_all_reels``

All calls force `sync_mode=async`, therefore **every method immediately
returns a *snapshot-id* string**.  
Run the snapshot through one of the poll-helpers to receive the final
JSON rows.

Example
-------
>>> from brightdata.ready_scrapers.instagram import InstagramScraper
>>> s = InstagramScraper()                             # token from .env
>>> snap = s.collect_profiles_by_url(
...     ["https://www.instagram.com/cats_of_world_/"])
>>> rows = poll_until_ready(s, snap).data              # list[dict]
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Optional

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# --------------------------------------------------------------------------- #
# Static dataset-IDs – harvested from the raw API examples you supplied
# --------------------------------------------------------------------------- #
_DATASET = {
    "profiles":  "gd_l1vikfch901nx3by4",   # instagram_profiles__collect_by_url
    "posts":     "gd_lk5ns7kz21pck8jpis",  # instagram_posts*  (collect / discover)
    "reels":     "gd_lyclm20il4r5helnj",   # instagram_reels*  (discover only)
    "comments":  "gd_ltppn085pokosxh13",   # instagram_comments__collect_by_url
}


@register("instagram")
class InstagramScraper(BrightdataBaseSpecializedScraper):
    """
    High-level client for every Instagram dataset Bright Data expose **today**.

    New datasets are usually a single extra method that calls
    :pymeth:`_trigger` – follow the patterns below.
    """

    # ------------------------------------------------------------------ #
    # ctor – we pass *any* valid dataset-id so the base class can perform
    # its optional connectivity HEAD request.  Individual methods always
    # override the ID with the correct value.
    # ------------------------------------------------------------------ #
    def __init__(self, bearer_token: Optional[str] = None, **kw):
        super().__init__(_DATASET["profiles"], bearer_token, **kw)

    # ────────────────────────────────────────────────────────────────────
    # 1.  PROFILES
    # ────────────────────────────────────────────────────────────────────
    def collect_profiles_by_url(self, urls: Sequence[str]) -> str:
        """
        Scrape **Instagram profile pages** (followers, bio, counters …).

        Parameters
        ----------
        urls :
            One or many profile links, e.g.
            ``["https://www.instagram.com/cats_of_world_/"]``

        Returns
        -------
        snapshot_id :
            ``str`` – pass to :pymeth:`get_data` or a poll-helper.
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["profiles"],
            extra_params={"sync_mode": "async"},
        )

    # ────────────────────────────────────────────────────────────────────
    # 2.  POSTS  (single-item scrape)
    # ────────────────────────────────────────────────────────────────────
    def collect_posts_by_url(self, urls: Sequence[str]) -> str:
        """
        Scrape one or more **individual Instagram posts** (images *or* reels).

        Parameters
        ----------
        urls :
            Links that start with ``/p/…`` for photos or ``/reel/…`` for reels.

        Returns
        -------
        snapshot_id : str
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts"],
            extra_params={"sync_mode": "async"},
        )

    # ------------------------------------------------------------------ #
    # 3.  POSTS  (bulk discovery)
    # ------------------------------------------------------------------ #
    def discover_posts_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        Crawl **many posts** from profile / hashtag / tagged feeds.

        Parameters
        ----------
        queries :
            An *iterable of dicts*.  
            **Each dict is forwarded 1-to-1 to Bright Data** and may contain
            the keys shown below (all strings unless noted).  *Omit a field or
            pass an empty string to use its default.*

            ===============  =============================================================
            Key              Meaning / accepted values
            ---------------  -------------------------------------------------------------
            ``url``          *(required)* profile / hashtag / tagged URL  
            ``num_of_posts`` max number of posts to fetch — **int**  
            ``start_date``   earliest date – format “MM-DD-YYYY” (e.g. ``"01-01-2025"``)
            ``end_date``     latest  date – same format
            ``post_type``    ``"Post"`` | ``"Reel"`` | ``""`` (both)
            ``posts_to_not_include`` list[str] of post-IDs to skip
            ===============  =============================================================

            Example
            ``{"url": "https://www.instagram.com/meta/",
               "num_of_posts": 20,
               "post_type": "Reel",
               "start_date": "", "end_date": ""}``

        Returns
        -------
        snapshot_id :
            ``str`` – poll with :pyfunc:`brightdata.utils.poll.poll_until_ready`.
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["posts"],
            extra_params={
                "sync_mode":   "async",
                "type":        "discover_new",
                "discover_by": "url",
            },
        )

    # ────────────────────────────────────────────────────────────────────
    # 4.  COMMENTS
    # ────────────────────────────────────────────────────────────────────
    def collect_comments_by_url(self, post_urls: Sequence[str]) -> str:
        """
        Retrieve **all comments** for the given posts / reels.

        Parameters
        ----------
        post_urls :
            Direct links to posts or reels, e.g.
            ``"https://www.instagram.com/p/Cuf4s0MNqNr"``

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

    # ────────────────────────────────────────────────────────────────────
    # 5.  REELS – recent subset
    # ────────────────────────────────────────────────────────────────────
    def discover_reels_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        Fetch the **recent reels** for multiple accounts in one go.

        Parameters
        ----------
        queries :
            Same structure as :pymeth:`discover_posts_by_url`, **but** Bright Data
            only looks at the *reel* tab of a profile and respects:

            * ``num_of_posts`` – int  
            * ``start_date`` & ``end_date`` – “MM-DD-YYYY”  
            * ``url`` – profile link

        Returns
        -------
        snapshot_id : str
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["reels"],
            extra_params={
                "sync_mode":   "async",
                "type":        "discover_new",
                "discover_by": "url",
            },
        )

    # ------------------------------------------------------------------ #
    # 6.  REELS – *all* reels
    # ------------------------------------------------------------------ #
    def discover_reels_all_by_url(
        self,
        queries: Sequence[Dict[str, Any]],
    ) -> str:
        """
        Crawl **the complete reel history** of each account.

        Parameters
        ----------
        queries :
            Same fields as :pymeth:`discover_reels_by_url`; Bright Data walks the
            *entire* reel timeline.  Useful keys:

            * ``url`` (required) – profile link  
            * ``num_of_posts`` – hard limit (leave empty ⇒ everything)  
            * ``start_date`` / ``end_date`` – optional date window

        Returns
        -------
        snapshot_id : str
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["reels"],
            extra_params={
                "sync_mode":   "async",
                "type":        "discover_new",
                "discover_by": "url_all_reels",
            },
        )

    # ------------------------------------------------------------------ #
    # INTERNAL – thin passthrough
    # ------------------------------------------------------------------ #
    def _trigger(  # noqa: D401 – description lives in base class
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



