#here is brightdata/browser_api.py

# to run python -m brightdata.browser_api
#!/usr/bin/env python3
"""
brightdata/browser_api.py

A high-level façade over BrowserapiEngine with three concurrency strategies:
  • noop      → spin up & tear down a session per URL
  • semaphore → same, but limit # concurrent sessions
  • pool      → keep a pool of long-lived sessions and reuse them

All engine-level options (resource blocking, hydration‐selector waits) are
exposed here and automatically forwarded down to BrowserapiEngine.fetch().
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Literal, Optional, List, Tuple

# suppress filelock/tldextract noise
logging.getLogger("filelock").setLevel(logging.WARNING)
logging.getLogger("tldextract").setLevel(logging.WARNING)

import tldextract
from .browserapi_engine import BrowserapiEngine
from ..models import ScrapeResult

logger = logging.getLogger(__name__)


class BrowserAPI:
    COST_PER_GIB = 8.40   # USD per GiB transferred
    GIB = 1024**3

    def __init__(
        self,
        *,
        strategy: Literal["noop", "semaphore", "pool"] = "noop",
        pool_size: int = 5,
        max_concurrent: Optional[int] = None,
        # engine-level defaults:
        block_patterns: Optional[List[str]] = None,
        enable_wait_for_selector: bool = False,
        wait_for_selector_timeout: int = 15_000,
    ):
        self.strategy = strategy
        self.pool_size = pool_size
        self._max_concurrent = max_concurrent or pool_size

        if strategy == "semaphore":
            self._sem = asyncio.Semaphore(self._max_concurrent)

        # for pool strategy
        self._sessions: List[BrowserapiEngine] = []
        self._rr_idx = 0

        # engine defaults
        self._block_patterns = block_patterns
        self._enable_wait_for_selector = enable_wait_for_selector
        self._wait_for_selector_timeout = wait_for_selector_timeout

        # usage tracking
        self.total_bytes = 0
        self.total_cost = 0.0

    def _extract_root(self, url: str) -> Optional[str]:
        e = tldextract.extract(url)
        return e.domain or None

    def calculate_cost(self, raw_html: str) -> float:
        byte_count = len(raw_html.encode("utf-8"))
        return byte_count / self.GIB * self.COST_PER_GIB

    async def _fetch_isolated(
        self,
        url: str,
        *,
        wait_until: str,
        timeout: int,
        headless: bool,
        window_size: Tuple[int, int],
    ) -> Tuple[str, float]:
        return await BrowserapiEngine.fetch(
            url=url,
            wait_until=wait_until,
            timeout=timeout,
            headless=headless,
            window_size=window_size,
            block_patterns=self._block_patterns,
            enable_wait_for_selector=self._enable_wait_for_selector,
            wait_for_selector_timeout=self._wait_for_selector_timeout,
        )

    async def _ensure_pool(self) -> None:
        while len(self._sessions) < self.pool_size:
            try:
                sess = await BrowserapiEngine.create()     # may raise
            except ConnectionError as e:
                logger.error("Browser-API pool(might be due to cdp connection failed): %s", e)
                break                     # leave the session list as-is (maybe empty)
            else:
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

    async def fetch_async(
        self,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout: int = 60_000,
        headless: bool = True,
        window_size: Tuple[int, int] = (1920, 1080),
    ) -> ScrapeResult:
        
        request_sent_at = datetime.utcnow()
        try:
            html, elapsed = await self._do_strategy_fetch(
                url=url,
                wait_until=wait_until,
                timeout=timeout,
                headless=headless,
                window_size=window_size,
            )

            data_received_at = datetime.utcnow()

            cost = self.calculate_cost(html)
            self.total_bytes += len(html.encode("utf-8"))
            self.total_cost += cost
            
            return ScrapeResult(
                success=True,
                url=url,
                status="ready",
                data=html,
                error=None,
                root_domain=self._extract_root(url),
                cost=cost,
                request_sent_at=request_sent_at,
                data_received_at=data_received_at,
                event_loop_id=id(asyncio.get_running_loop()),
                browser_warmed_at=None,
                html_char_size= len(html),
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
                request_sent_at=request_sent_at,
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
        return asyncio.run(
            self.fetch_async(
                url=url,
                wait_until=wait_until,
                timeout=timeout,
                headless=headless,
                window_size=window_size,
            )
        )

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

        # No-pool
        api = BrowserAPI(strategy="noop",
                         enable_wait_for_selector=True,
                         block_patterns=["**/*.png","**/*.css"])
        for u in urls:
            res = await api.fetch_async(u)
            print(
                f"noop: {u:>25} → {res.html_char_size} chars, "
                f"${res.cost:.5f}, status={res.status}"
            )
        await api.close()

        # Semaphore
        api = BrowserAPI(strategy="semaphore", max_concurrent=3)
        tasks = [api.fetch_async(u) for u in urls]
        for res, u in zip(await asyncio.gather(*tasks), urls):
            print(
                f"sema: {u:>25} → {res.html_char_size} chars, "
                f"${res.cost:.5f}, status={res.status}"
            )
        await api.close()

        # Pool
        api = BrowserAPI(strategy="pool", pool_size=2)
        tasks = [api.fetch_async(u) for u in urls]
        for res, u in zip(await asyncio.gather(*tasks), urls):
            print(
                f"pool: {u:>25} → {res.html_char_size} chars, "
                f"${res.cost:.5f}, status={res.status}"
            )
        await api.close()

    asyncio.run(main())
