# to run python -m brightdata.browser_api

"""
brightdata.browser_api  ·  Playwright edition
---------------------------------------------

Async, resource-friendly wrapper around Bright Data’s *Browser API* (CDP).
All public helpers return **ScrapeResult** so the higher-level
`brightdata.auto` helpers work unchanged.

Run a quick smoke-test with:
    
    python -m brightdata.browser_api
"""
from __future__ import annotations

import asyncio
import os
import pathlib
import time
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from playwright.async_api import (
    async_playwright,
    Browser,
    Error as PWError,
    Page,
    TimeoutError as PWTimeoutError,
)

# ── brightdata imports ──────────────────────────────────────────────────────
from brightdata.models import ScrapeResult
from brightdata.utils import _make_result_browserapi as _mk
from brightdata.playwright_session import PlaywrightSession  # our singleton

# ── all configurable defaults in one place ──────────────────────────────────
DEFAULT_HOST         = "brd.superproxy.io"
DEFAULT_CDP_PORT     = 9222
DEFAULT_WINDOW_SIZE  = (1920, 1080)
DEFAULT_LOAD_STATE   = "domcontentloaded"  # Playwright wait_until milestone
NAVIGATION_TIMEOUT   = 60_000              # 60 s budget for page.goto
MAIN_SELECTOR        = "#main"
MAIN_SELECTOR_WAIT   = 30_000              # when wait_for_main=True (ms)


