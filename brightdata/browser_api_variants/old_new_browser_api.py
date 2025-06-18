# brightdata/new_browser_api.py

import os
import time
import asyncio
import logging
from typing import Literal, Optional, List, Tuple

from playwright.async_api import TimeoutError as PWTimeoutError, Error as PWError

from isolated_playwright_session import IsolatedPlaywrightSession

logger = logging.getLogger(__name__)


class NewBrowserAPI:
    """
    A single Browser-API façade with three strategies:

      • noop      → spin up & tear down a session per URL
      • semaphore → same, but limit # concurrent sessions
      • pool      → keep a fixed pool of CDP sessions and reuse them

    Returns: (html: str, elapsed: float)
    """

    def __init__(
        self,
        *,
        strategy: Literal["noop", "semaphore", "pool"] = "noop",
        pool_size: int = 5,
        max_concurrent: Optional[int] = None,
    ):
        self.strategy = strategy
        self.pool_size = pool_size
        # for semaphore strategy: how many in-flight at once
        self._max_concurrent = max_concurrent or pool_size

        # semaphore object for throttling
        if self.strategy == "semaphore":
            self._sem = asyncio.Semaphore(self._max_concurrent)

        # session pool for reuse
        self._sessions: List[IsolatedPlaywrightSession] = []
        self._rr_idx = 0

    # ─── core fetch logic ──────────────────────────────────────────


    def calculate_cost(self, raw_html: str) -> float:
        """
        Returns the USD cost to transfer `raw_html` bytes,
        assuming $8.40 per GiB (1 GiB = 1024³ bytes).
        """
        # how many bytes did we actually transfer?
        byte_count = len(raw_html.encode("utf-8"))
        # cost = bytes / bytes_per_gib * dollars_per_gib
        return byte_count / (1024**3) * 8.40
    


    async def _fetch_isolated(
        self,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout: int = 60_000,
        headless: bool = True,
        window_size: tuple[int, int] = (1920, 1080),
    ) -> Tuple[str, float]:
        """spin up one session, fetch, tear down."""
        return await IsolatedPlaywrightSession.fetch(
            url,
            wait_until=wait_until,
            timeout=timeout,
            headless=headless,
            window_size=window_size,
        )

    async def _ensure_pool(self) -> None:
        """lazily build up to pool_size sessions."""
        while len(self._sessions) < self.pool_size:
            sess = await IsolatedPlaywrightSession.create()
            self._sessions.append(sess)

    async def _fetch_from_pool(
        self,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout: int = 60_000,
        headless: bool = True,
        window_size: tuple[int, int] = (1920, 1080),
    ) -> Tuple[str, float]:
        """round-robin pick a long-lived session and fetch."""
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

    # ─── public API ────────────────────────────────────────────────


    async def _do_strategy_fetch(
        self,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout: int = 60_000,
        headless: bool = True,
        window_size: tuple[int, int] = (1920, 1080),
    ) -> tuple[str, float]:
        """
        Pick the right fetch implementation based on self.strategy,
        and return (html, elapsed_seconds).
        """
        if self.strategy == "noop":
            # cold-start per request
            return await self._fetch_isolated(
                url,
                wait_until=wait_until,
                timeout=timeout,
                headless=headless,
                window_size=window_size,
            )

        elif self.strategy == "semaphore":
            # throttle concurrency
            async with self._sem:
                return await self._fetch_isolated(
                    url,
                    wait_until=wait_until,
                    timeout=timeout,
                    headless=headless,
                    window_size=window_size,
                )

        elif self.strategy == "pool":
            # reuse sessions in a round-robin pool
            return await self._fetch_from_pool(
                url,
                wait_until=wait_until,
                timeout=timeout,
                headless=headless,
                window_size=window_size,
            )

        else:
            raise ValueError(f"Unknown strategy: {self.strategy!r}")

    async def fetch_async(
        self,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout: int = 60_000,
        headless: bool = True,
        window_size: tuple[int, int] = (1920, 1080),
    ) -> Tuple[str, float]:
        """
        Fetch one URL and return (html, elapsed_seconds) according
        to the chosen strategy.
        """

        html, elapsed = await self._do_strategy_fetch(url, **kwargs)
        cost = self.calculate_cost(html)
        self.total_bytes += len(html.encode("utf-8"))
        self.total_cost  += cost
        return html, elapsed, cost

        # if self.strategy == "noop":
        #     return await self._fetch_isolated(
        #         url, wait_until=wait_until, timeout=timeout,
        #         headless=headless, window_size=window_size
        #     )

        # elif self.strategy == "semaphore":
        #     async with self._sem:
        #         return await self._fetch_isolated(
        #             url, wait_until=wait_until, timeout=timeout,
        #             headless=headless, window_size=window_size
        #         )

        # elif self.strategy == "pool":
        #     return await self._fetch_from_pool(
        #         url, wait_until=wait_until, timeout=timeout,
        #         headless=headless, window_size=window_size
        #     )

        # else:
        #     raise ValueError(f"Unknown strategy {self.strategy!r}")
        



    def fetch(
        self,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout: int = 60_000,
        headless: bool = True,
        window_size: tuple[int, int] = (1920, 1080),
    ) -> Tuple[str, float]:
        """
        Sync wrapper around fetch_async().
        """
        return asyncio.run(self.fetch_async(
            url,
            wait_until=wait_until,
            timeout=timeout,
            headless=headless,
            window_size=window_size,
        ))

    async def close(self) -> None:
        """
        Tear down any pooled sessions (noop/semaphore have nothing to close).
        """
        if self.strategy == "pool" and self._sessions:
            await asyncio.gather(*(sess.close() for sess in self._sessions))
            self._sessions.clear()

    def __del__(self):
        # best‐effort cleanup if they forgot to close()
        try:
            if self.strategy == "pool":
                asyncio.run(self.close())
        except Exception:
            pass


# ─── Demo / smoke‐test ──────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s  %(message)s",
    )

    async def main():
        urls = ["https://example.com", "https://openai.com"]

        # 1) No‐pool (cold start each time)
        api1 = NewBrowserAPI(strategy="noop")
        for u in urls:
            html, t, c = await api1.fetch_async(u, wait_until="domcontentloaded")
            print("noop:", u, len(html), f"{t:.2f}s")
        await api1.close()

        # 2) Semaphore (limit to 3 concurrent)
        api2 = NewBrowserAPI(strategy="semaphore", max_concurrent=3)
        tasks = [api2.fetch_async(u) for u in urls]
        results = await asyncio.gather(*tasks)
        for u, (html, t) in zip(urls, results):
            print("sem :", u, len(html), f"{t:.2f}s")
        await api2.close()
        
        # 3) Pool (reuse 2 sessions)
        api3 = NewBrowserAPI(strategy="pool", pool_size=2)
        tasks = [api3.fetch_async(u) for u in urls]
        results = await asyncio.gather(*tasks)
        for u, (html, t) in zip(urls, results):
            print("pool:", u, len(html), f"{t:.2f}s")
        await api3.close()

    asyncio.run(main())
