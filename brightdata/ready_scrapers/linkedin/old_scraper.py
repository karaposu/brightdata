from __future__ import annotations
import re
from typing import Any, Dict, List, Sequence, Tuple, DefaultDict, Iterable
from collections import defaultdict
from urllib.parse import urlparse

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

_DATASET_PEOPLE   = "gd_l1viktl72bvl7bjuj0"
_DATASET_COMPANY  = "gd_l1vikfnt1wgvvqz95w"
_DATASET_JOBS     = "gd_lpfll7v5hcqtkxl6l"

_DEFAULT_DATASET = _DATASET_PEOPLE   

@register("linkedin")
class LinkedInScraper(BrightdataBaseSpecializedScraper):
    """
    Wrapper for *linkedin_people_profile*, *linkedin_company_information* and
    *linkedin_job_listing_information* datasets.

    New helper
    ----------
    collect_by_url(urls)   → {"people": snapshot_id, …}
    """

    def __init__(self, *, bearer_token: str):
        super().__init__(dataset_id=_DEFAULT_DATASET,
                         bearer_token=bearer_token)

    # --------------------------------------------------------------------- #
    # ▶▶  0.  ROUTER  ◀◀
    # --------------------------------------------------------------------- #
    _RX_PEOPLE  = re.compile(r"^/(in|pub)/[^/]+/?", re.I)
    _RX_COMPANY = re.compile(r"^/company/[^/]+/?",  re.I)
    _RX_JOB     = re.compile(r"^/jobs/view/",       re.I)
    
    def _classify(self, url: str) -> str | None:
        """Return 'people' | 'company' | 'job' or None."""
        path = urlparse(url).path
        if self._RX_PEOPLE.match(path):
            return "people"
        if self._RX_COMPANY.match(path):
            return "company"
        if self._RX_JOB.match(path):
            return "job"
        return None

    def collect_by_url(self, urls: Sequence[str]) -> Dict[str, str]:
        """
        Smart façade – detects entity type from the path and forwards the
        sub-list to the proper method.  Always returns **snapshot-ids** in a
        dict keyed by entity type.

        >>> snaps = scraper.collect_by_url(mixed_urls)
        >>> poll_until_ready(scraper, snaps["people"])
        """
        buckets: DefaultDict[str, List[str]] = defaultdict(list)
        for u in urls:
            kind = self._classify(u)
            if not kind:
                raise ValueError(f"Unrecognised LinkedIn URL: {u}")
            buckets[kind].append(u)

        results: Dict[str, str] = {}
        if buckets.get("people"):
            results["people"] = self.collect_people_by_url(buckets["people"])
        if buckets.get("company"):
            results["company"] = self.collect_company_by_url(buckets["company"])
        if buckets.get("job"):
            results["job"] = self.collect_jobs_by_url(buckets["job"])
        return results
    
    # ------------------------------------------------------------------ #
    # 1.  PEOPLE
    # ------------------------------------------------------------------ #
    def collect_people_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]

        return self._trigger(
                            payload,
                            dataset_id=_DATASET_PEOPLE,
                            extra_params={"sync_mode": "async"}   # 👈 add this line
                            )
       

    def discover_people_by_name(self, names: Sequence[str]) -> str:
        payload = [{"name": n} for n in names]
        return self._trigger(
            payload, dataset_id=_DATASET_PEOPLE,
            extra_params={"type": "discover_new", "discover_by": "name"},
        )

    # ------------------------------------------------------------------ #
    # 2.  COMPANY
    # ------------------------------------------------------------------ #
    def collect_company_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]
        # return self._trigger(payload, dataset_id=_DATASET_COMPANY)
        
        return self._trigger(
                            payload,
                            dataset_id=_DATASET_COMPANY,
                            extra_params={"sync_mode": "async"}   # 👈 add this line
                            )
    
    

    # ------------------------------------------------------------------ #
    # 3.  JOBS
    # ------------------------------------------------------------------ #
    def collect_jobs_by_url(self, urls: Sequence[str]) -> str:
        payload = [{"url": u} for u in urls]
        # return self._trigger(payload, dataset_id=_DATASET_JOBS)
    
        return self._trigger(
                            payload,
                            dataset_id=_DATASET_JOBS,
                            extra_params={"sync_mode": "async"}   # 👈 add this line
                            )

    def discover_jobs_by_keyword(self,
                                 queries: Sequence[Dict[str, Any]]) -> str:
        return self._trigger(
            list(queries), dataset_id=_DATASET_JOBS,
            extra_params={"type": "discover_new", "discover_by": "keyword"},
        )


# __all__: list[str] = ["LinkedInScraper"]
