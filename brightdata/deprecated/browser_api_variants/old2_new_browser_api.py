# brightdata/new_browser_api.py

import os
import time
import asyncio
import logging
from typing import Literal, Optional, List, Tuple

from isolated_playwright_session import IsolatedPlaywrightSession

logger = logging.getLogger(__name__)


class NewBrowserAPI:
    """
    A single Browser-API façade with three strategies:

      • noop      → spin up & tear down a session per URL
      • semaphore → same, but limit # concurrent sessions
      • pool      → keep a fixed pool of CDP sessions and reuse them

    fetch_async() returns: (html: str, elapsed: float, cost: float)
    """

    COST_PER_GIB = 8.40   # USD per GiB
    GIB = 1024 ** 3

    def __init__(
        self,
        *,
        strategy: Literal["noop", "semaphore", "pool"] = "noop",
        pool_size: int = 5,
        max_concurrent: Optional[int] = None,
    ):
        self.strategy = strategy
        self.pool_size = pool_size
        # semaphore cap (for "semaphore" strategy)
        self._max_concurrent = max_concurrent or pool_size

        if self.strategy == "semaphore":
            self._sem = asyncio.Semaphore(self._max_concurrent)

        # for the "pool" strategy
        self._sessions: List[IsolatedPlaywrightSession] = []
        self._rr_idx = 0

        # track usage
        self.total_bytes = 0
        self.total_cost  = 0.0

    def calculate_cost(self, raw_html: str) -> float:
        """
        USD cost to transfer the given HTML payload.
        """
        byte_count = len(raw_html.encode("utf-8"))
        return byte_count / self.GIB * self.COST_PER_GIB

    # ─── core fetch implementations ─────────────────────────────────

    async def _fetch_isolated(
        self,
        url: str,
        *,
        wait_until: str,
        timeout: int,
        headless: bool,
        window_size: Tuple[int, int],
    ) -> Tuple[str, float]:
        return await IsolatedPlaywrightSession.fetch(
            url=url,
            wait_until=wait_until,
            timeout=timeout,
            headless=headless,
            window_size=window_size,
        )

    async def _ensure_pool(self) -> None:
        while len(self._sessions) < self.pool_size:
            sess = await IsolatedPlaywrightSession.create()
            self._sessions.append(sess)

    async def _fetch_from_pool(
        self,
        url: str,
        *,
        wait_until: str,
        timeout: int,
        headless: bool,
        window_size: Tuple[int, int],
    ) -> Tuple[str, float]:
        await self._ensure_pool()
        sess = self._sessions[self._rr_idx % len(self._sessions)]
        self._rr_idx += 1

        page = await sess.new_page(headless=headless, window_size=window_size)
        t0 = time.time()
        await page.goto(url, timeout=timeout, wait_until=wait_until)
        elapsed = time.time() - t0
        html = await page.content()
        await page.context.close()
        return html, elapsed

    # ─── unified strategy selector ─────────────────────────────────

    async def _do_strategy_fetch(
        self,
        url: str,
        *,
        wait_until: str,
        timeout: int,
        headless: bool,
        window_size: Tuple[int, int],
    ) -> Tuple[str, float]:
        if self.strategy == "noop":
            return await self._fetch_isolated(
                url, wait_until=wait_until,
                timeout=timeout, headless=headless,
                window_size=window_size,
            )

        elif self.strategy == "semaphore":
            async with self._sem:
                return await self._fetch_isolated(
                    url, wait_until=wait_until,
                    timeout=timeout, headless=headless,
                    window_size=window_size,
                )

        elif self.strategy == "pool":
            return await self._fetch_from_pool(
                url, wait_until=wait_until,
                timeout=timeout, headless=headless,
                window_size=window_size,
            )

        else:
            raise ValueError(f"Unknown strategy {self.strategy!r}")

    # ─── public API ────────────────────────────────────────────────

    async def fetch_async(
        self,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout: int = 60_000,
        headless: bool = True,
        window_size: Tuple[int, int] = (1920, 1080),
    ) -> Tuple[str, float, float]:
        """
        Fetch one URL and return (html, elapsed_seconds, cost_usd).
        """
        html, elapsed = await self._do_strategy_fetch(
            url,
            wait_until=wait_until,
            timeout=timeout,
            headless=headless,
            window_size=window_size,
        )

        cost = self.calculate_cost(html)
        self.total_bytes += len(html.encode("utf-8"))
        self.total_cost  += cost

        return html, elapsed, cost

    def fetch(
        self,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout: int = 60_000,
        headless: bool = True,
        window_size: Tuple[int, int] = (1920, 1080),
    ) -> Tuple[str, float, float]:
        """
        Sync wrapper around fetch_async().
        """
        return asyncio.run(self.fetch_async(
            url=url,
            wait_until=wait_until,
            timeout=timeout,
            headless=headless,
            window_size=window_size,
        ))

    async def close(self) -> None:
        """
        Tear down any persistent sessions (only for pool strategy).
        """
        if self.strategy == "pool" and self._sessions:
            await asyncio.gather(*(sess.close() for sess in self._sessions))
            self._sessions.clear()

    def __del__(self):
        # best-effort cleanup
        if self.strategy == "pool" and self._sessions:
            try:
                asyncio.run(self.close())
            except Exception:
                pass


# ─── Demo / smoke-test ──────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    async def main():
        urls = ["https://example.com", "https://openai.com"]

        # 1) noop
        api1 = NewBrowserAPI(strategy="noop")
        for u in urls:
            html, t, c = await api1.fetch_async(u)
            print(f"noop: {u:>25} → {len(html):6} chars, {t:.2f}s, ${c:.5f}")
        await api1.close()

        # 2) semaphore
        api2 = NewBrowserAPI(strategy="semaphore", max_concurrent=3)
        tasks = [api2.fetch_async(u) for u in urls]
        for (html, t, c), u in zip(await asyncio.gather(*tasks), urls):
            print(f"sema: {u:>25} → {len(html):6} chars, {t:.2f}s, ${c:.5f}")
        await api2.close()

        # 3) pool
        api3 = NewBrowserAPI(strategy="pool", pool_size=2)
        tasks = [api3.fetch_async(u) for u in urls]
        for (html, t, c), u in zip(await asyncio.gather(*tasks), urls):
            print(f"pool: {u:>25} → {len(html):6} chars, {t:.2f}s, ${c:.5f}")
        await api3.close()

    asyncio.run(main())
