#!/usr/bin/env python3
"""
brightdata.ready_scrapers.instagram.scraper
===========================================

Unofficial wrapper around Bright Data’s Instagram datasets.

Implemented endpoints
---------------------
# profiles__collect_by_url
# posts__collect_by_url
# posts__discover_by_url
# reels__collect_by_url
# reels__discover_by_url
# reels__discover_by_url_all_reels
# comments__collect_by_url




All calls force `sync_mode=async`, therefore **every method immediately  
returns a *snapshot-id* string**.  Run the snapshot through one of the  
poll-helpers to receive the final JSON rows.

Example
-------
>>> from brightdata.ready_scrapers.instagram import InstagramScraper  
>>> s = InstagramScraper()                             # token from .env  
>>> snap = s.collect_profiles_by_url(  
...     ["https://www.instagram.com/cats_of_world_/"]  
... )  
>>> rows = poll_until_ready(s, snap).data               # list[dict]  
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence, Optional

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register
from urllib.parse import urlparse


# {"url":"https://www.instagram.com/cats_of_instagram/reel/C4GLo_eLO2e/"},
# {"url":"https://www.instagram.com/catsofinstagram/p/CesFC7JLyFl/?img_index=1"},
# {"url":"https://www.instagram.com/cats_of_instagram/reel/C2TmNOVMSbG/"},


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
    ---
    agent_id: instagram
    title: InstagramScraper
    desc: >
      High-level client for Bright Data’s Instagram endpoints.
      Each method returns immediately with a snapshot-id.
    example: |
      from brightdata.ready_scrapers.instagram import InstagramScraper
      s = InstagramScraper()
      snap = s.collect_profiles_by_url([
        "https://www.instagram.com/cats_of_world_/"
      ])
      # then poll with poll_until_ready(s, snap)
    ---
    """

    def __init__(self, bearer_token: Optional[str] = None, **kw):
        """
        ---
        endpoint: constructor
        desc: Instantiate an InstagramScraper; bearer_token is optional.
        params:
          bearer_token:
            type: str
            desc: Bright Data API token (reads from BRIGHTDATA_TOKEN if None).
          kw:
            type: dict
            desc: Extra keyword-args forwarded to the base class.
        returns:
          type: InstagramScraper
          desc: A configured scraper instance.
        ---
        """
        super().__init__(_DATASET["profiles"], bearer_token, **kw)

    # ------------------------------------------------------------------ #
    # SMART COLLECT ROUTER
    # ------------------------------------------------------------------ #
    def collect_by_url(
        self,
        urls: Sequence[str],
        *,
        include_comments: bool = False,
    ) -> Dict[str, str]:
        """
        Smart one-call entry point.

        • Detects whether each URL is a *profile*, *post* or *reel*  
        • If **include_comments=True** all post / reel URLs are fetched
          **via the comments dataset** instead of the post / reel datasets.

        Parameters
        ----------
        urls : list[str]
            Any mix of profile / post / reel links.
        include_comments : bool, default **False**
            *False* ⇒ get the post/reel objects themselves.  
            *True*  ⇒ get the complete comment thread instead.

        Returns
        -------
        dict[str, str]
            Mapping ``bucket → snapshot_id``  
            (`bucket` ∈ {"profiles", "posts", "reels", "comments"} –  
            only the ones actually triggered are present).
        """
        # Buckets for the three canonical datasets (+comments)
        profiles, posts, reels, comments = [], [], [], []

        for url in urls:
            path = urlparse(url).path.lower()
            if "/reel/" in path:
                # treat as reel – but may get redirected to *comments*
                (comments if include_comments else reels).append(url)
            elif "/p/" in path:
                # treat as image-post
                (comments if include_comments else posts).append(url)
            else:
                profiles.append(url)

        results: Dict[str, str] = {}

        # ---- trigger the necessary sub-jobs ---------------------------
        if profiles:
            results["profiles"] = self.profiles__collect_by_url(profiles)

        if posts:
            results["posts"] = self.posts__collect_by_url(posts)

        if reels:
            results["reels"] = self.reels__collect_by_url(reels)

        if comments:
            # Bright Data expects *payload objects*, not just raw URLs.
            payload = [
                {
                    "url": u,
                    "days_back": "",
                    "load_all_replies": False,
                    "comment_limit": ""
                }
                for u in comments
            ]
            results["comments"] = self.comments__collect_by_url(payload)

        return results
   


    def profiles__collect_by_url(self, urls: Sequence[str]) -> str:
        """
        ---
        endpoint: profiles__collect_by_url
        desc: Scrape Instagram profile pages (followers, bio, counters).
        params:
          urls:
            type: list[str]
            desc: Full profile URLs.
        returns:
          type: str
          desc: snapshot_id; poll until ready to get list[dict].
        example: |
          snap = scraper.profiles__collect_by_url([
            "https://www.instagram.com/cats_of_world_/"
          ])
        ---
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["profiles"],
            extra_params={"sync_mode": "async"},
        )

    def posts__collect_by_url(self, urls: Sequence[str]) -> str:
        """
        ---
        endpoint: posts__collect_by_url
        desc: Scrape individual Instagram posts (images or reels).
        params:
          urls:
            type: list[str]
            desc: Post URLs starting with /p/ or /reel/.
        returns:
          type: str
          desc: snapshot_id; poll until ready to get list[dict].
        example: |
          snap = scraper.posts__collect_by_url([
            "https://www.instagram.com/p/Cuf4s0MNqNr",
            "https://www.instagram.com/reel/Cuvy6JbtyQ6"
          ])
        ---
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts"],
            extra_params={"sync_mode": "async"},
        )

    def posts__discover_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        ---
        endpoint: posts__discover_by_url
        desc: Crawl multiple posts from profile / hashtag / tagged feeds.
        params:
          queries:
            type: list[dict]
            desc: |
              Each dict forwarded verbatim to Bright Data.  
              Keys:
                - url (str, required): profile/hashtag/tagged URL  
                - num_of_posts (int): max posts  
                - start_date (MM-DD-YYYY)  
                - end_date (MM-DD-YYYY)  
                - post_type (\"Post\"|\"Reel\"|\"\")  
                - posts_to_not_include (list[str]): IDs  
        returns:
          type: str
          desc: snapshot_id; poll until ready to get list[dict].
        example: |
          snap = scraper.posts__discover_by_url([{
            "url":"https://www.instagram.com/meta/",
            "num_of_posts":10,
            "post_type":"Reel",
            "start_date":"01-01-2025",
            "end_date":"03-01-2025"
          }])
        ---
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
    
    def reels__collect_by_url():
        pass

   

    def reels__discover_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        ---
        endpoint: reels__discover_by_url
        desc: Fetch recent reels for multiple accounts.
        params:
          queries:
            type: list[dict]
            desc: |
              Same structure as discover_posts_by_url, but only reels:
                - url (str): profile link  
                - num_of_posts (int)  
                - start_date (MM-DD-YYYY)  
                - end_date (MM-DD-YYYY)
        returns:
          type: str
          desc: snapshot_id; poll until ready to get list[dict].
        example: |
          snap = scraper.reels__discover_by_url([{
            "url":"https://www.instagram.com/espn",
            "num_of_posts":5,
            "start_date":"","end_date":""
          }])
        ---
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


    def reels__discover_by_url_all_reels(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        ---
        endpoint: reels__discover_by_url_all_reels
        desc: Crawl the complete reel history of each account.
        params:
          queries:
            type: list[dict]
            desc: |
              Same fields as discover_reels_by_url, but retrieves *all* reels.
                - url (str)  
                - num_of_posts (int; leave empty for all)  
                - start_date, end_date (MM-DD-YYYY)
        returns:
          type: str
          desc: snapshot_id; poll until ready to get list[dict].
        example: |
          snap = scraper.reels__discover_by_url_all_reels([{
            "url":"https://www.instagram.com/billieeilish",
            "num_of_posts":20
          }])
        ---
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
    

    def comments__collect_by_url(self, post_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: comments__collect_by_url
        desc: Retrieve all comments for the given post or reel URLs.
        params:
          post_urls:
            type: list[str]
            desc: URLs of posts or reels.
        returns:
          type: str
          desc: snapshot_id; poll until ready to get list[dict].
        example: |
          snap = scraper.comments__collect_by_url([
            "https://www.instagram.com/p/Cuf4s0MNqNr"
          ])
        ---
        """
        payload = [{"url": u} for u in post_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["comments"],
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
        # internal passthrough to BrightdataBaseSpecializedScraper._trigger
        return super()._trigger(
            data,
            dataset_id=dataset_id,
            include_errors=include_errors,
            extra_params=extra_params,
        )


# __all__ = ["InstagramScraper"]
