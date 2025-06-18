# brightdata/base_specialized_scraper.py  – patched

from __future__ import annotations
import asyncio, logging, requests
from typing import Any, Dict, List, Optional, Union
from typing import Dict, List, Any, Optional, Tuple, Pattern
from collections import defaultdict
from brightdata.engine import get_engine
from brightdata.models import ScrapeResult

log = logging.getLogger(__name__)




class BrightdataBaseSpecializedScraper:
    # legacy constants (for poll helpers)
    COST_PER_RECORD = 0.001 

    trigger_url      = "https://api.brightdata.com/datasets/v3/trigger"
    status_base_url  = "https://api.brightdata.com/datasets/v3/progress"
    result_base_url  = "https://api.brightdata.com/datasets/v3/snapshot"

    def __init__(self, dataset_id: str, bearer_token: Optional[str] = None):
        self.dataset_id = dataset_id
        self._engine    = get_engine(bearer_token)

    # ─────────────────────────── trigger (sync) ────────────────────────────
    def trigger(
        self,
        payload: List[Dict[str, Any]],
        *,
        dataset_id: Optional[str] = None,         # ← NEW (override)
        include_errors: bool = True,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        ds = dataset_id or self.dataset_id
        return _run_blocking(
            self._engine.trigger(
                payload,
                dataset_id=ds,
                include_errors=include_errors,
                extra_params=extra_params,
            )
        )

    # ───────────────────────── trigger (async) ────────────────────────────
    async def _trigger_async(
        self,
        payload: List[Dict[str, Any]],
        *,
        dataset_id: Optional[str] = None,         # ← NEW
        include_errors: bool = True,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        ds = dataset_id or self.dataset_id
        return await self._engine.trigger(
            payload,
            dataset_id=ds,
            include_errors=include_errors,
            extra_params=extra_params,
        )

    # ─────────────────────────── get_data (sync) ───────────────────────────
    def get_data(self, snapshot_id: str) -> ScrapeResult:
        status = _run_blocking(self._engine.get_status(snapshot_id))
        if status == "ready":

            # return _run_blocking(self._engine.fetch_result(snapshot_id))
            res = _run_blocking(self._engine.fetch_result(snapshot_id))
            # if isinstance(res.data, list):
            #     res.cost = len(res.data) * self.COST_PER_RECORD
            return res

        


        if status in {"error", "failed"}:



            return ScrapeResult(False, f"{self.status_base_url}/{snapshot_id}",
                                status="error", error="job_failed",
                                snapshot_id=snapshot_id)
        return ScrapeResult(True, f"{self.status_base_url}/{snapshot_id}",
                            status="not_ready", snapshot_id=snapshot_id)

    # ───────────────────────── get_data (async) ────────────────────────────
    async def get_data_async(self, snapshot_id: str) -> ScrapeResult:
        status = await self._engine.get_status(snapshot_id)
        if status == "ready":

            res = await self._engine.fetch_result(snapshot_id)
            # if isinstance(res.data, list):
            #     res.cost = len(res.data) * self.COST_PER_RECORD
            return res
        

        if status in {"error", "failed"}:


            return ScrapeResult(False, f"{self.status_base_url}/{snapshot_id}",
                                status="error", error="job_failed",
                                snapshot_id=snapshot_id)
        return ScrapeResult(True, f"{self.status_base_url}/{snapshot_id}",
                            status="not_ready", snapshot_id=snapshot_id)

    # convenience wrappers unchanged …
    def trigger_multiple(self, urls: List[str]) -> Optional[str]:
        return self.trigger([{"url": u} for u in urls])

    async def trigger_multiple_async(self, urls: List[str]) -> Optional[str]:
        return await self._trigger_async([{"url": u} for u in urls])

    def test_connection(self) -> tuple[bool, Optional[str]]:
        try:
            r = requests.head(self.trigger_url,
                              params={"dataset_id": self.dataset_id},
                              timeout=4)
            r.raise_for_status()
            return True, None
        except requests.RequestException as e:
            return False, str(e)
        
 
    def dispatch_by_regex(
        self,
        urls: List[str],
        pattern_map: Dict[str, Pattern],
        *,
        allow_multiple: bool = False,
        unknown_bucket: str | None = None
    ) -> Dict[str, List[str]]:
        """
        Bucket a list of URLs by regex patterns.

        Parameters
        ----------
        urls         : List of raw URLs to classify
        pattern_map  : Mapping { bucket_name: compiled_regex }
        allow_multiple : if False (default), stops at first match; 
                         if True, a URL can live in many buckets
        unknown_bucket: if set, any URL that matches no pattern
                        goes into this bucket; else they’re ignored

        Side-effect
        ----------
        Sets self._url_buckets to the same returned dict.

        Returns
        -------
        A dict { bucket_name: [urls…], … }
        """
       
        buckets = defaultdict(list)
        for url in urls:
            matched = False
            for name, rx in pattern_map.items():
                if rx.search(url):
                    buckets[name].append(url)
                    matched = True
                    if not allow_multiple:
                        break
            if not matched and unknown_bucket:
                buckets[unknown_bucket].append(url)

        self._url_buckets = dict(buckets)
        return self._url_buckets
        
    

    def poll_until_ready(
            self,
            snapshot_id: str,
            *,
            poll_interval: int = 10,
            timeout: int = 600,
        ) -> ScrapeResult:
        """Blocking helper that delegates entirely to engine.poll_until_ready."""
        return _run_blocking(
            self._engine.poll_until_ready(
                snapshot_id,
                poll_interval=poll_interval,
                timeout=timeout,
            )
        )
    
    async def poll_until_ready_async(
        self,
        snapshot_id: str,
        *,
        poll_interval: int = 10,
        timeout: int = 600,
    ) -> ScrapeResult:
        
        return await self._engine.poll_until_ready(snapshot_id,  poll_interval=poll_interval, timeout=timeout, )


# helper – run one coroutine from sync context
def _run_blocking(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():              # inside existing loop
        import concurrent.futures as cf
        with cf.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()
    return asyncio.run(coro)

