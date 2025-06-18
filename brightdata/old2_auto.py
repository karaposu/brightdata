# here is brightdata/auto.py

#!/usr/bin/env python3
"""
brightdata.auto
===============

“One-liner” helpers that

1. detect which ready-scraper can handle a URL,
2. trigger the Bright-Data job, and
3. (optionally) wait until the snapshot is ready.

If no specialised scraper exists you *can* fall back to Browser-API.
"""

# # to run smoketest  python -m brightdata.auto

from __future__ import annotations
import asyncio
import logging
import os
from typing import Any, Dict, List, Union

from dotenv import load_dotenv

from brightdata.browser_api import BrowserAPI
from brightdata.browser_pool import BrowserPool
from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
from brightdata.models import ScrapeResult
from brightdata.registry import get_scraper_for
from brightdata.utils import show_scrape_results

load_dotenv()
logger = logging.getLogger(__name__)

Rows       = List[Dict[str, Any]]
Snapshot   = Union[str, Dict[str, str]]      # single- or multi-bucket
ResultData = Union[Rows, Dict[str, Rows], ScrapeResult]


# ─────────────────────────────────────────────────────────────── trigger helpers
def trigger_scrape_url(
    url: str,
    bearer_token: str | None = None,
    *,
    raise_if_unknown: bool = False,
) -> Snapshot | None:
    """
    Detect a ready-scraper for *url* and call its ``collect_by_url`` method.
    Returns the snapshot-id (or dict of ids).  If no scraper is found:

    * raise ``ValueError`` when *raise_if_unknown=True*
    * return **None** otherwise
    """
    token = bearer_token or os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        raise RuntimeError("Provide bearer_token or set BRIGHTDATA_TOKEN")

    ScraperCls = get_scraper_for(url)
    if ScraperCls is None:
        if raise_if_unknown:
            raise ValueError(f"No scraper registered for {url}")
        return None
    
    scraper = ScraperCls(bearer_token=token)
    if not hasattr(scraper, "collect_by_url"):
        raise ValueError(f"{ScraperCls.__name__} lacks collect_by_url()")

    return scraper.collect_by_url([url])


# ─────────────────────────────────────────────────────────────── single URL (sync)
def scrape_url(
    url: str,
    *,
    bearer_token: str | None = None,
    poll_interval: int = 8,
    poll_timeout:  int = 180,
    fallback_to_browser_api: bool = False,
) -> ScrapeResult | None:
    """
    Fire & wait.  Returns a **ScrapeResult** (or *None* when no scraper +
    no fallback).
    """
    SnapOrNone = trigger_scrape_url(url, bearer_token=bearer_token)
    if SnapOrNone is None:
        if not fallback_to_browser_api:
            return None
        return BrowserAPI().get_page_source_with_a_delay(url)

    ScraperCls = get_scraper_for(url)
    scraper    = ScraperCls(bearer_token=bearer_token)

    # multi-bucket?
    if isinstance(SnapOrNone, dict):
        # Aggregate row counts etc. in a parent result?  Out-of-scope here.
        # Simply poll each bucket and return a mapping {bucket: ScrapeResult}
        return {
            b: scraper.poll_until_ready(
                   sid,
                   poll=poll_interval,
                   timeout=poll_timeout
               )
            for b, sid in SnapOrNone.items()
        }

    # single snapshot
    return scraper.poll_until_ready(
        SnapOrNone,
        poll=poll_interval,
        timeout=poll_timeout,
    )


# ─────────────────────────────────────────────────────────────── single URL (async)
async def scrape_url_async(
    url: str,
    *,
    bearer_token: str | None = None,
    poll_interval: int = 8,
    poll_timeout:  int = 180,
    fallback_to_browser_api: bool = False,
) -> ScrapeResult | Dict[str, ScrapeResult] | None:
    loop = asyncio.get_running_loop()

    # 1) run the *blocking* trigger in a thread
    snap = await loop.run_in_executor(
        None,
        lambda: trigger_scrape_url(url, bearer_token=bearer_token)
    )

    if snap is None:
        if not fallback_to_browser_api:
            return None
        return await loop.run_in_executor(
            None,
            lambda: BrowserAPI().get_page_source_with_a_delay(url)
        )

    ScraperCls = get_scraper_for(url)
    scraper    = ScraperCls(bearer_token=bearer_token)

    if isinstance(snap, dict):            # multi-bucket
        tasks = {
            b: asyncio.create_task(
                   scraper.poll_until_ready_async(
                       sid,
                       poll_interval=poll_interval,
                       timeout=poll_timeout
                   )
               )
            for b, sid in snap.items()
        }
        done  = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), done))

    # single snapshot
    return await scraper.poll_until_ready_async(
        snap,
        poll_interval=poll_interval,
        timeout=poll_timeout,
    )


