# brightdata/new_browser_api.py

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional, List, Tuple


import logging

# suppress filelock chatter
logging.getLogger("filelock").setLevel(logging.WARNING)
# optionally mute tldextract’s own logs too
logging.getLogger("tldextract").setLevel(logging.WARNING)

import tldextract
from isolated_playwright_session import IsolatedPlaywrightSession

logger = logging.getLogger(__name__)

@dataclass
class ScrapeResult:
    success: bool
    url: str
    status: str
    data: Optional[str] = None
    error: Optional[str] = None
    snapshot_id: Optional[str] = None
    cost: Optional[float] = None
    fallback_used: bool = True
    root_domain: Optional[str] = None
    request_sent_at: Optional[datetime] = None
    snapshot_id_received_at: Optional[datetime] = None
    snapshot_polled_at: List[datetime] = field(default_factory=list)
    data_received_at: Optional[datetime] = None
    event_loop_id: Optional[int] = None
    browser_warmed_at: Optional[datetime] = None
    html_char_size: Optional[int] = None


class NewBrowserAPI:
    """
    A single Browser-API façade with three strategies, returning ScrapeResult:

      • noop      → spin up & tear down a session per URL
      • semaphore → same, but limit # concurrent sessions
      • pool      → keep a fixed pool of CDP sessions and reuse them
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
        self._max_concurrent = max_concurrent or pool_size

        if self.strategy == "semaphore":
            self._sem = asyncio.Semaphore(self._max_concurrent)

        self._sessions: List[IsolatedPlaywrightSession] = []
        self._rr_idx = 0

        # usage tracking
        self.total_bytes = 0
        self.total_cost  = 0.0

    def _extract_root(self, url: str) -> Optional[str]:
        e = tldextract.extract(url)
        return e.domain or None

    def calculate_cost(self, raw_html: str) -> float:
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
                url=url,
                wait_until=wait_until,
                timeout=timeout,
                headless=headless,
                window_size=window_size,
            )
        elif self.strategy == "semaphore":
            async with self._sem:
                return await self._fetch_isolated(
                    url=url,
                    wait_until=wait_until,
                    timeout=timeout,
                    headless=headless,
                    window_size=window_size,
                )
        elif self.strategy == "pool":
            return await self._fetch_from_pool(
                url=url,
                wait_until=wait_until,
                timeout=timeout,
                headless=headless,
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
    ) -> ScrapeResult:
        try:
            html, elapsed = await self._do_strategy_fetch(
                url=url,
                wait_until=wait_until,
                timeout=timeout,
                headless=headless,
                window_size=window_size,
            )
            cost = self.calculate_cost(html)
            self.total_bytes += len(html.encode("utf-8"))
            self.total_cost  += cost

            return ScrapeResult(
                success=True,
                url=url,
                status="ready",
                data=html,
                error=None,
                root_domain=self._extract_root(url),
                cost=cost,
                request_sent_at=None,
                data_received_at=None,
                event_loop_id=id(asyncio.get_running_loop()),
                browser_warmed_at=None,
                html_char_size=len(html),
            )
        except Exception as e:
            logger.error("fetch_async failed for %s: %s", url, e)
            return ScrapeResult(
                success=False,
                url=url,
                status="error",
                data=None,
                error=str(e),
                root_domain=self._extract_root(url),
                cost=0.0,
                request_sent_at=None,
                data_received_at=None,
                event_loop_id=id(asyncio.get_running_loop()),
            )

    def fetch(
        self,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout: int = 60_000,
        headless: bool = True,
        window_size: Tuple[int, int] = (1920, 1080),
    ) -> ScrapeResult:
        return asyncio.run(self.fetch_async(
            url=url,
            wait_until=wait_until,
            timeout=timeout,
            headless=headless,
            window_size=window_size,
        ))

    async def close(self) -> None:
        if self.strategy == "pool" and self._sessions:
            await asyncio.gather(*(sess.close() for sess in self._sessions))
            self._sessions.clear()

    def __del__(self):
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

        api = NewBrowserAPI(strategy="noop")
        for u in urls:
            res = await api.fetch_async(u)
            print(f"noop: {u:>25} → {res.html_char_size} chars, "
                  f"${res.cost:.5f}, status={res.status}")
        await api.close()

        api = NewBrowserAPI(strategy="semaphore", max_concurrent=3)
        tasks = [api.fetch_async(u) for u in urls]
        for res, u in zip(await asyncio.gather(*tasks), urls):
            print(f"sema: {u:>25} → {res.html_char_size} chars, "
                  f"${res.cost:.5f}, status={res.status}")
        await api.close()

        api = NewBrowserAPI(strategy="pool", pool_size=2)
        tasks = [api.fetch_async(u) for u in urls]
        for res, u in zip(await asyncio.gather(*tasks), urls):
            print(f"pool: {u:>25} → {res.html_char_size} chars, "
                  f"${res.cost:.5f}, status={res.status}")
        await api.close()

    asyncio.run(main())
