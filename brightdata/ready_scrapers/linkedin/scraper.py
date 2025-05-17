"""
brightdata.ready_scrapers.linkedin.scraper
==========================================

One thin wrapper around the **three** Bright-Data LinkedIn datasets that are
publicly documented as of 2025-05-17.

Dataset IDs (static – taken from the examples you supplied)
-----------------------------------------------------------
* gd_l1viktl72bvl7bjuj0 ― *linkedin_people_profile*
* gd_l1vikfnt1wgvvqz95w ― *linkedin_company_information*
* gd_lpfll7v5hcqtkxl6l ― *linkedin_job_listing_information*

All requests are forced into `sync_mode=async` by the shared base-class, so
every method returns **`snapshot_id` (str)**.  Call
`BrightdataBaseSpecializedScraper.get_data()` (blocking) or the async helper
in `brightdata.utils.async_poll` to obtain the final rows.

Example
-------
>>> from brightdata.ready_scrapers.linkedin import LinkedInScraper
>>> s = LinkedInScraper(bearer_token=TOKEN)
>>> snap = s.discover_jobs_by_keyword([{"keyword": "python developer"}])
>>> rows = poll_until_ready(s, snap).data
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper

# ──────────────────────────────────────────────────────────────
# hard-coded dataset IDs
# ──────────────────────────────────────────────────────────────
_DATASET_PEOPLE   = "gd_l1viktl72bvl7bjuj0"
_DATASET_COMPANY  = "gd_l1vikfnt1wgvvqz95w"
_DATASET_JOBS     = "gd_lpfll7v5hcqtkxl6l"


class LinkedInScraper(BrightdataBaseSpecializedScraper):
    """
    **ready_scrapers.linkedin.LinkedInScraper**

    Endpoints
    ---------
    • collect_people_by_url(urls)  
    • discover_people_by_name(names)

    • collect_company_by_url(urls)

    • collect_jobs_by_url(urls)  
    • discover_jobs_by_keyword(job_queries)

    All methods return a **snapshot-id string** that must be polled.
    """

    # we give *any* dataset_id to the base-class; individual methods will pass
    # their own dataset_id to _trigger().
    def __init__(self, bearer_token: str):
        super().__init__(dataset_id=_DATASET_PEOPLE, bearer_token=bearer_token)

    # ─────────────────────────────────────────────────────────────
    # 1.  People profile
    # ─────────────────────────────────────────────────────────────
    def collect_people_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]
        return self._trigger(payload, dataset_id=_DATASET_PEOPLE)

    def discover_people_by_name(self, names: Sequence[str]) -> str:
        """
        Bright Data → ‘discover by name’

        Parameters
        ----------
        names : list[str] – “First Last”
        """
        payload = [{"name": n} for n in names]
        return self._trigger(
            payload,
            dataset_id=_DATASET_PEOPLE,
            extra_params={"type": "discover_new", "discover_by": "name"},
        )

    # ─────────────────────────────────────────────────────────────
    # 2.  Company pages
    # ─────────────────────────────────────────────────────────────
    def collect_company_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]
        return self._trigger(payload, dataset_id=_DATASET_COMPANY)

    # ─────────────────────────────────────────────────────────────
    # 3.  Job listings
    # ─────────────────────────────────────────────────────────────
    def collect_jobs_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]
        return self._trigger(payload, dataset_id=_DATASET_JOBS)

    def discover_jobs_by_keyword(
        self,
        queries: Sequence[Dict[str, Any]],
    ) -> str:
        """
        Each item in *queries* must carry the keys Bright-Data expects, e.g.:

        {
            "location": "paris",
            "keyword":  "product manager",
            "country":  "FR",
            "time_range": "Past month",
            "job_type":  "Full-time",
            "experience_level": "Internship",
            "remote": "On-site",
            "company": ""
        }
        """
        return self._trigger(
            list(queries),
            dataset_id=_DATASET_JOBS,
            extra_params={"type": "discover_new", "discover_by": "keyword"},
        )


# # so that `from brightdata.ready_scrapers.linkedin import LinkedInScraper`
# # just works:
# __all__: list[str] = ["LinkedInScraper"]