# ════════════════════════════════════════════════════════════════════════════
# BrowserAPI
# ════════════════════════════════════════════════════════════════════════════
class BrowserAPI:
    """
    Thin async wrapper around Bright Data’s Browser-API proxy.

    Parameters
    ----------
    username / password : str | None
        Credentials *or* read from env vars
        `BRIGHTDATA_BROWSERAPI_USERNAME` / `..._PASSWORD`.
    load_state : {"load", "domcontentloaded", "networkidle", "commit"}
        Default Playwright life-cycle milestone to wait for on every `goto`.
    window_size : tuple[int, int]
        Per-context viewport.
    host, port : str / int
        Override Bright Data endpoint (rare).
    """

    # ------------------------------------------------------------------ init
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        *,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_CDP_PORT,
        window_size: tuple[int, int] = DEFAULT_WINDOW_SIZE,
        load_state: str = DEFAULT_LOAD_STATE,
        block_resources: bool | list[str] = True,   
    ):
        load_dotenv()  # allow .env credentials

        self.username = username or os.getenv("BRIGHTDATA_BROWSERAPI_USERNAME")
        self.password = password or os.getenv("BRIGHTDATA_BROWSERAPI_PASSWORD")
        if not (self.username and self.password):
            raise ValueError(
                "Set BRIGHTDATA_BROWSERAPI_USERNAME / _PASSWORD env vars "
                "or pass them into BrowserAPI(...)"
            )

        self.host          = host
        self.port          = port
        self.window_size   = window_size
        self._load_state   = load_state  # default, can be overridden per-call

        # One PlaywrightSession (singleton) per *Python process*
        self._session: PlaywrightSession | None = None


        self._block_patterns: list[str] = (
            ["**/*.{png,jpg,jpeg,webp,gif,svg,woff,woff2,ttf,otf}"]
            if block_resources is True
            else (block_resources or [])                # custom patterns
        )

    # ------------------------------------------------------- private helpers
    async def _open_page(self) -> Page:
        """
        Get a *fresh* page: new incognito context + tab behind Bright Data.
        """
        if self._session is None:
            self._session = await PlaywrightSession.get(
                username=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
            )
        return await self._session.new_page(
            headless=True,
            window_size=self.window_size,
        )

    # ---- 1) low-level: navigate ------------------------------------------
    # async def _perform_navigation(
    #     self,
    #     url: str,
    #     *,
    #     load_state: str | None,
    # ) -> tuple[Page, datetime]:
    #     """
    #     Open a page, navigate to *url* and return *(page, request_sent_ts)*.
    #     """
    #     page       = await self._open_page()
    #     sent_at    = datetime.utcnow()
    #     wait_until = load_state or self._load_state
    #     await page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until=wait_until)
    #     return page, sent_at
    
    async def _perform_navigation(self, url: str, *, load_state: str | None):
        page      = await self._open_page()

        # ── 1. OPTIONAL resource blocking ─────────────────────────────
        if self._block_patterns:                       # only if enabled
            async def _block(route):
                await route.abort()
            for pat in self._block_patterns:
                await page.route(pat, _block)

        # ── 2. Navigate as before ─────────────────────────────────────
        sent_at   = datetime.utcnow()
        wait_until = load_state or self._load_state   # ← use the right attr
        await page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until=wait_until)
        return page, sent_at
    

    # ---- 2) mid-level: navigate → (optional) wait → collect --------------
    async def _navigate_and_collect(
        self,
        url: str,
        wait_for_main: bool | int,
        *,
        load_state: str | None,
    ) -> tuple[str | None, datetime | None, datetime, str | None]:
        """
        Do all Playwright I/O, return *(html, sent_at, recv_at, warning)*.
        *warning* is a human-readable note on soft failures (e.g. #main timeout).
        """
        page, sent_at = await self._perform_navigation(url, load_state=load_state)

        try:
            # optional <div id="main"> wait
            if wait_for_main:
                timeout = (
                    wait_for_main * 1_000
                    if isinstance(wait_for_main, int)
                    else MAIN_SELECTOR_WAIT
                )
                await page.wait_for_selector(MAIN_SELECTOR, timeout=timeout)

            html    = await page.content()
            recv_at = datetime.utcnow()
            return html, sent_at, recv_at, None  # success

        except PWTimeoutError as e:
            # soft failure – still have partial HTML
            html    = await page.content()
            recv_at = datetime.utcnow()
            note    = f"wait_for_selector timeout ({e}). Returned partial HTML."
            return html, sent_at, recv_at, note

        finally:
            await page.context.close()

    # ---- 3) public helper: build ScrapeResult ----------------------------
    async def _goto(
        self,
        url: str,
        wait_for_main: bool | int,
        *,
        load_state: str | None = None,
    ) -> ScrapeResult:

        try:
            html, sent_at, recv_at, warn = await self._navigate_and_collect(
                url, wait_for_main, load_state=load_state
            )
            return _mk(  # from brightdata.utils
                url,
                success=html is not None,
                status="ready",
                data=html,
                error=warn,
                request_sent_at=sent_at,
                data_received_at=recv_at,
            )

        # hard Playwright errors
        except PWError as e:
            msg = getattr(e, "message", "") or str(e) or repr(e)
            return _mk(
                url,
                success=False,
                status="error",
                error=msg,
                data_received_at=datetime.utcnow(),
            )

        # everything else
        except Exception as e:
            return _mk(
                url,
                success=False,
                status="error",
                error=str(e) or repr(e),
                data_received_at=datetime.utcnow(),
            )

    # ─────────────────────────────────────────────────────────── public API
    async def get_page_source_async(
        self,
        url: str,
        *,
        load_state: str | None = None,
    ) -> ScrapeResult:
        """Return raw HTML as soon as *load_state* is reached."""
        return await self._goto(url, wait_for_main=False, load_state=load_state)

    async def get_page_source_with_a_delay_async(
        self,
        url: str,
        wait_time_in_seconds: int = 25,
        *,
        load_state: str | None = None,
    ) -> ScrapeResult:
        """Return hydrated HTML, waiting for `#main` (or until timeout)."""
        return await self._goto(
            url, wait_for_main=wait_time_in_seconds, load_state=load_state
        )

    async def capture_screenshot_async(
        self,
        url: str,
        path: str | pathlib.Path,
        wait_for_main: bool | int = False,
        *,
        load_state: str | None = None,
    ) -> ScrapeResult:
        """
        Navigate, optionally wait for `#main`, save screenshot to *path*.
        """
        res = await self._goto(url, wait_for_main, load_state=load_state)
        if not res.success:
            return res  # propagate failure

        # re-open page (simplest) just for the screenshot
        page, _ = await self._perform_navigation(url, load_state=load_state)
        if wait_for_main:
            timeout = (
                wait_for_main * 1_000 if isinstance(wait_for_main, int) else MAIN_SELECTOR_WAIT
            )
            try:
                await page.wait_for_selector(MAIN_SELECTOR, timeout=timeout)
            except PWTimeoutError:
                pass  # ignore, we’ll still capture what we have

        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(path), full_page=True)
        await page.context.close()

        return _mk(url, success=True, status="ready", data=str(path))

    # ── convenience sync wrappers ─────────────────────────────────────────
    def get_page_source(self, url: str, *, load_state: str | None = None) -> ScrapeResult:
        return asyncio.run(self.get_page_source_async(url, load_state=load_state))

    def get_page_source_with_a_delay(
        self,
        url: str,
        wait_time_in_seconds: int = 25,
        *,
        load_state: str | None = None,
    ) -> ScrapeResult:
        return asyncio.run(
            self.get_page_source_with_a_delay_async(
                url, wait_time_in_seconds, load_state=load_state
            )
        )

    def capture_screenshot(
        self,
        url: str,
        path: str | pathlib.Path,
        wait_for_main: bool | int = False,
        *,
        load_state: str | None = None,
    ) -> ScrapeResult:
        return asyncio.run(
            self.capture_screenshot_async(
                url, path, wait_for_main=wait_for_main, load_state=load_state
            )
        )

    # ---------------------------------------------------------------- close
    async def close(self) -> None:
        """
        Close the underlying Playwright session (important when you build
        a *pool* of BrowserAPI instances).
        """
        if self._session is not None:
            await self._session.close()
            self._session = None


# ════════════════════════════════════════════════════════════════════════════
# Manual smoke-test ( python -m brightdata.browser_api )
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":  # pragma: no cover
    import pprint
    
    async def _demo() -> None:
        target = "https://openai.com"  # change freely
        api    = BrowserAPI(load_state="domcontentloaded")

        t0 = time.time()
        res = await api.get_page_source_with_a_delay_async(
            target, wait_time_in_seconds=25
        )
        t1 = time.time()

        pprint.pprint(
            {
                "success": res.success,
                "status":  res.status,
                "root":    res.root_domain,
                "error":   res.error,
                "data_snippet": (res.data or "")[:400],
                "elapsed": round(t1 - t0, 3),
            }
        )

        await api.close()

    asyncio.run(_demo())
