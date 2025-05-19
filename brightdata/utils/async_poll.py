# brightdata/utils/async_poll.py
"""
Async helpers for retrieving Bright Data snapshot results.

Typical flow
------------
1.  You *trigger* one or many jobs on Bright Data (all return a `snapshot_id`).
2.  Pass those snapshot-ids to **fetch_snapshot_async** / **fetch_snapshots_async**.
3.  Await the coroutine(s) → you get `ScrapeResult` objects.

Why two functions?
------------------
* **fetch_snapshot_async** – low-level, deals with **one** snapshot-id.
  Perfect when you occasionally need to wait for a single job inside an
  already-async application.

* **fetch_snapshots_async** – convenience wrapper that fan-outs *N* polling
  coroutines (one per id) and gathers them back. Handy when you just launched
  hundreds of jobs and don’t want to write the task orchestration yourself.
"""

from __future__ import annotations

import asyncio
import time
from typing import List

import aiohttp

from brightdata.base_specialized_scraper import ScrapeResult

# Default timings – can be overridden per call
POLL_INTERVAL = 10     # seconds between /progress probes
TIMEOUT_SEC   = 600    # overall ceiling


# ──────────────────────────────────────────────────────────────
# Single-snapshot helper
# ──────────────────────────────────────────────────────────────
async def fetch_snapshot_async(
    scraper,
    snapshot_id: str,
    *,
    session: aiohttp.ClientSession | None = None,
    poll: int   = POLL_INTERVAL,
    timeout: int = TIMEOUT_SEC,
) -> ScrapeResult:
    """
    **Await the final state of ONE Bright Data job.**

    Parameters
    ----------
    scraper      – an *instantiated* ready_scraper (e.g. ``AmazonScraper``)
    snapshot_id  – the id returned by any ``collect_*`` / ``discover_*`` call
    session      – optional shared ``aiohttp.ClientSession`` (performance)
    poll         – seconds to sleep between status checks
    timeout      – give up and return ``ScrapeResult(status="timeout")``

    Returns
    -------
    ``ScrapeResult`` with status = ``"ready"`` | ``"error"`` | ``"timeout"``
    (never raises).
    """
    own_session = False
    if session is None:                       # allow standalone use
        session = aiohttp.ClientSession()
        own_session = True

    start = time.time()
    try:
        while True:
            res: ScrapeResult = await scraper.get_data_async(snapshot_id, session)

            if res.status in {"ready", "error"}:
                return res

            if time.time() - start >= timeout:
                return ScrapeResult(False, "timeout",
                                    error=f"gave up after {timeout}s")

            await asyncio.sleep(poll)

    finally:
        if own_session:
            await session.close()


# ──────────────────────────────────────────────────────────────
# Many-snapshots helper
# ──────────────────────────────────────────────────────────────
async def fetch_snapshots_async(
    scraper,
    snapshot_ids: List[str],
    *,
    poll: int   = POLL_INTERVAL,
    timeout: int = TIMEOUT_SEC,
) -> List[ScrapeResult]:
    """
    **Await the final state of MANY Bright Data jobs in parallel.**

    Spawns one coroutine per snapshot-id, all sharing a single
    ``aiohttp.ClientSession`` for efficiency.

    Returns
    -------
    ``List[ScrapeResult]`` – **same order** as *snapshot_ids*.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_snapshot_async(
                scraper,
                sid,
                session=session,
                poll=poll,
                timeout=timeout,
            )
            for sid in snapshot_ids
        ]
        return await asyncio.gather(*tasks)
