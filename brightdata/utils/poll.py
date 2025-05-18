"""
brightdata.utils.poll
---------------------

A **blocking** helper that repeatedly calls
`BrightdataBaseSpecializedScraper.get_data()` until the snapshot is ready,
fails, or a timeout is reached.

Usage
~~~~~
>>> from brightdata.utils.poll import poll_until_ready
>>> res = poll_until_ready(scraper, snapshot_id, poll=12, timeout=300)
>>> if res.status == "ready":
...     print(res.data)
"""

from __future__ import annotations
import time
from typing import Union, Callable, Optional
from brightdata.base_specialized_scraper import ScrapeResult


def poll_until_ready(
    scraper,                       # any subclass of BrightdataBaseSpecializedScraper
    snapshot_id: str,
    *,
    poll: int = 10,                # seconds between probes
    timeout: int = 600,            # give up after N seconds
    on_update: Optional[Callable[[str], None]] = None,
) -> ScrapeResult:
    """
    Parameters
    ----------
    scraper      : instance that implements .get_data(snapshot_id) → ScrapeResult
    snapshot_id  : str  – returned by `_trigger()`
    poll         : int  – seconds between /progress calls
    timeout      : int  – absolute ceiling in seconds
    on_update    : callable(status_str) – optional; called every poll-loop

    Returns
    -------
    ScrapeResult
        • success=True,  status="ready",  data=[...]       → finished
        • success=False, status="error",  error="…"        → Bright-Data error
        • success=False, status="timeout", error="…"       → we gave up
        • success=True,  status="not_ready", data=None     → *only* if timeout=0
    """
    start = time.time()
    while True:
        res: ScrapeResult = scraper.get_data(snapshot_id)

        # finished (either OK or ERROR inside Bright Data)
        if res.status in {"ready", "error"}:
            return res

        # inform caller every iteration
        if on_update:
            on_update(res.status)

        # time-out check
        elapsed = time.time() - start
        if elapsed >= timeout:
            return ScrapeResult(
                success=False,
                status="timeout",
                error=f"gave up after {timeout}s",
            )

        time.sleep(poll)
