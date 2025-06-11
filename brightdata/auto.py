# brightdata/auto.py
"""
High‐level helpers: detect the right scraper for a URL, trigger a crawl,
and (optionally) wait for results.

Functions
---------
scrape_trigger_url(url, bearer_token=None)
    → trigger a Bright Data job for the given URL, returning the raw
      snapshot‐id (str) or a dict of snapshot‐ids for multi‐bucket scrapers.

scrape_url(url, bearer_token=None, poll=True, poll_interval=8, poll_timeout=180)
    → same as scrape_trigger_url but, if poll=True, blocks until the job(s)
      are ready and returns the scraped rows.
"""

from __future__ import annotations
import os
from dotenv import load_dotenv
from typing import Any, Dict, List, Union

from brightdata.registry import get_scraper_for
from brightdata.utils.poll import poll_until_ready
from brightdata.base_specialized_scraper import ScrapeResult
from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
from brightdata.browser_api import BrowserAPI

import asyncio
from brightdata.utils.async_poll import fetch_snapshot_async, fetch_snapshots_async

from brightdata.models import ScrapeResult
import tldextract



load_dotenv()

Rows = List[Dict[str, Any]]
Snapshot = Union[str, Dict[str, str]]
ResultData = Union[Rows, Dict[str, Rows], ScrapeResult]



def trigger_scrape_url_with_fallback(
    url: str,
    bearer_token: str | None = None,
    throw_a_value_error_if_not_a_known_scraper=False, 
) -> Snapshot:
    """
    Detect and instantiate the right scraper for `url`, call its
    collect_by_url([...]) method, and return the raw snapshot‐id
    (or dict of snapshot‐ids).
    """
    token = bearer_token or os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        raise RuntimeError("Provide bearer_token or set BRIGHTDATA_TOKEN env var")

    ScraperCls = get_scraper_for(url)

    if ScraperCls is None:
        if  throw_a_value_error_if_not_a_known_scraper:
                 raise ValueError(f"No scraper registered for {url}")
        else: 
            # if fallback_to_web_unlocker:
            unlocker = BrightdataWebUnlocker()
            source = unlocker.get_source(url)
            return None, source
            
            # else:
            #     return None ,None
   
    scraper = ScraperCls(bearer_token=token)
    if not hasattr(scraper, "collect_by_url"):
        raise ValueError(f"{ScraperCls.__name__} does not implement collect_by_url()")
    
    # Returns either a str snapshot_id or a dict of them
    return scraper.collect_by_url([url]), None

def trigger_scrape_url(
    url: str,
    bearer_token: str | None = None,
    throw_a_value_error_if_not_a_known_scraper=False, 
    # fallback_to_web_unlocker=False
) -> Snapshot:
    """
    Detect and instantiate the right scraper for `url`, call its
    collect_by_url([...]) method, and return the raw snapshot‐id
    (or dict of snapshot‐ids).
    """
    token = bearer_token or os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        raise RuntimeError("Provide bearer_token or set BRIGHTDATA_TOKEN env var")

    ScraperCls = get_scraper_for(url)

    
    if ScraperCls is None:
        if  throw_a_value_error_if_not_a_known_scraper:
                 raise ValueError(f"No scraper registered for {url}")
        else: 
  
                return None 
    
    scraper = ScraperCls(bearer_token=token)
    if not hasattr(scraper, "collect_by_url"):
        raise ValueError(f"{ScraperCls.__name__} does not implement collect_by_url()")

    # Returns either a str snapshot_id or a dict of them
    return scraper.collect_by_url([url])



