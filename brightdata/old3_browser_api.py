#!/usr/bin/env python3
from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from playwright.async_api import Page, TimeoutError as PWTimeoutError, Error as PWError

from brightdata.models import ScrapeResult
from brightdata.playwright_session import PlaywrightSession

import asyncio

# ─── defaults ────────────────────────────────────────────────────

DEFAULT_HOST            = os.getenv("BROWSERAPI_HOST", "brd.superproxy.io")
DEFAULT_PORT            = int(os.getenv("BROWSERAPI_PORT", 9222))
DEFAULT_WINDOW_SIZE     = (1920, 1080)
DEFAULT_LOAD_STATE      = os.getenv("BROWSERAPI_LOAD_STATE", "domcontentloaded")
DEFAULT_NAV_TIMEOUT_MS  = int(os.getenv("BROWSERAPI_NAV_TIMEOUT_MS", 75_000))
DEFAULT_HYDRATE_WAIT_MS = int(os.getenv("BROWSERAPI_HYDRATE_WAIT_MS", 30_000))

# try a handful of selectors for “main content”
DEFAULT_SELECTORS = [
    "#main",
    "div#__next",
    "div[data-reactroot]",
    "body > *:not(script)",
]

# block common heavy assets by default
DEFAULT_PATTERNS = ["**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,otf}"]

logger = logging.getLogger(__name__)


class BrowserAPI:
    """
    Async, debug-friendly wrapper around Bright Data’s Browser-API (CDP).
    """

    def __init__(
        self,
        *,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        window_size: tuple[int, int] = DEFAULT_WINDOW_SIZE,
        load_state: str = DEFAULT_LOAD_STATE,
        nav_timeout_ms: int = DEFAULT_NAV_TIMEOUT_MS,
        hydrate_wait_ms: int = DEFAULT_HYDRATE_WAIT_MS,
        hydration_selectors: Optional[list[str]] = None,
        block_patterns: Optional[list[str]] = None,
    ):
        load_dotenv()

        self.host = host
        self.port = port
        self.window_size = window_size
        self.load_state = load_state
        self.nav_timeout = nav_timeout_ms
        self.hydrate_wait = hydrate_wait_ms
        self.hydration_selectors = hydration_selectors or DEFAULT_SELECTORS
        self.block_patterns = block_patterns or DEFAULT_PATTERNS

    async def _perform_navigation(
        self,
        url: str,
        *,
        load_state: Optional[str] = None
    ) -> tuple[Page, datetime, datetime]:
        """
        1) open a fresh incognito context + page
        2) record warmed_at
        3) goto(url) → record sent_at
        """
        logger.debug("▶ _perform_navigation start: %r (load_state=%r)", url, load_state)
        session = await PlaywrightSession.get(
            username=os.getenv("BRIGHTDATA_BROWSERAPI_USERNAME"),
            password=os.getenv("BRIGHTDATA_BROWSERAPI_PASSWORD"),
            host=self.host,
            port=self.port,
        )
        page = await session.new_page(
            headless=True,
            window_size=self.window_size,
        )
        warmed_at = datetime.utcnow()

        # optional resource blocking
        if self.block_patterns:
            async def _block(route): await route.abort()
            for pat in self.block_patterns:
                await page.route(pat, _block)

        sent_at = datetime.utcnow()
        wait_until = load_state or self.load_state
        logger.debug("→ goto %r (wait_until=%r)", url, wait_until)
        t0 = time.time()
        await page.goto(url, timeout=self.nav_timeout, wait_until=wait_until)
        elapsed = time.time() - t0
        logger.debug("← goto %r took %.2fs", url, elapsed)

        return page, warmed_at, sent_at

    async def _navigate_and_collect(
        self,
        url: str,
        wait_for_main: int,
        *,
        load_state: Optional[str] = None,
    ) -> tuple[str, datetime, datetime, datetime, Optional[str]]:
        """
        1) perform navigation
        2) optionally wait for hydration selectors
        3) grab html, record recv_at
        4) always close context
        Returns: (html, warmed_at, sent_at, recv_at, warning_msg)
        """
        page, warmed_at, sent_at = await self._perform_navigation(url, load_state=load_state)

        warn: Optional[str] = None
        try:
            if wait_for_main > 0:
                timeout = wait_for_main * 1_000
                logger.debug(
                    "hydration-wait: up to %sms for selectors %r",
                    timeout, self.hydration_selectors
                )
                # match ANY of them in one shot via :is()
                sel = ":is(" + ",".join(self.hydration_selectors) + ")"
                await page.wait_for_selector(sel, timeout=timeout)

            html = await page.content()
            recv_at = datetime.utcnow()
            return html, warmed_at, sent_at, recv_at, warn

        except PWTimeoutError as e:
            html = await page.content()
            recv_at = datetime.utcnow()
            warn = f"hydration timeout; partial HTML"
            logger.warning("⚠ %s", warn)
            return html, warmed_at, sent_at, recv_at, warn

        finally:
            await page.context.close()
            logger.debug("✔ closed context for %r", url)

    async def _goto(
        self,
        url: str,
        wait_for_main: int = 0,
        *,
        load_state: Optional[str] = None,
    ) -> ScrapeResult:
        """
        Top-level helper: navigate+collect, wrap in ScrapeResult.
        """
        logger.debug("▶ _goto start: %r (wait_for_main=%s)", url, wait_for_main)
        try:
            html, warmed_at, sent_at, recv_at, warn = await self._navigate_and_collect(
                url,
                wait_for_main,
                load_state=load_state,
            )
            logger.debug("✔ _goto success: %r", url)
            return ScrapeResult(
                success=html is not None,
                url=url,
                status="ready",
                data=html,
                error=warn,
                root_domain=None,                # tldextract if you need it
                snapshot_id=None,
                cost=None,
                fallback_used=True,
                request_sent_at=sent_at,
                browser_warmed_at=warmed_at,
                data_received_at=recv_at,
                event_loop_id=id(asyncio.get_running_loop()),
            )
        except PWError as e:
            logger.error("✗ _goto PWError: %s", e)
            return ScrapeResult(
                success=False,
                url=url,
                status="error",
                data=None,
                error=str(e),
                root_domain=None,
                snapshot_id=None,
                cost=None,
                fallback_used=True,
                request_sent_at=None,
                browser_warmed_at=None,
                data_received_at=None,
                event_loop_id=id(asyncio.get_running_loop()),
            )

    async def get_page_source_async(
        self,
        url: str,
        *,
        wait_for_main: int = 0,
        load_state: Optional[str] = None,
    ) -> ScrapeResult:
        return await self._goto(url, wait_for_main, load_state=load_state)

    async def get_page_source_with_a_delay_async(
        self,
        url: str,
        wait_time_in_seconds: int = 25,
        *,
        load_state: Optional[str] = None,
    ) -> ScrapeResult:
        return await self._goto(url, wait_time_in_seconds, load_state=load_state)
    
    async def close(self) -> None:
        """
        Tear down the *one* global CDP session.
        """
        logger.debug("▶ BrowserAPI.close()")
        await PlaywrightSession.close_all()
        logger.debug("✔ PlaywrightSession closed")




if __name__ == "__main__":  # pragma: no cover


    logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s  %(message)s",
    )

    import asyncio
    
    async def smoke():
        api = BrowserAPI()
        res1 = await api.get_page_source_async("https://openai.com")
        res2 = await api.get_page_source_with_a_delay_async("https://openai.com", 5)
        await api.close()
        print(res1, res2)

    asyncio.run(smoke())
    