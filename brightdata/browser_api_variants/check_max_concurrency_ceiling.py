#!/usr/bin/env python3
"""
check_max_concurrency_ceiling.py

Exercise each BrowserAPI strategy at increasing parallel‐fetch levels
to see where errors or big slowdowns kick in.

For each strategy ∈ {noop, semaphore, pool} and each concurrency level,
we fire that many simultaneous fetches of a cheap page (example.com),
then print avg/max latency, error count and total batch time.

Usage:
  cd brightdata/browser_api_variants
  python check_max_concurrency_ceiling.py
"""
import asyncio
import time
import logging

from new_browser_api import NewBrowserAPI

#–– Define the concurrency levels you want to test
CONCURRENCY_LEVELS = [1, 5, 10, 20, 50, 100]

#–– The strategies to test and their per‐strategy kwargs
STRATEGIES = [
    ("noop",        dict(strategy="noop")),
    ("semaphore=25",dict(strategy="semaphore", max_concurrent=25)),
    ("semaphore=50",dict(strategy="semaphore", max_concurrent=50)),
    ("pool=25",     dict(strategy="pool",     pool_size=25)),
    ("pool=50",     dict(strategy="pool",     pool_size=50)),
]

TEST_URL = "https://example.com"


async def run_batch(name: str, api_kwargs: dict, concurrency: int):
    log = logging.getLogger(f"{name}@{concurrency}")
    log.info(f"→ starting {concurrency} parallel fetches")
    api = NewBrowserAPI(**api_kwargs)
    start = time.time()
    # schedule them all at once
    tasks = [api.fetch_async(TEST_URL, wait_until="domcontentloaded") for _ in range(concurrency)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total = time.time() - start

    latencies = []
    errors = 0
    for r in results:
        if isinstance(r, Exception):
            errors += 1
        else:
            html, took = r
            latencies.append(took)

    avg = sum(latencies) / len(latencies) if latencies else float("nan")
    mx  = max(latencies) if latencies else float("nan")
    err_pct = errors / concurrency * 100

    log.info(f"   avg latency = {avg:.2f}s   max = {mx:.2f}s   errors = {errors}/{concurrency} ({err_pct:.1f}%)")
    log.info(f"   total batch time = {total:.2f}s\n")

    # clean up
    # NewBrowserAPI.close() should be synchronous or awaited if async
    maybe = api.close()
    if asyncio.iscoroutine(maybe):
        await maybe


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    for name, kwargs in STRATEGIES:
        logging.info(f"=== Strategy: {name} ===")
        for lvl in CONCURRENCY_LEVELS:
            await run_batch(name, kwargs, lvl)
        print()

if __name__ == "__main__":
    asyncio.run(main())
