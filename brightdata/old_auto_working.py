# brightdata/auto.py


# to run smoketest  python -m brightdata.auto
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
from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
from brightdata.browser_api import BrowserAPI

import asyncio
from brightdata.utils.async_poll import fetch_snapshot_async, fetch_snapshots_async

from brightdata.models import ScrapeResult
import tldextract


import warnings

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="selenium.webdriver.remote.remote_connection"
)


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
    fallback_to_browser_api: bool = False
) -> ScrapeResult:
    """
    Triggers a scrape and waits for it to finish, returning a
    ScrapeResponse with data, cost, and fallback info.
    """
    ScraperCls = get_scraper_for(url)
    if ScraperCls is None:
        if fallback_to_browser_api:
            scrape_result = BrowserAPI().get_page_source_with_a_delay(url)
            if isinstance(scrape_result, ScrapeResult):
                return scrape_result

        return None
          

        # return ScrapeResult(
        #     url=url,
        #     status="error",
        #     data=None,
        #     error="no_scraper",
        #     snapshot_id=None,
        #     cost=None,
        #     fallback_used=False,
        # )

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
            scrape_result = await loop.run_in_executor(
                None,
                lambda: BrowserAPI().get_page_source_with_a_delay(url)
            )

            if isinstance(scrape_result, ScrapeResult):
                return scrape_result

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
    fallback_to_browser_api: bool = False,
) -> Dict[str, Union[ScrapeResult, Dict[str, ScrapeResult]]]:
    """
    Trigger & poll many URLs concurrently.

    Returns
    -------
    dict[str, ScrapeResult | dict[str, ScrapeResult]]
        url → ScrapeResult  (single bucket)
        url → {bucket: ScrapeResult, …}  (multi-bucket scrapers)
    """
    loop = asyncio.get_running_loop()

    # -------------------------------------------------------------- #
    # 1) Trigger Bright-Data jobs in parallel (thread-pool is fine)
    # -------------------------------------------------------------- #
    trigger_futures = {
        url: loop.run_in_executor(
            None, lambda u=url: trigger_scrape_url(u, bearer_token=bearer_token)
        )
        for url in urls
    }
    snaps = await asyncio.gather(*trigger_futures.values())
    url_to_snap: Dict[str, Snapshot] = dict(zip(trigger_futures.keys(), snaps))

    # -------------------------------------------------------------- #
    # 2) Prepare BrowserAPI fallback (one shared instance)
    # -------------------------------------------------------------- #
    browser: BrowserAPI | None = None
    if fallback_to_browser_api and any(
        get_scraper_for(u) is None for u in urls
    ):
        browser = BrowserAPI()                                # Playwright version

    # -------------------------------------------------------------- #
    # 3) Schedule all polling / fallback tasks
    # -------------------------------------------------------------- #
    async def _poll_multi(scraper, bucket_map):
        tasks = [
            fetch_snapshot_async(scraper, sid,
                                 poll=poll_interval, timeout=poll_timeout)
            for sid in bucket_map.values()
        ]
        done = await asyncio.gather(*tasks)
        return dict(zip(bucket_map.keys(), done))

    tasks: Dict[str, asyncio.Task] = {}

    for url, snap in url_to_snap.items():
        ScraperCls = get_scraper_for(url)

        # ── Fallback branch ────────────────────────────────────────
        if ScraperCls is None:
            if browser is not None:
                # schedule Playwright coroutine directly
                tasks[url] = asyncio.create_task(
                    browser.get_page_source_with_a_delay_async(url)
                )
            else:
                # No scraper, no fallback
                tasks[url] = asyncio.create_task(asyncio.sleep(0, result=None))
            continue

        # ── Bright-Data branch ─────────────────────────────────────
        token = bearer_token or os.getenv("BRIGHTDATA_TOKEN")
        scraper = ScraperCls(bearer_token=token)

        if isinstance(snap, dict):
            tasks[url] = asyncio.create_task(_poll_multi(scraper, snap))
        else:
            tasks[url] = asyncio.create_task(
                fetch_snapshot_async(
                    scraper, snap,
                    poll=poll_interval, timeout=poll_timeout
                )
            )

    # -------------------------------------------------------------- #
    # 4) Collect results
    # -------------------------------------------------------------- #
    gathered = await asyncio.gather(*tasks.values())
    results = dict(zip(tasks.keys(), gathered))

    # -------------------------------------------------------------- #
    # 5) Clean-up Playwright browser (if we opened one)
    # -------------------------------------------------------------- #
    if browser is not None:
        await browser.close()

    return results




