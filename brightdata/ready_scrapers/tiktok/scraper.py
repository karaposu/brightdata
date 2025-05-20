#!/usr/bin/env python3
"""
brightdata.ready_scrapers.tiktok.scraper
========================================

High-level wrapper around Bright Data’s **TikTok** datasets.

Implemented endpoints
---------------------

==============================  Dataset-ID                           Method
------------------------------  -----------------------------------  -------------------------------
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

# Static Bright-Data dataset IDs
_DATASET = {
    "comments":           "gd_lkf2st302ap89utw5k",
    "posts_fast":         "gd_lkf2st302ap89utw5k",
    "posts_profile_fast": "gd_m7n5v2gq296pex2f5m",
    "posts_search_fast":  "gd_m7n5v2gq296pex2f5m",
    "profiles":           "gd_l1villgoiiidt09ci",
    "posts":              "gd_lu702nij2f790tmv9h",
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

        
        #profiles__collect_by_url
        #profiles__discover_by_search_url
        # posts__collect_by_url

        # posts__discover_by_keyword


        # posts__discover_by_profile_url
        # posts__discover_by_url
        # shop__collect_by_url
        # shop__discover_by_category
        # comments__collect_by_url
        # posts_by_url_fast_api__collect_by_url
        # posts_by_profile_fast_api__collect_by_url
        # posts_by_search_url_fast_api__collect_by_url
        
    def profiles__collect_by_url(self, profile_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: profiles__collect_by_url
        desc: Scrape TikTok profile metadata (followers, bio, stats).
        params:
          profile_urls:
            type: list[str]
            desc: Profile URLs, e.g. "https://www.tiktok.com/@fofimdmell".
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
    

    

    def posts__collect_by_url(self, post_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: posts__collect_by_url
        desc: Fast-API variant to scrape one or many TikTok post objects.
        params:
          post_urls:
            type: list[str]
            desc: TikTok post URLs (same format as collect_comments_by_url).
        returns:
          type: str
          desc: snapshot_id – poll until ready to retrieve post JSON.
        example: |
          snap = scraper.posts__collect_by_url([
            "https://www.tiktok.com/@mmeowmmia/video/7077929908365823237"
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
            desc: Use "#tag" for hashtags or plain text.
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
    

    def posts__discover_by_url():
        pass
    
    def shop__collect_by_url():
        pass
    

    def shop__discover_by_category():
        pass
    
    def comments__collect_by_url(self, post_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: collect_comments_by_url
        desc: Retrieve comments for specified TikTok post URLs.
        params:
          post_urls:
            type: list[str]
            desc: Full TikTok post URLs, e.g. ".../video/<id>".
        returns:
          type: str
          desc: snapshot_id – poll this until ready to fetch results.
        example: |
          snap = scraper.collect_comments_by_url([
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

    
    def posts_by_url_fast_api__collect_by_url():
        pass
    
    def posts_by_profile_fast_api__collect_by_url():
        pass
    
    def posts_by_search_url_fast_api__collect_by_url():
        pass
    

    

     

    def _trigger(  # noqa: D401
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


    
    
    def collect_posts_by_profile_fast(self, profile_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: collect_posts_by_profile_fast
        desc: Fetch latest posts from profile URLs via fast-API.
        params:
          profile_urls:
            type: list[str]
            desc: TikTok profile URLs, e.g. "https://www.tiktok.com/@bbc".
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.collect_posts_by_profile_fast([
            "https://www.tiktok.com/@bbc"
          ])
        ---
        """
        payload = [{"url": u} for u in profile_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts_profile_fast"],
            extra_params={"sync_mode": "async"},
        )
    
    def collect_posts_by_search_url_fast(self, search_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: collect_posts_by_search_url_fast
        desc: Crawl search-results feeds via TikTok fast-API.
        params:
          search_urls:
            type: list[str]
            desc: Full TikTok search URLs, e.g. ".../search?q=music".
        returns:
          type: str
          desc: snapshot_id
        example: |
          snap = scraper.collect_posts_by_search_url_fast([
            "https://www.tiktok.com/search?q=music"
          ])
        ---
        """
        payload = [{"url": u} for u in search_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET["posts_search_fast"],
            extra_params={"sync_mode": "async"},
        )
  
    

   

    
