#!/usr/bin/env python3
"""
brightdata.ready_scrapers.reddit.scraper
========================================

Unofficial wrapper around Bright Data’s **Reddit** datasets.

Implemented endpoints
---------------------

===============================  Dataset-ID                          Python method
-------------------------------- ---------------------------------- ----------------------------------------------
posts__collect_by_url            «gd_lvz8ah06191smkebj4»             posts__collect_by_url()
posts__discover_by_keyword       «gd_lvz8ah06191smkebj4»             posts__discover_by_keyword()
posts__discover_by_subreddit_url «gd_lvz8ah06191smkebj4»             posts__discover_by_subreddit_url()
comments__collect_by_url         «gd_lvzdpsdlw09j6t702»             comments__collect_by_url()

All calls run in **async mode** (`sync_mode=async`) – every method returns a
*snapshot-id* immediately.  Poll that id (e.g. `poll_until_ready`) to obtain
the JSON rows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union, Dict

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register
from urllib.parse import urlparse

# --------------------------------------------------------------------------- #
# Static dataset-ids (taken from your sample API calls)
# --------------------------------------------------------------------------- #
_DATASET = {
    "posts":    "gd_lvz8ah06191smkebj4",
    "comments": "gd_lvzdpsdlw09j6t702",
}


@register("reddit")  # registry matches “reddit” in the domain
class RedditScraper(BrightdataBaseSpecializedScraper):
    """
    ---
    agent_id: reddit
    title: RedditScraper
    desc: >
      One class that wraps Bright Data’s “collect / discover posts” and
      “collect comments” Reddit datasets.
    example: |
      from brightdata.ready_scrapers.reddit import RedditScraper
      s = RedditScraper()                                 # token from .env
      snap = s.posts__collect_by_url(
          ["https://www.reddit.com/r/singularity/comments/1cmoa52/..."]
      )
    ---
    """

    # ------------------------------------------------------------------ #
    # ctor – bearer_token optional
    # ------------------------------------------------------------------ #
    def __init__(self, bearer_token: Optional[str] = None, **kw):
        super().__init__(_DATASET["posts"], bearer_token, **kw)

    
    def collect_by_url(
        self,
        urls: Sequence[str],
    ) -> Union[str, Dict[str, str]]:
        """
        Auto-dispatch raw Reddit URLs to the right endpoint:

        • URLs containing "/comment/" → comments__collect_by_url  
        • everything else         → posts__collect_by_url

        Returns a single snapshot-id if all URLs went to one bucket,
        or a dict {"posts": id1, "comments": id2} if both were used.
        """
        post_urls = []
        comment_urls = []
        for u in urls:
            path = urlparse(u).path
            if "/comment/" in path:
                comment_urls.append(u)
            else:
                post_urls.append(u)

        results: Dict[str, str] = {}
        if post_urls:
            results["posts"] = self.posts__collect_by_url(post_urls)
        if comment_urls:
            results["comments"] = self.comments__collect_by_url(comment_urls)

        # if only one bucket was used, return its snapshot-id directly
        if len(results) == 1:
            return next(iter(results.values()))
        return results

    # ****************************************************************** #
    # 1.  posts__collect_by_url
    # ****************************************************************** #
    def posts__collect_by_url(self, post_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: posts__collect_by_url
        desc: Scrape specific Reddit posts or threads by full URL.
        params:
          post_urls:
            type: list[str]
            desc: Full post URLs.
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.posts__collect_by_url([
            "https://www.reddit.com/r/battlefield2042/comments/1cmqs1d/..."
          ])
        ---
        """
        payload = [{"url": u} for u in post_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts"],
            extra_params={"sync_mode": "async"},
        )

    # ****************************************************************** #
    # 2.  posts__discover_by_keyword
    # ****************************************************************** #
    def posts__discover_by_keyword(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        ---
        endpoint: posts__discover_by_keyword
        desc: Search Reddit for posts matching one or several keywords.
        params:
          queries:
            type: list[dict]
            desc: |
              Each dict may include:
                keyword        (required, str)
                date           "All time" | "Past year" | ...
                num_of_posts   int (optional)
                sort_by        "Hot" | "Top" | "New" | "Rising"
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.posts__discover_by_keyword([
            {"keyword":"datascience","date":"All time","sort_by":"Hot"}
          ])
        ---
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["posts"],
            extra_params={
                "sync_mode":   "async",
                "type":        "discover_new",
                "discover_by": "keyword",
            },
        )

    # ****************************************************************** #
    # 3.  posts__discover_by_subreddit_url
    # ****************************************************************** #
    def posts__discover_by_subreddit_url(
        self,
        queries: Sequence[Dict[str, Any]],
    ) -> str:
        """
        ---
        endpoint: posts__discover_by_subreddit_url
        desc: Crawl multiple posts from one or more subreddit URLs.
        params:
          queries:
            type: list[dict]
            desc: |
              Keys Bright Data accepts:
                url            (required, str)
                sort_by        "Hot" | "New" | "Rising" | "Top"
                sort_by_time   "Today" | "Past week" | "All Time" | ""
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.posts__discover_by_subreddit_url([
            {"url":"https://www.reddit.com/r/datascience/",
             "sort_by":"Rising","sort_by_time":"All Time"}
          ])
        ---
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["posts"],
            extra_params={
                "sync_mode":   "async",
                "type":        "discover_new",
                "discover_by": "subreddit_url",
            },
        )

    # ****************************************************************** #
    # 4.  comments__collect_by_url
    # ****************************************************************** #
    def comments__collect_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        ---
        endpoint: comments__collect_by_url
        desc: Scrape comment threads or single comments by URL.
        params:
          queries:
            type: list[dict]
            desc: |
              Allowed keys:
                url               (required, str)
                days_back         int
                load_all_replies  bool
                comment_limit     int or ""
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.comments__collect_by_url([
            {"url":"https://www.reddit.com/r/singularity/comments/1cmoa52/comment/l31pwza/",
             "days_back":30,"load_all_replies":false,"comment_limit":5}
          ])
        ---
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET["comments"],
            extra_params={"sync_mode": "async"},
        )

   
    



