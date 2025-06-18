#!/usr/bin/env python3
"""
fallback_strategies/semaphore

A semaphore‐throttled isolated‐session fetcher:

  • Reuses your IsolatedPlaywrightSession.fetch convenience method
    but caps the number of concurrent CDP sessions to avoid resource exhaustion.
  • Each fetch still spins up its own CDP connection + browser context,
    then tears it down—so there’s no shared global state to collide.

At the bottom you’ll find:

  • a sequential smoke-test (awaiting one fetch at a time)
  • a parallel smoke-test (kicking off all fetches together under the semaphore)

Usage:
    python semaphore.py

  
"""

import asyncio
import logging

# from browser_api_variants.isolated_playwright_session import IsolatedPlaywrightSession
from isolated_playwright_session import IsolatedPlaywrightSession

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Maximum number of simultaneous CDP sessions
_MAX_CONCURRENT = 5

# Semaphore to throttle concurrency
_SEMAPHORE = asyncio.Semaphore(_MAX_CONCURRENT)


# ─── PUBLIC API ───────────────────────────────────────────────────────────────

async def fetch(
    url: str,
    *,
    wait_until: str = "domcontentloaded",
    timeout: int = 60_000,
    headless: bool = True,
    window_size: tuple[int, int] = (1920, 1080),
) -> tuple[str, float]:
    """
    Fetch the given URL by spinning up an isolated CDP session,
    waiting for the page, then tearing it down—throttled so that
    no more than _MAX_CONCURRENT sessions run in parallel.

    Returns
    -------
    html : str
      The page’s HTML.
    elapsed : float
      Seconds elapsed during navigation.
    """
    async with _SEMAPHORE:
        return await IsolatedPlaywrightSession.fetch(
            url,
            wait_until=wait_until,
            timeout=timeout,
            headless=headless,
            window_size=window_size,
        )


# ─── SMOKE-TEST under “python semaphore.py” ────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s  %(message)s",
    )
    
    URLS = [
        "https://example.com",
        "https://openai.com",
        "https://medium.com",
        "https://news.ycombinator.com",
    ]

    # 1) sequential, one at a time
    print("\n=== sequential (one-by-one) ===")
    async def _run_sequential():
        for url in URLS:
            try:
                html, took = await fetch(url)
                print(f"✓ {url!r}: {len(html)} chars in {took:.2f}s")
            except Exception as e:
                print(f"✗ {url!r}: error {e!r}")

    asyncio.run(_run_sequential())

    # 2) parallel, all scheduled at once (throttled by semaphore)
    print("\n=== parallel (async gather) ===")
    async def _run_parallel():
        tasks = [fetch(u) for u in URLS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for url, res in zip(URLS, results):
            if isinstance(res, Exception):
                print(f"✗ {url!r}: error {res!r}")
            else:
                html, took = res
                print(f"✓ {url!r}: {len(html)} chars in {took:.2f}s")
    
    asyncio.run(_run_parallel())
