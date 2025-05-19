"""
brightdata.ready_scrapers.linkedin.scraper
==========================================

One wrapper for Bright Data’s three LinkedIn datasets:

* **People profile**               →  gd_l1viktl72bvl7bjuj0
* **Company information**          →  gd_l1vikfnt1wgvvqz95w
* **Job-listing information**      →  gd_lpfll7v5hcqtkxl6l

Highlights
----------
* ``collect_by_url()`` auto-detects the entity type from the path and calls
  the specialised method for you.
* All calls run with ``sync_mode=async`` → return **snapshot-id** strings.
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

# default id for connectivity checks in the base class
_DEFAULT_DATASET  = _DATASET_PEOPLE


@register("linkedin")
class LinkedInScraper(BrightdataBaseSpecializedScraper):
    """
    Unified LinkedIn scraper – wraps the *people*, *company* and *job*
    Bright-Data datasets.

    Example
    -------
    >>> from brightdata.ready_scrapers.linkedin import LinkedInScraper
    >>> s = LinkedInScraper()  # token from .env
    >>> snap_map = s.collect_by_url([
    ...     "https://www.linkedin.com/in/elonmusk/",
    ...     "https://www.linkedin.com/company/openai/",
    ...     "https://www.linkedin.com/jobs/view/4231516747/"
    ... ])
    >>> # snap_map → {'people': 's_…', 'company': 's_…', 'job': 's_…'}
    """

    # ------------------------------------------------------------------ #
    # Ctor – bearer_token optional
    # ------------------------------------------------------------------ #
    def __init__(self, bearer_token: Optional[str] = None, **kw):
        super().__init__(_DEFAULT_DATASET, bearer_token, **kw)

    # ---------- internal URL classification helpers ------------------ #
    _RX_PEOPLE  = re.compile(r"^/(in|pub)/[^/]+/?", re.I)
    _RX_COMPANY = re.compile(r"^/company/[^/]+/?",  re.I)
    _RX_JOB     = re.compile(r"^/jobs/view/",       re.I)

    def _classify(self, url: str) -> str | None:
        """Return ``'people' | 'company' | 'job'`` or ``None``."""
        path = urlparse(url).path
        if self._RX_PEOPLE.match(path):
            return "people"
        if self._RX_COMPANY.match(path):
            return "company"
        if self._RX_JOB.match(path):
            return "job"
        return None

    # ────────────────────────────────────────────────────────────────
    # 0 ▸ Smart router
    # ────────────────────────────────────────────────────────────────
    def collect_by_url(self, urls: Sequence[str]) -> Dict[str, str]:
        """
        Auto-detect the LinkedIn entity type for each URL and forward the
        sub-lists to the correct *collect* method.

        Parameters
        ----------
        urls : sequence of str
            People / company / job URLs (mixed is fine).

        Returns
        -------
        dict[str, str]
            Keys are ``'people' | 'company' | 'job'``; values are
            **snapshot-id** strings for each sub-job.

        Notes
        -----
        *The mapping of original URLs → bucket type* is stored on the
        instance as ``self._url_buckets`` for the benefit of
        ``brightdata.auto.scrape_url``.
        """
        buckets: DefaultDict[str, List[str]] = defaultdict(list)
        for u in urls:
            kind = self._classify(u)
            if not kind:
                raise ValueError(f"Unrecognised LinkedIn URL: {u}")
            buckets[kind].append(u)

        # expose for external helpers (auto.scrape_url uses this)
        self._url_buckets: Dict[str, List[str]] = dict(buckets)

        results: Dict[str, str] = {}
        if buckets.get("people"):
            results["people"] = self.collect_people_by_url(buckets["people"])
        if buckets.get("company"):
            results["company"] = self.collect_company_by_url(buckets["company"])
        if buckets.get("job"):
            results["job"] = self.collect_jobs_by_url(buckets["job"])
        return results

    # ────────────────────────────────────────────────────────────────
    # 1 ▸ People
    # ────────────────────────────────────────────────────────────────
    def collect_people_by_url(self, urls: Sequence[str]) -> str:
        """
        Scrape **individual profile pages**.

        Returns
        -------
        snapshot_id : str
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET_PEOPLE,
            extra_params={"sync_mode": "async"},
        )

    def discover_people_by_name(self, names: Sequence[str]) -> str:
        """
        Discover profiles by full-name search.

        Returns
        -------
        snapshot_id : str
        """
        payload = [{"name": n} for n in names]
        return self._trigger(
            payload,
            dataset_id=_DATASET_PEOPLE,
            extra_params={
                "type": "discover_new",
                "discover_by": "name",
                "sync_mode": "async",
            },
        )

    # ────────────────────────────────────────────────────────────────
    # 2 ▸ Company
    # ────────────────────────────────────────────────────────────────
    def collect_company_by_url(self, urls: Sequence[str]) -> str:
        """
        Scrape **LinkedIn company pages**.

        Returns
        -------
        snapshot_id : str
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET_COMPANY,
            extra_params={"sync_mode": "async"},
        )

    # ────────────────────────────────────────────────────────────────
    # 3 ▸ Jobs
    # ────────────────────────────────────────────────────────────────
    def collect_jobs_by_url(self, urls: Sequence[str]) -> str:
        """
        Scrape **individual job-posting URLs**.

        Returns
        -------
        snapshot_id : str
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET_JOBS,
            extra_params={"sync_mode": "async"},
        )

    def discover_jobs_by_keyword(self, queries: Sequence[Dict[str, Any]]) -> str:
        """
        Discover job listings via keyword / location search.

        Parameters
        ----------
        queries : sequence of dict
            Exactly the structure Bright Data expects, e.g. ::

                {"location":"Paris",
                 "keyword":"product manager",
                 "country":"FR", ...}

        Returns
        -------
        snapshot_id : str
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET_JOBS,
            extra_params={
                "type": "discover_new",
                "discover_by": "keyword",
                "sync_mode": "async",
            },
        )

    # ------------------------------------------------------------------
    # No _trigger override needed – we rely on the base implementation.
    # ------------------------------------------------------------------



