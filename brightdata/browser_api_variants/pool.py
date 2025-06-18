#!/usr/bin/env python3
"""
fallback_strategies/pool

A “pooled” IsolatedPlaywrightSession fetcher:

  • Keeps a fixed‐size pool of CDP connections (sessions).
  • For each URL, grabs the next session (round-robin), opens a new
    incognito context/page, navigates, tears down *that* context, but
    leaves the underlying CDP connection alive.
  • At the end it gracefully closes all sessions.

Usage:
    python fallback_strategies/pool.py
"""

import asyncio
import logging

from isolated_playwright_session import IsolatedPlaywrightSession

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# How many concurrent CDP connections to keep alive
_POOL_SIZE = 5


# ─── SESSION POOL IMPLEMENTATION ─────────────────────────────────────────────

class SessionPool:
    def __init__(self, size: int = _POOL_SIZE):
        self.size = size
        self._sessions: list[IsolatedPlaywrightSession] = []
        self._idx = 0
        self._lock = asyncio.Lock()

    async def _ensure_pool(self) -> None:
        async with self._lock:
            while len(self._sessions) < self.size:
                sess = await IsolatedPlaywrightSession.create()
                self._sessions.append(sess)

    async def acquire(self) -> IsolatedPlaywrightSession:
        await self._ensure_pool()
        sess = self._sessions[self._idx % self.size]
        self._idx += 1
        return sess

    async def close(self) -> None:
        for sess in self._sessions:
            await sess.close()
        self._sessions.clear()


# ─── PUBLIC FETCH FUNCTION ───────────────────────────────────────────────────

_pool = SessionPool()


async def fetch(
    url: str,
    *,
    wait_until: str = "domcontentloaded",
    timeout: int = 60_000,
    headless: bool = True,
    window_size: tuple[int, int] = (1920, 1080),
) -> tuple[str, float]:
    """
    Fetch the given URL using a pooled session.

    Returns
    -------
    html : str
      The page HTML.
    elapsed : float
      Seconds spent on navigation.
    """
    sess = await _pool.acquire()
    page = await sess.new_page(headless=headless, window_size=window_size)
    t0 = asyncio.get_event_loop().time()
    await page.goto(url, timeout=timeout, wait_until=wait_until)
    elapsed = asyncio.get_event_loop().time() - t0
    html = await page.content()
    await page.context.close()
    return html, elapsed


# ─── SMOKE-TESTS ──────────────────────────────────────────────────────────────

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

    # 1) sequential, one by one
    print("\n=== sequential (one-by-one) ===")
    async def _run_sequential():
        for url in URLS:
            try:
                html, took = await fetch(url)
                print(f"✓ {url!r}: {len(html)} chars in {took:.2f}s")
            except Exception as e:
                print(f"✗ {url!r}: error {e!r}")
        # tear down all sessions
        await _pool.close()

    asyncio.run(_run_sequential())

    # 2) parallel, all scheduled at once (round-robin across pool)
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
        # tear down all sessions
        await _pool.close()

    asyncio.run(_run_parallel())
