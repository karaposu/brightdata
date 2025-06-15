#!/usr/bin/env python3
"""
brightdata.ready_scrapers.linkedin.scraper
------------------------------------------
Wrapper around Bright Data’s three LinkedIn datasets.
"""

from __future__ import annotations
import re, asyncio
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlparse

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# dataset-ids
_DATASET_PEOPLE   = "gd_l1viktl72bvl7bjuj0"
_DATASET_COMPANY  = "gd_l1vikfnt1wgvvqz95w"
_DATASET_JOBS     = "gd_lpfll7v5hcqtkxl6l"
_DEFAULT_DATASET  = _DATASET_PEOPLE


@register("linkedin")
class LinkedInScraper(BrightdataBaseSpecializedScraper):
    """One class that wraps all LinkedIn datasets."""

    _RX_PEOPLE  = re.compile(r"^/(in|pub)/[^/]+/?", re.I)
    _RX_COMPANY = re.compile(r"^/company/[^/]+/?",  re.I)
    _RX_JOB     = re.compile(r"^/jobs/view/",       re.I)

    # ───────────────────────── constructor ─────────────────────────
    def __init__(self, bearer_token: Optional[str] = None, **kw):
        super().__init__(_DEFAULT_DATASET, bearer_token, **kw)

    # ══════════════════════════════════════════════════════════════
    # 0. SMART ROUTER
    # ══════════════════════════════════════════════════════════════
    def collect_by_url(self, urls: Sequence[str]) -> Dict[str, str]:
        buckets: dict[str, List[str]] = {"people": [], "company": [], "job": []}
        for u in urls:
            kind = self._classify(u)
            if not kind:
                raise ValueError(f"Unrecognised LinkedIn URL: {u}")
            buckets[kind].append(u)

        self._url_buckets = {k: v for k, v in buckets.items() if v}

        out: Dict[str, str] = {}
        if buckets["people"]:
            out["people"] = self.people_profiles__collect_by_url(buckets["people"])
        if buckets["company"]:
            out["company"] = self.company_information__collect_by_url(buckets["company"])
        if buckets["job"]:
            out["job"] = self.job_listing_information__collect_by_url(buckets["job"])
        return out

    def _classify(self, url: str) -> str | None:
        path = urlparse(url).path
        if self._RX_PEOPLE.match(path):  return "people"
        if self._RX_COMPANY.match(path): return "company"
        if self._RX_JOB.match(path):     return "job"
        return None

    # ─────────────────── PEOPLE: collect & discover ───────────────────
    def people_profiles__collect_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]
        return self.trigger(payload, dataset_id=_DATASET_PEOPLE)
    
    def people_profiles__discover_by_name(
        self,
        queries: Sequence[Dict[str, str]]
    ) -> str:
        """
        Discover LinkedIn profiles by full-name search.

        Parameters
        ----------
        queries : list of dict
            Each dict **must** have:
              - "first_name": str
              - "last_name":  str

        Returns
        -------
        str
            Bright Data snapshot-id; poll until ready to get list[dict].
        """
        # validate
        for i, q in enumerate(queries):
            if "first_name" not in q or "last_name" not in q:
                raise ValueError(
                    f"Query at index {i} missing 'first_name' or 'last_name': {q}"
                )

        # payload is exactly what the API expects
        payload = [{"first_name": q["first_name"], "last_name": q["last_name"]} 
                   for q in queries]

        return self.trigger(
            payload,
            dataset_id=_DATASET_PEOPLE,
            extra_params={
                "type":        "discover_new",
                "discover_by": "name",
            },
        )
    # ─────────────────── COMPANY: collect ─────────────────────────────
    def company_information__collect_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]
        return self.trigger(payload, dataset_id=_DATASET_COMPANY)

    # ─────────────────── JOB: collect & discover ─────────────────────
    def job_listing_information__collect_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]
        return self.trigger(payload, dataset_id=_DATASET_JOBS)

    def job_listing_information__discover_by_keyword(
        self, queries: Sequence[Dict[str, Any]]
    ) -> str:
        return self.trigger(
            list(queries),
            dataset_id=_DATASET_JOBS,
            extra_params={"type": "discover_new", "discover_by": "keyword"},
        )

    # (other stubs can be filled later)
    def job_listing_information__discover_by_url(self, q):  ...
    def posts__collect_by_url(self, q):                     ...
    def posts__discover_by_company_url(self, q):            ...
    def posts__discover_by_profile_url(self, q):            ...
    def posts__discover_by_url(self, q):                    ...
    def people_search__collect_by_url(self, q):             ...

    # =================================================================
    # Async variants – unchanged, just keep using _trigger_async
    # =================================================================
    async def collect_by_url_async(self, urls: Sequence[str]) -> Dict[str, str]:
        buckets = self._url_buckets = defaultdict(list)
        for u in urls:
            kind = self._classify(u)
            if not kind:
                raise ValueError(f"Unrecognised LinkedIn URL: {u}")
            buckets[kind].append(u)

        tasks: Dict[str, asyncio.Task[str]] = {}
        if buckets["people"]:
            tasks["people"] = asyncio.create_task(
                self._trigger_async([{"url": u} for u in buckets["people"]], _DATASET_PEOPLE)
            )
        if buckets["company"]:
            tasks["company"] = asyncio.create_task(
                self._trigger_async([{"url": u} for u in buckets["company"]], _DATASET_COMPANY)
            )
        if buckets["job"]:
            tasks["job"] = asyncio.create_task(
                self._trigger_async([{"url": u} for u in buckets["job"]], _DATASET_JOBS)
            )

        snaps = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), snaps))

    # individual async wrappers (examples)
    async def people_profiles__collect_by_url_async(self, urls: Sequence[str]) -> str:
        return await self._trigger_async([{"url": u} for u in urls], _DATASET_PEOPLE)

    async def company_information__collect_by_url_async(self, urls: Sequence[str]) -> str:
        return await self._trigger_async([{"url": u} for u in urls], _DATASET_COMPANY)

    async def job_listing_information__collect_by_url_async(self, urls: Sequence[str]) -> str:
        return await self._trigger_async([{"url": u} for u in urls], _DATASET_JOBS)