def scrape_url(
    url: str,
    bearer_token: str | None = None,
    poll_interval: int = 8,
    poll_timeout: int = 180,
) -> ScrapeResult:
    """
    Triggers a scrape and waits for it to finish, returning a
    ScrapeResponse with data, cost, and fallback info.
    """
    ScraperCls = get_scraper_for(url)
    if ScraperCls is None:
        return ScrapeResult(
            url=url,
            status="error",
            data=None,
            error="no_scraper",
            snapshot_id=None,
            cost=None,
            fallback_used=False,
        )

    # 1) Trigger
    snap = trigger_scrape_url(url, bearer_token=bearer_token)
    snapshot_id = snap if isinstance(snap, str) else None

    # 2) Poll
    scraper = ScraperCls(bearer_token=bearer_token)
    res = poll_until_ready(scraper, snapshot_id, poll=poll_interval, timeout=poll_timeout)

    # 3) Extract cost if available (assuming Bright Data returns it in res.data metadata)
    cost = None
    if isinstance(res.data, dict) and "cost" in res.data:
        cost = float(res.data.pop("cost"))

    # 4) Determine if we fell back (example: if status != "ready" and we choose a BrowserAPI fallback)
    fallback_used = False
    if res.status != "ready":
        # fallback logic could live here...
        # e.g., call BrowserAPI or a secondary scraper
        fallback_used = True
        # new_data = BrowserAPI(...).get_page_source_and_wait(url)
        # return early or merge new_data into data

    return ScrapeResult(
        url=url,
        status=res.status,
        data=res.data if res.status == "ready" else None,
        error=res.error,
        snapshot_id=snapshot_id,
        cost=cost,
        fallback_used=fallback_used,
    )

# this is in auto.py
def scrape_url(
    url: str,
    bearer_token: str | None = None,
    # poll: bool = True,
    poll_interval: int = 8,
    poll_timeout: int = 180,
    fallback_to_browser_api= False
) -> ResultData:
    """
    High-level scrape: trigger + (optionally) wait for data.

    Parameters
    ----------
    url           – a single URL to scrape
    bearer_token  – your Bright Data token (or set BRIGHTDATA_TOKEN)
    poll_interval – seconds between status checks
    poll_timeout  – maximum seconds to wait per snapshot
    
    Returns
    -------
    • If poll=False:
        Snapshot           (str) or dict[str, str]
    • If poll=True and single‐snapshot:
        List[dict]         (the rows)
      or ScrapeResult      (if the job errored or timed out)
    • If poll=True and multi‐snapshot (e.g. LinkedIn):
        Dict[str, List[dict]]  mapping bucket → rows
      or Dict[str, ScrapeResult]
    """
    snap = trigger_scrape_url(url, bearer_token=bearer_token)
    token = bearer_token or os.getenv("BRIGHTDATA_TOKEN")
    ScraperCls = get_scraper_for(url)
     
    if ScraperCls is None:
        
        if fallback_to_browser_api:
            api = BrowserAPI()
            html_hydrated = api.get_page_source_with_a_delay(url)
            if html_hydrated:
                sr= ScrapeResult(
                    success=True, 
                    status="ready", 
                    data=html_hydrated
                )
            else:
                sr= ScrapeResult(
                    success=False, 
                    status="error", 
                    data=html_hydrated, 
                    error="unknown_browser_api_error"
                )
            return sr
        else:

               return None
    
    
    
    # Multi‐bucket case (e.g. LinkedIn returns {"people": id1, ...})
    if isinstance(snap, dict):
        results: Dict[str, Any] = {}
        for key, sid in snap.items():
            scraper = ScraperCls(bearer_token=token)
            res = poll_until_ready(
                scraper,
                sid,
                poll=poll_interval,
                timeout=poll_timeout,
            )
            if res.status == "ready":
                results[key] = res.data
            else:
                results[key] = res
        return results

    # Single‐snapshot case
    scraper = ScraperCls(bearer_token=token)
    res = poll_until_ready(
        scraper,
        snap,
        poll=poll_interval,
        timeout=poll_timeout,
    )
    if res.status == "ready":
        return res.data
    return res



