# brightdata/utils/async_poll.py
import asyncio, time
from aiohttp import ClientSession
from brightdata.base_specialized_scraper import ScrapeResult

POLL    = 10     # seconds between /progress probes
TIMEOUT = 600    # give up after n seconds

async def wait_ready(
    scraper,
    snapshot_id: str,
    session: ClientSession,
    *,
    poll: int = POLL,
    timeout: int = TIMEOUT,
) -> ScrapeResult:
    """
    Coroutine that polls Bright-Data until the snapshot is *ready*,
    *error*, or we hit *timeout*.  Never raises; always returns ScrapeResult.
    """
    start = time.time()
    while True:
        res: ScrapeResult = await scraper.get_data_async(snapshot_id, session)

        if res.status in {"ready", "error"}:
            return res
        if time.time() - start >= timeout:
            return ScrapeResult(False, "timeout",
                                error=f"gave up after {timeout}s")

        await asyncio.sleep(poll)

import aiohttp, asyncio
from typing import List

async def monitor_snapshots(scraper, snapshot_ids: List[str],
                            *, poll=10, timeout=600):
    """
    Launch N coroutines, each polling one snapshot, and wait for *all* to
    finish.  Returns list[ScrapeResult] in the same order as snapshot_ids.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [
            wait_ready(scraper, sid, session, poll=poll, timeout=timeout)
            for sid in snapshot_ids
        ]
        return await asyncio.gather(*tasks)
