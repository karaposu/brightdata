# here is brightdata.browserapi_engine.py

#!/usr/bin/env python3

# to run  python browserapi_engine.py

"""
isolated_playwright_session.py

A per-instance PlaywrightSession: each .create() makes a fresh CDP connection,
and .close() tears it down.  No global singleton.
"""

import os
import asyncio
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, Page
from typing import Optional, Tuple, List
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PWTimeoutError

load_dotenv()
logger = logging.getLogger(__name__)


# BrowserAPI_IsolatedPlaywrightSession
DEFAULT_BLOCK_PATTERNS: List[str] = [
    "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,otf,css,mp4,webm}"
]

# wait up to this many ms for hydration selectors
DEFAULT_HYDRATE_WAIT_MS: int = 30_000

# try these selectors in order for “page is actually usable”
DEFAULT_HYDRATION_SELECTORS: List[str] = [
    "#main",
    "div#__next",
    "div[data-reactroot]",
    "body > *:not(script)",
]


class BrowserapiEngine:
    """
    Each instance holds its own playwright and browser.
    """

    # default block‐patterns (images, fonts, media, etc.)


    def __init__(self, pw_ctx, browser: Browser):
        self._pw_ctx = pw_ctx
        self._browser = browser

    @classmethod
    async def create(
        cls,
        username: str | None = None,
        password: str | None = None,
        host: str = os.getenv("BROWSERAPI_HOST", "brd.superproxy.io"),
        port: int = int(os.getenv("BROWSERAPI_PORT", 9222)),
        retry: int = 1                         
    
    ) -> "IsolatedPlaywrightSession":
        """
        Open a new playwright context + CDP connection.
        """

        DEFAULT_CONNECT_TIMEOUT_MS = 30_000      

        username = username or os.getenv("BRIGHTDATA_BROWSERAPI_USERNAME")
        password = password or os.getenv("BRIGHTDATA_BROWSERAPI_PASSWORD")
        if not (username and password):
            raise RuntimeError("Missing Browser-API credentials")

        pw_ctx = await async_playwright().start()
        ws_url = f"wss://{username}:{password}@{host}:{port}/"


        attempt = 0
        while True:
            try:
                browser = await pw_ctx.chromium.connect_over_cdp(
                    ws_url
                )
                break                                # success
            except PWTimeoutError as err:
                attempt += 1                         # count this failure first
                if attempt > retry:                  # retries exhausted
                    raise ConnectionError(
                        f"CDP handshake timed out after "
                        f"{DEFAULT_CONNECT_TIMEOUT_MS/1000:.0f}s "
                        f"(attempt {attempt}/{retry+1})"
                    ) from err
                    # logger.error(
                    # "CDP handshake failed (browserapi_engine.py line 98), no error is raised",
                    # attempt, retry, err
                    # )
                
                logger.warning(
                    "CDP handshake retry %d/%d after timeout (%s)",
                    attempt, retry, err
                )
                await asyncio.sleep(5.0)             # small back-off

        return cls(pw_ctx, browser)





    async def new_page(
        self,
        headless: bool = True,
        window_size: tuple[int, int] = (1920, 1080),
    ) -> Page:
        """
        Open a fresh incognito context + tab.
        """
        width, height = window_size
        ctx = await self._browser.new_context(
            viewport={"width": width, "height": height},
            accept_downloads=False,
        )
        return await ctx.new_page()

    async def close(self) -> None:
        """
        Tear down both the browser and the playwright driver.
        """
        if self._browser and self._browser.is_connected():
            await self._browser.close()
        if self._pw_ctx:
            await self._pw_ctx.stop()
        self._browser = None
        self._pw_ctx = None

    @classmethod
    async def fetch(
        cls,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout: int = 75_000,
        headless: bool = True,
        window_size: Tuple[int, int] = (1920, 1080),
        # block_patterns: Optional[List[str]] = DEFAULT_BLOCK_PATTERNS,
        block_patterns: Optional[List[str]] = None,
        enable_wait_for_selector: bool = False,
        wait_for_selector_timeout: int = 15_000,   # ms
    ) -> Tuple[str, float]:
        """
        Convenience helper: spin up a session, optionally block resources,
        grab the HTML, and tear down.

        Parameters
        ----------
        url : str
        wait_until : playwright wait_until option
        timeout : navigation timeout in ms
        headless : whether to run headless (always true on the remote side)
        window_size : viewport size
        block_patterns : list of glob patterns to abort (e.g. images/fonts)

        Returns
        -------
        html : str
          The full page HTML.
        elapsed : float
          Seconds elapsed during the navigation.
        """
        session = await cls.create()
        try:
            page = await session.new_page(headless=headless, window_size=window_size)

            # set up resource blocking
            patterns = block_patterns if block_patterns is not None else DEFAULT_BLOCK_PATTERNS
            if patterns:
                async def _block(route):
                    await route.abort()
                for pat in patterns:
                    await page.route(pat, _block)

            # navigate & measure
            t0 = time.time()
            await page.goto(url, timeout=timeout, wait_until=wait_until)

            # 2) optional hydration‐selector wait
            if enable_wait_for_selector:
                sel = ":is(" + ",".join(DEFAULT_HYDRATION_SELECTORS) + ")"
                try:
                    await page.wait_for_selector(sel, timeout=wait_for_selector_timeout)
                except PWTimeoutError:
                    logger.debug(
                        "⚠ none of %r appeared within %dms on %s",
                        DEFAULT_HYDRATION_SELECTORS, wait_for_selector_timeout, url
                    )


            elapsed = time.time() - t0

            # capture HTML
            html = await page.content()
            await page.context.close()
            return html, elapsed

        finally:
            await session.close()

    # @classmethod
    # async def fetch(
    #     cls,
    #     url: str,
    #     *,
    #     wait_until: str = "domcontentloaded",
    #     timeout: int = 60_000,
    #     headless: bool = True,
    #     window_size: tuple[int, int] = (1920, 1080),
    # ) -> tuple[str, float]:
    #     """
    #     Convenience helper: in one shot, spin up a session, grab the HTML, and tear down.

    #     Returns
    #     -------
    #     html : str
    #       The full page HTML.
    #     elapsed : float
    #       Seconds elapsed during the navigation.
    #     """
    #     session = await cls.create()
    #     try:
    #         page = await session.new_page(headless=headless, window_size=window_size)
    #         t0 = time.time()
    #         await page.goto(url, timeout=timeout, wait_until=wait_until)
    #         elapsed = time.time() - t0
    #         html = await page.content()
    #         await page.context.close()
    #         return html, elapsed
    #     finally:
    #         await session.close()


if __name__ == "__main__":  # pragma: no cover
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

    async def sequential():
        print("\n=== SEQUENTIAL FETCH ===")
        for url in URLS:
            print(f"\n→ fetching {url}")
            html, took = await IsolatedPlaywrightSession.fetch(url )
            print(f"   ↳ got {len(html)} chars in {took:.2f}s")

    async def parallel():
        print("\n=== PARALLEL FETCH ===")
        tasks = [IsolatedPlaywrightSession.fetch(url ) for url in URLS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for url, result in zip(URLS, results):
            if isinstance(result, Exception):
                print(f"✗ {url!r}: error {result}")
            else:
                html, took = result
                print(f"✓ {url!r}: {len(html)} chars in {took:.2f}s")

    async def main():
        await sequential()
        await parallel()

    asyncio.run(main())