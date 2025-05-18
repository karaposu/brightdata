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

load_dotenv()

Rows = List[Dict[str, Any]]
Snapshot = Union[str, Dict[str, str]]
ResultData = Union[Rows, Dict[str, Rows], ScrapeResult]


def trigger_scrape_url(
    url: str,
    bearer_token: str | None = None,
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
        raise ValueError(f"No scraper registered for {url}")

    scraper = ScraperCls(bearer_token=token)
    if not hasattr(scraper, "collect_by_url"):
        raise ValueError(f"{ScraperCls.__name__} does not implement collect_by_url()")

    # Returns either a str snapshot_id or a dict of them
    return scraper.collect_by_url([url])


def scrape_url(
    url: str,
    bearer_token: str | None = None,
    poll: bool = True,
    poll_interval: int = 8,
    poll_timeout: int = 180,
) -> ResultData:
    """
    High-level scrape: trigger + (optionally) wait for data.

    Parameters
    ----------
    url           – a single URL to scrape
    bearer_token  – your Bright Data token (or set BRIGHTDATA_TOKEN)
    poll          – if True, block until ready; else return snapshot_id
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
    snap = scrape_trigger_url(url, bearer_token=bearer_token)
    token = bearer_token or os.getenv("BRIGHTDATA_TOKEN")
    ScraperCls = get_scraper_for(url)

    if not poll:
        return snap

    # Multi‐bucket case (e.g. LinkedIn returns {"people": id1, ...})
    if isinstance(snap, dict):
        results: Dict[str, Any] = {}
        for key, sid in snap.items():
            scraper = ScraperCls(bearer_token=token)
            res = poll_until_ready(
                scraper,
                sid,
                interval=poll_interval,
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
        interval=poll_interval,
        timeout=poll_timeout,
    )
    if res.status == "ready":
        return res.data
    return res