def scrape_urls(
    urls, bearer_token=None, poll_interval=8, poll_timeout=180, fallback_to_browser_api=False
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
            fallback_to_browser_api=fallback_to_browser_api,
        )
    )





def print_scrape_summary(
    results: Dict[str, Union[ScrapeResult, Dict[str, ScrapeResult]]]
) -> None:
    """
    Pretty console output for the dict returned by `scrape_urls(_async)`.

    • Handles single-bucket ScrapeResult objects
    • Handles multi-bucket dicts {bucket: ScrapeResult}
    • Prints timing fields when present
    """
    for url, result in results.items():
        print(f"\nURL: {url}")

        # ────────────────────────────────────────────────
        # 1. Single-bucket
        # ────────────────────────────────────────────────
        if isinstance(result, ScrapeResult):
            print(f"  success:       {result.success}")
            print(f"  status:        {result.status}")
            print(f"  root_domain:   {result.root_domain!r}")

            # optional timestamps
            if result.request_sent_at:
                print(f"  sent at:       {result.request_sent_at.isoformat()}Z")
            if result.snapshot_id_received_at:
                print(f"  sid recv at:   {result.snapshot_id_received_at.isoformat()}Z")
            if result.snapshot_polled_at:
                print(f"  last polled:   {result.snapshot_polled_at[-1].isoformat()}Z")
            if result.data_received_at:
                print(f"  data recv at:  {result.data_received_at.isoformat()}Z")
            if result.event_loop_id is not None:
                print(f"  loop id:       {result.event_loop_id}")

            # error (if any)
            if result.error:
                print(f"  error:         {result.error}")

            # data size / type
            if result.data is not None:
                if isinstance(result.data, list):
                    print(f"  rows:          {len(result.data)}")
                else:
                    print(f"  data type:     {type(result.data).__name__}")

        # ────────────────────────────────────────────────
        # 2. Multi-bucket
        # ────────────────────────────────────────────────
        elif isinstance(result, dict):
            print("  multi-bucket:")
            for bucket, sub in result.items():
                line = f"    [{bucket}] success={sub.success} status={sub.status}"
                if sub.error:
                    line += f" error={sub.error}"
                print(line)
                if sub.snapshot_polled_at:
                    print(f"       last poll: {sub.snapshot_polled_at[-1].isoformat()}Z")
                if isinstance(sub.data, list):
                    print(f"       rows:      {len(sub.data)}")

        # ────────────────────────────────────────────────
        # 3. No result
        # ────────────────────────────────────────────────
        else:
            print("  <no result>")


if __name__ == "__main__":
    # import pprint


 
    # 1) smoke-test scrape_url
    # print("== Smoke-test: scrape_url ==")
    # single = "https://budgety.ai"
    # # fallback_to_browser_api=True so that even un-scrapable URLs return HTML
    # res1 = scrape_url(single, fallback_to_browser_api=True)
    # # pprint.pprint(res1)
    # print(res1)


    
    # 2) smoke-test scrape_urls
    print("\n== Smoke-test: scrape_urls ==")
    many = ["https://budgety.ai", "https://openai.com"]
    # again fallback=True so that non-registered scrapers will return HTML
    results = scrape_urls(many, fallback_to_browser_api=True)
     
    print_scrape_summary(results)

   