# ─────────────────────────────────────────────────────────────── many URLs (async)
async def scrape_urls_async(
    urls: List[str],
    *,
    bearer_token: str | None = None,
    poll_interval: int = 8,
    poll_timeout:  int = 180,
    fallback_to_browser_api: bool = False,
    pool_size: int = 8,
) -> Dict[str, Union[ScrapeResult, Dict[str, ScrapeResult], None]]:
    """
    Launch & poll many URLs concurrently.  Unknown URLs optionally fall
    back to Browser-API, sharing at most *pool_size* headless browsers.
    """
    loop = asyncio.get_running_loop()

    # 1) trigger all in a thread-pool
    trigger_futs = {
        u: loop.run_in_executor(
               None, lambda _u=u: trigger_scrape_url(_u, bearer_token)
           )
        for u in urls
    }
    snaps = await asyncio.gather(*trigger_futs.values())
    url_to_snap: Dict[str, Snapshot | None] = dict(zip(urls, snaps))

    # 2) Browser-API pool when needed
    missing  = [u for u, s in url_to_snap.items() if s is None]
    pool: BrowserPool | None = None
    if fallback_to_browser_api and missing:
        pool = BrowserPool(size=min(pool_size, len(missing)),
                           browser_kwargs=dict(load_state="domcontentloaded"))

    # 3) schedule polls / fallbacks
    tasks: Dict[str, asyncio.Task] = {}
    for url, snap in url_to_snap.items():
        ScraperCls = get_scraper_for(url)

        # ---- fallback branch -------------------------------------------
        if snap is None or ScraperCls is None:
            if pool is not None:
                async def _fallback(u=url):
                    api = await pool.acquire()
                    return await api.get_page_source_with_a_delay_async(
                        u, wait_time_in_seconds=25
                    )
                tasks[url] = asyncio.create_task(_fallback())
            else:
                tasks[url] = asyncio.create_task(asyncio.sleep(0, result=None))
            continue

        # ---- Bright-Data branch ----------------------------------------
        scraper = ScraperCls(bearer_token=bearer_token)

        if isinstance(snap, dict):        # multi-bucket
            subtasks = {
                b: asyncio.create_task(
                       scraper.poll_until_ready_async(
                           sid,
                           poll_interval=poll_interval,
                           timeout=poll_timeout
                       )
                   )
                for b, sid in snap.items()
            }
            async def _gather_multi(s=subtasks):
                done = await asyncio.gather(*s.values())
                return dict(zip(s.keys(), done))
            tasks[url] = asyncio.create_task(_gather_multi())
        else:                             # single snapshot
            tasks[url] = asyncio.create_task(
                scraper.poll_until_ready_async(
                    snap,
                    poll_interval=poll_interval,
                    timeout=poll_timeout
                )
            )

    # 4) collect + tidy-up
    gathered = await asyncio.gather(*tasks.values())
    results  = dict(zip(tasks.keys(), gathered))

    if pool is not None:
        await pool.close()

    return results


# ─────────────────────────────────────────────────────────────── many URLs (sync)
def scrape_urls(
    urls: List[str],
    *,
    bearer_token: str | None = None,
    poll_interval: int = 8,
    poll_timeout:  int = 180,
    fallback_to_browser_api: bool = False,
) -> Dict[str, Union[ScrapeResult, Dict[str, ScrapeResult], None]]:
    """Blocking wrapper around :pyfunc:`scrape_urls_async`."""
    return asyncio.run(
        scrape_urls_async(
            urls,
            bearer_token=bearer_token,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
            fallback_to_browser_api=fallback_to_browser_api,
        )
    )




if __name__ == "__main__":
  

    logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s  %(message)s",
)   
 
    # 1) smoke-test scrape_url
    # print("== Smoke-test: scrape_url ==")
    # single = "https://budgety.ai"
    # # fallback_to_browser_api=True so that even un-scrapable URLs return HTML
    # res1 = scrape_url(single, fallback_to_browser_api=True)
    # # pprint.pprint(res1)
    # print(res1)

    
    
    # # 2) smoke-test scrape_urls
    # print("\n== Smoke-test: scrape_urls ==")
    # many = ["https://budgety.ai", "https://openai.com"]
    
    # many =["https://budgety.ai"]

    #many =["https://vickiboykis.com/", "https://www.1337x.to/home/"]
    # many =["https://vickiboykis.com/", "https://www.1337x.to/home/","https://budgety.ai", "https://openai.com"]
    # again fallback=True so that non-registered scrapers will return HTML
    # many = ["https://budgety.ai", "https://openai.com"]

    # b="https://openai.com/news/"

    b="https://www.reddit.com/r/OpenAI/"
    a="https://community.openai.com/t/openai-website-rss-feed-inquiry/733747"
    
    many= [a,b]
    
    results = scrape_urls(many, fallback_to_browser_api=True)
     
    show_scrape_results("AUTO TEST", results)

   