async def scrape_url_async(
    url: str,
    bearer_token: str | None = None,
    poll_interval: int = 8,
    poll_timeout: int = 180,
    fallback_to_browser_api: bool = False
) -> ScrapeResult | dict[str, ScrapeResult]:
    # 1) Trigger via executor so we don't block the event loop
    loop = asyncio.get_running_loop()
    snap = await loop.run_in_executor(
        None,
        lambda: trigger_scrape_url(url, bearer_token=bearer_token)
    )

    ScraperCls = get_scraper_for(url)
    if ScraperCls is None:
        if fallback_to_browser_api:
            # offload blocking browser call to executor
            html = await loop.run_in_executor(
                None,
                lambda: BrowserAPI().get_page_source_with_a_delay(url)
            )
            return ScrapeResult(
                success=bool(html),
                url=url,
                status="ready" if html else "error",
                data=html if html else None,
                error=None if html else "browser_api_failed",
                snapshot_id=None,
                cost=None,
                fallback_used=True,
                root_domain=None
            )
        return None

    # 2) Poll asynchronously
    scraper = ScraperCls(bearer_token or os.getenv("BRIGHTDATA_TOKEN"))
    if isinstance(snap, dict):
        # multi-bucket
        tasks = {
            key: fetch_snapshot_async(scraper, sid, poll=poll_interval, timeout=poll_timeout)
            for key, sid in snap.items()
        }
        results = await asyncio.gather(*tasks.values())
        return {k: r for k, r in zip(tasks.keys(), results)}

    # single snapshot
    res = await fetch_snapshot_async(scraper, snap, poll=poll_interval, timeout=poll_timeout)
    return res




async def scrape_urls_async(
    urls: List[str],
    bearer_token: str | None = None,
    poll_interval: int = 8,
    poll_timeout: int = 180,
    fallback_to_browser_api: bool = False
) -> Dict[str, Union[ScrapeResult, Dict[str, ScrapeResult]]]:
    """
    Trigger and poll multiple URLs concurrently, returning a mapping:
      url -> ScrapeResult  (single-bucket)
      url -> {bucket: ScrapeResult, ...}  (multi-bucket)
    Fallback to BrowserAPI if no scraper is registered and fallback_to_browser_api=True.
    """
    loop = asyncio.get_running_loop()
     
    # 1) Trigger all jobs in parallel (off the event loop)
    trigger_tasks = {
        url: loop.run_in_executor(
            None,
            lambda url=url: trigger_scrape_url(url, bearer_token=bearer_token)
        )
        for url in urls
    }
    snaps = await asyncio.gather(*trigger_tasks.values())
    url_to_snap = dict(zip(trigger_tasks.keys(), snaps))

    # Helper to gather multi-bucket polling
    async def _gather_buckets(scraper, bucket_map):
        tasks = {
            bucket: asyncio.create_task(
                fetch_snapshot_async(scraper, sid, poll=poll_interval, timeout=poll_timeout)
            )
            for bucket, sid in bucket_map.items()
        }
        results = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), results))

    results: Dict[str, Union[ScrapeResult, Dict[str, ScrapeResult]]] = {}

    # 2) Poll all jobs asynchronously
    for url, snap in url_to_snap.items():
        ScraperCls = get_scraper_for(url)
        if ScraperCls is None:
            if fallback_to_browser_api:
                # Fallback via BrowserAPI off the event loop
                html = await loop.run_in_executor(
                    None,
                    lambda: BrowserAPI().get_page_source(url)
                )
                # Build a minimal ScrapeResult
                ext = tldextract.extract(url)
                root = ext.domain or None
                results[url] = ScrapeResult(
                    success=bool(html),
                    url=url,
                    status="ready" if html else "error",
                    data=html if html else None,
                    error=None if html else "browser_api_failed",
                    snapshot_id=None,
                    cost=None,
                    fallback_used=True,
                    root_domain=root
                )
            else:
                results[url] = None
            continue

        # Registered scraper: poll results
        token = bearer_token or os.getenv("BRIGHTDATA_TOKEN")
        scraper = ScraperCls(bearer_token=token)

        if isinstance(snap, dict):
            # Multi-bucket
            results[url] = await _gather_buckets(scraper, snap)
        else:
            # Single snapshot
            results[url] = await fetch_snapshot_async(
                scraper, snap, poll=poll_interval, timeout=poll_timeout
            )

    return results



def scrape_urls(
    urls, bearer_token=None, poll_interval=8, poll_timeout=180, fallback=False
):
    """
    Synchronous wrapper around scrape_urls_async.
    """
    return asyncio.run(
        scrape_urls_async(
            urls,
            bearer_token=bearer_token,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
            fallback_to_browser_api=fallback,
        )
    )