#brightdata/utils/poll.py
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
from pprint import pprint
from brightdata.models import ScrapeResult
import tldextract



# def poll_until_ready(
#     scraper,                       # any subclass of BrightdataBaseSpecializedScraper
#     snapshot_id: str,
#     *,
#     poll: int = 10,                # seconds between probes
#     timeout: int = 600,            # give up after N seconds
#     on_update: Optional[Callable[[str], None]] = None,
# ) -> ScrapeResult:
#     """
#     Parameters
#     ----------
#     scraper      : instance that implements .get_data(snapshot_id) → ScrapeResult
#     snapshot_id  : str  – returned by `_trigger()`
#     poll         : int  – seconds between /progress calls
#     timeout      : int  – absolute ceiling in seconds
#     on_update    : callable(status_str) – optional; called every poll-loop

#     Returns
#     -------
#     ScrapeResult
#         • success=True,  status="ready",  data=[...]       → finished
#         • success=False, status="error",  error="…"        → Bright-Data error
#         • success=False, status="timeout", error="…"       → we gave up
#         • success=True,  status="not_ready", data=None     → *only* if timeout=0
#     """
#     start = time.time()
#     while True:
#         res: ScrapeResult = scraper.get_data(snapshot_id)

#         # finished (either OK or ERROR inside Bright Data)
#         if res.status in {"ready", "error"}:
#             return res

#         # inform caller every iteration
#         if on_update:
#             on_update(res.status)

#         # time-out check
#         elapsed = time.time() - start
#         if elapsed >= timeout:
#             return ScrapeResult(
#                 success=False,
#                 status="timeout",
#                 error=f"gave up after {timeout}s",
#             )

#         time.sleep(poll)



def poll_until_ready(
    scraper,                       # any subclass of BrightdataBaseSpecializedScraper
    snapshot_id: str,
    *,
    poll: int = 10,                # seconds between probes
    timeout: int = 600,            # give up after N seconds
    on_update: Optional[Callable[[str], None]] = None,
) -> ScrapeResult:
    """
    Repeatedly calls `scraper.get_data(snapshot_id)` until completion or timeout.
    Returns a fully populated ScrapeResult.
    """
    start = time.time()
    status_url = f"{scraper.status_base_url}/{snapshot_id}"
    # Extract root_domain for reuse
    ext = tldextract.extract(status_url)
    root = ext.domain or None

    while True:
        res: ScrapeResult = scraper.get_data(snapshot_id)

        # finished (ready or error inside Bright Data)
        if res.status in {"ready", "error"}:
            return res

        if on_update:
            on_update(res.status)

        elapsed = time.time() - start
        if elapsed >= timeout:
            return ScrapeResult(
                success=False,
                url=status_url,
                status="timeout",
                data=None,
                error=f"gave up after {timeout}s",
                snapshot_id=snapshot_id,
                cost=None,
                fallback_used=False,
                root_domain=root,
            )

        time.sleep(poll)


def poll_until_ready_and_show(scraper, label: str, snap_id: str, timeout=600):
        print(f"\n=== {label} ===  (snapshot: {snap_id})")
        res = poll_until_ready(scraper, snap_id, poll=10, timeout=timeout)
        
        if res.status == "ready":
            print(f"{label} ✓  received {len(res.data)} rows")
            pprint(res.data[:2])
        else:
            print(f"{label} ✗  {res.status} – {res.error or ''}")



