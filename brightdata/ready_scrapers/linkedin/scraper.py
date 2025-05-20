#!/usr/bin/env python3
"""
brightdata.ready_scrapers.linkedin.scraper
==========================================

One wrapper for Bright Data’s three LinkedIn datasets:

* **People profile**               →  gd_l1viktl72bvl7bjuj0  
* **Company information**          →  gd_l1vikfnt1wgvvqz95w  
* **Job-listing information**      →  gd_lpfll7v5hcqtkxl6l  

Highlights
----------
* `collect_by_url()` auto-detects the entity type from the path and calls
  the specialised method for you.  
* All calls run with `sync_mode=async` → return **snapshot-id** strings.
"""

from __future__ import annotations
import re
from collections import defaultdict
from typing import Any, Dict, List, Sequence, DefaultDict, Optional
from urllib.parse import urlparse

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# Bright-Data dataset IDs (static)
_DATASET_PEOPLE   = "gd_l1viktl72bvl7bjuj0"
_DATASET_COMPANY  = "gd_l1vikfnt1wgvvqz95w"
_DATASET_JOBS     = "gd_lpfll7v5hcqtkxl6l"
# default id for connectivity checks
_DEFAULT_DATASET  = _DATASET_PEOPLE


@register("linkedin")
class LinkedInScraper(BrightdataBaseSpecializedScraper):
    """
    ---
    agent_id: linkedin
    title: LinkedInScraper
    desc: |
      Unified LinkedIn scraper – wraps the people, company and job Bright-Data
      datasets.  Each method immediately returns a snapshot-id.
    example: |
      from brightdata.ready_scrapers.linkedin import LinkedInScraper
      s = LinkedInScraper()
      snaps = s.collect_by_url([
        "https://www.linkedin.com/in/elonmusk/",
        "https://www.linkedin.com/company/openai/",
        "https://www.linkedin.com/jobs/view/4231516747/"
      ])
      # → {'people': 's_xxx', 'company': 's_yyy', 'job': 's_zzz'}
    ---
    """

    def __init__(self, bearer_token: Optional[str] = None, **kw):
        """
        ---
        endpoint: constructor
        desc: Instantiate a LinkedInScraper; bearer_token optional.
        params:
          bearer_token:
            type: str
            desc: Bright Data API token (reads BRIGHTDATA_TOKEN if None)
          kw:
            type: dict
            desc: Extra kwargs forwarded to base class
        returns:
          type: LinkedInScraper
          desc: Configured scraper instance
        ---
        """
        super().__init__(_DEFAULT_DATASET, bearer_token, **kw)

    _RX_PEOPLE  = re.compile(r"^/(in|pub)/[^/]+/?", re.I)
    _RX_COMPANY = re.compile(r"^/company/[^/]+/?",  re.I)
    _RX_JOB     = re.compile(r"^/jobs/view/",       re.I)

    def collect_by_url(self, urls: Sequence[str]) -> Dict[str, str]:
        """
        ---
        endpoint: collect_by_url
        desc: |
          Auto-detect the LinkedIn entity type for each URL and dispatch
          them to the proper collect_* method.
        params:
          urls:
            type: list[str]
            desc: People, company or job URLs (mixed allowed)
        returns:
          type: dict[str,str]
          desc: Mapping of {'people','company','job'} → snapshot_id
        example: |
          snap_map = scraper.collect_by_url([
            "https://www.linkedin.com/in/enes-kuzucu/",
            "https://www.linkedin.com/company/105448508/",
            "https://www.linkedin.com/jobs/view/4231516747/"
          ])
        notes:
          mapping: Stored in self._url_buckets for auto.scrape_url support.
        ---
        """
        buckets: DefaultDict[str, List[str]] = defaultdict(list)
        for u in urls:
            kind = self._classify(u)
            if not kind:
                raise ValueError(f"Unrecognised LinkedIn URL: {u}")
            buckets[kind].append(u)
        # expose for brightdata.auto
        self._url_buckets = dict(buckets)

        results: Dict[str, str] = {}
        if buckets.get("people"):
            results["people"] = self.people_profiles__collect_by_url(buckets["people"])
        if buckets.get("company"):
            results["company"] = self.company_information__collect_by_url(buckets["company"])
        if buckets.get("job"):
            results["job"] = self.job_listing_information__collect_by_url(buckets["job"])
        return results

    def _classify(self, url: str) -> str | None:
        path = urlparse(url).path
        if self._RX_PEOPLE.match(path):
            return "people"
        if self._RX_COMPANY.match(path):
            return "company"
        if self._RX_JOB.match(path):
            return "job"
        return None
         
    def people_profiles__collect_by_url(self, urls: Sequence[str]) -> str:
        """
        ---
        endpoint: people_profiles__collect_by_url
        desc: Scrape individual LinkedIn profile pages.
        params:
          urls:
            type: list[str]
            desc: Profile URLs (e.g. /in/username).
        returns:
          type: str
          desc: snapshot_id; poll until ready to get list[dict].
        example: |
          snap = scraper.people_profiles__collect_by_url([
            "https://www.linkedin.com/in/elad-moshe-05a90413/"
          ])
        ---
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET_PEOPLE,
            extra_params={"sync_mode": "async"},
        )
    
    
    def people_profiles__discover_by_name(self, names: Sequence[str]) -> str:
        """
        ---
        endpoint: people_profiles__discover_by_name
        desc: Discover profile pages by full-name search.
        params:
          names:
            type: list[str]
            desc: Full names to search.
        returns:
          type: str
          desc: snapshot_id.
        example: |
          snap = scraper.people_profiles__discover_by_name(["Elad Moshe", "Aviv Tal"])
        ---
        """
        payload = [{"name": n} for n in names]
        return self._trigger(
            payload,
            dataset_id=_DATASET_PEOPLE,
            extra_params={
                "type":        "discover_new",
                "discover_by": "name",
                "sync_mode":   "async",
            },
        )


    
    def company_information__collect_by_url(self, urls: Sequence[str]) -> str:
        """
        ---
        endpoint: company_information__collect_by_url
        desc: Scrape LinkedIn company pages.
        params:
          urls:
            type: list[str]
            desc: Company page URLs.
        returns:
          type: str
          desc: snapshot_id.
        example: |
          snap = scraper.company_information__collect_by_url([
            "https://www.linkedin.com/company/bright-data"
          ])
        ---
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET_COMPANY,
            extra_params={"sync_mode": "async"},
        )


    
    def job_listing_information__collect_by_url(self, urls: Sequence[str]) -> str:
        """
        ---
        endpoint: job_listing_information__collect_by_url
        desc: Scrape individual LinkedIn job-post URLs.
        params:
          urls:
            type: list[str]
            desc: Job listing URLs.
        returns:
          type: str
          desc: snapshot_id.
        example: |
          snap = scraper.job_listing_information__collect_by_url([
            "https://www.linkedin.com/jobs/view/4181034038/"
          ])
        ---
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET_JOBS,
            extra_params={"sync_mode": "async"},
        )

     
    def job_listing_information__discover_by_keyword(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        ---
        endpoint: job_listing_information__discover_by_keyword
        desc: Discover job listings via keyword / location search.
        params:
          queries:
            type: list[dict]
            desc: |
              Each dict must match Bright Data’s expected payload, e.g.:
                {"location":"Paris",
                 "keyword":"python developer",
                 "country":"FR", ...}
        returns:
          type: str
          desc: snapshot_id.
        example: |
          snap = scraper.job_listing_information__discover_by_keyword([{
            "location":"New York",
            "keyword":"Data Scientist",
            "country":"US"
          }])
        ---
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET_JOBS,
            extra_params={
                "type":        "discover_new",
                "discover_by": "keyword",
                "sync_mode":   "async",
            },
        )
    
    def job_listing_information__discover_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
       pass
    
    def posts__collect_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
       pass
    
    def posts__discover_by_company_url(self, queries: Sequence[Dict[str, Any]]) -> str:
       pass
    
    def posts__discover_by_profile_url(self, queries: Sequence[Dict[str, Any]]) -> str:
       pass
    def posts__discover_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
       pass
    def people_search__collect_by_url(self, queries: Sequence[Dict[str, Any]]) -> str:
       pass
    

        

    