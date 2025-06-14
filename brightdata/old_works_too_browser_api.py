
# brightdata.browser_api  ·  Playwright edition
# ---------------------------------------------

# Async, resource-friendly wrapper around Bright Data’s *Browser API* proxy.
# All public helpers return **ScrapeResult** objects so the higher-level
# brightdata.auto helpers keep working unchanged.


# to run python -m brightdata.browser_api

from __future__ import annotations
import os, pathlib, asyncio, time
from datetime import datetime
from typing import Any, Optional, List
import tldextract

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, Page, Error as PWError
from playwright.async_api import TimeoutError as PWTimeoutError
from brightdata.playwright_session import PlaywrightSession  as _PlaywrightSession


from brightdata.models import ScrapeResult


# ────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ────────────────────────────────────────────────────────────────────────────
# browser_api.py
def _make_result(
    url: str,
    *,
    success: bool,
    status: str,
    data: Any = None,
    error: str | None = None,
    request_sent_at: datetime | None = None,      # ← NEW
    data_received_at: datetime | None = None,     # ← NEW
) -> ScrapeResult:
    ext = tldextract.extract(url)
    return ScrapeResult(
        success=success,
        url=url,
        status=status,
        data=data,
        error=error,
        snapshot_id=None,
        cost=None,
        fallback_used=True,
        root_domain=ext.domain or None,
        request_sent_at=request_sent_at,          # ← pass through
        data_received_at=data_received_at,        # ← pass through
        event_loop_id=id(asyncio.get_running_loop()),
    )





    # async def new_page(self, headless: bool, window_size: tuple[int, int]) -> Page:
    #     """
    #     Create a fresh context + tab.
    #     Re-connect transparently if the previous Chrome session died.
    #     """
    #     if self._browser is None or self._browser.is_closed():
    #         # try once more – Bright Data may have recycled the session
    #         await self._connect()

    #     if self._browser is None:                # still no luck → raise
    #         raise RuntimeError("Unable to connect to Bright Data Browser-API")

    #     ctx = await self._browser.new_context(
    #         viewport={"width": window_size[0], "height": window_size[1]},
    #         user_agent=(
    #             "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    #             "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    #         ),
    #     )
    #     return await ctx.new_page()



class BrowserAPI:
    DEFAULT_HOST = "brd.superproxy.io"
    DEFAULT_PORT = 9222   # CDP websocket port for Bright Data’s Browser API

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        *,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        window_size: tuple[int, int] = (1920, 1080),
        load_state: str = "domcontentloaded",   #  ← NEW  ("load", "domcontentloaded", "networkidle", "commit")
        main_selector: str = "#main"
    ):
        load_dotenv()
        self.username = username or os.getenv("BRIGHTDATA_BROWSERAPI_USERNAME")
        self.password = password or os.getenv("BRIGHTDATA_BROWSERAPI_PASSWORD")

        self._main_selector = main_selector

        self._default_load_state = load_state   #  ← keep for later

        if not (self.username and self.password):
            raise ValueError(
                "Set BRIGHTDATA_BROWSERAPI_USERNAME and "
                "BRIGHTDATA_BROWSERAPI_PASSWORD to use BrowserAPI."
            )

        self.host = host
        self.port = port
        self.window_size = window_size

        # Playwright session will be created lazily on first use
        self._session: _PlaywrightSession | None = None


    async def _launch(self) -> None:
        """
        Internal: start Playwright (if not running yet) and create
        a single browser tab we reuse for all requests.
        """
        if hasattr(self, "_browser"):
            return                          # already running
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True, proxy={
                "server": f"http://{self.username}:{self.password}"
                           f"@{self.DEFAULT_HOST}:{self.DEFAULT_PORT}"
            }
        )
        self._page = await self._browser.new_page()

    async def close(self) -> None:
        """
        Public coroutine – gracefully shut Playwright down.
        """
        if hasattr(self, "_browser"):
            await self._browser.close()
            await self._playwright.stop()
            del self._browser, self._playwright, self._page
    
    # ────────────────────────────────────────────────────────────
    # Low-level async helpers
    # ────────────────────────────────────────────────────────────
    async def _open_page(self) -> Page:
        if self._session is None:
            self._session = await _PlaywrightSession.get(
                username=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
            )
        return await self._session.new_page(
            headless=True,
            window_size=self.window_size,


        )
    

    async def _perform_navigation(
        self,
        url: str,
        *,
        load_state: str | None,
    ) -> tuple[Page, datetime]:
        """
        Return an *open* Playwright Page that has already navigated to
        *url*, plus the timestamp right before the request was sent.
        """
        page       = await self._open_page()
        sent_at    = datetime.utcnow()
        wait_until = load_state or self._default_load_state
        await page.goto(url, timeout=60_000, wait_until=wait_until)
        return page, sent_at
        

    async def _navigate_and_collect(
        self,
        url: str,
        wait_for_main: bool | int,
        *,
        load_state: str | None,
    ) -> tuple[str | None, datetime, datetime, str | None]:
        """
        Returns (html, sent_at, recv_at, warning_msg)

        *warning_msg* is **None** on perfect success, or a human-readable note
        when we timed-out waiting for `#main` but still got partial HTML.
        """
        # ── step 1: navigate ─────────────────────────────────────────────
        page, sent_at = await self._perform_navigation(url, load_state=load_state)

        try:
            # ── step 2: optional '#main' wait ────────────────────────────
            # if wait_for_main:
            #     timeout_ms = wait_for_main * 1_000 if isinstance(wait_for_main, int) else 30_000
            #     await page.wait_for_selector("#main", timeout=timeout_ms)

            if wait_for_main:
                selector = self._main_selector or "body"   # fallback to <body> if empty
                timeout_ms = (wait_for_main * 1000
                            if isinstance(wait_for_main, int) else 30_000)
                await page.wait_for_selector(selector, timeout=timeout_ms)

            html    = await page.content()
            recv_at = datetime.utcnow()
            return html, sent_at, recv_at, None                      # perfect

        except PWTimeoutError as e:
            html    = await page.content()          # salvage partial markup
            recv_at = datetime.utcnow()
            note    = f"wait_for_selector timeout ({e}). Returned partial HTML."
            return html, sent_at, recv_at, note                      # soft fail

        finally:
            await page.context.close()

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

            return _make_result(
                url,
                success=True,
                status="ready",
                data=html,
                error=warn,                 # None on happy path, message on soft fail
                request_sent_at=sent_at,
                data_received_at=recv_at,
            )

        # ───── Hard Playwright errors (navigation, DNS, etc.) ─────────────
        except PWError as e:
            msg = getattr(e, "message", "") or str(e) or repr(e)
            return _make_result(
                url,
                success=False,
                status="error",
                error=msg,
                request_sent_at=sent_at if "sent_at" in locals() else None,
                data_received_at=datetime.utcnow(),
            )

        # ───── Anything else unexpected ───────────────────────────────────
        except Exception as e:
            msg = (str(e) or repr(e)).strip()
            return _make_result(
                url,
                success=False,
                status="error",
                error=msg,
                request_sent_at=sent_at if "sent_at" in locals() else None,
                data_received_at=datetime.utcnow(),
            )

    

    async def get_page_source_async(
        self,
        url: str,
        *,
        load_state: str | None = None,
    ) -> ScrapeResult:
        """
        Fetch raw HTML immediately after the chosen *load_state* milestone.
        """
        return await self._goto(url, wait_for_main=False, load_state=load_state)

    # async def get_page_source_async(self, url: str) -> ScrapeResult:
    #     return await self._goto(url, wait_for_main=False)
    
    async def get_page_source_with_a_delay_async(
        self,
        url: str,
        wait_time_in_seconds: int = 25,
        *,
        load_state: str | None = None,
    ) -> ScrapeResult:
        """
        Fetch hydrated HTML after waiting for <div id="main"> to appear
        (up to *wait_time_in_seconds*).  Uses *load_state* just like the
        plain helper above.
        """
        return await self._goto(
            url,
            wait_for_main=wait_time_in_seconds,
            load_state=load_state,
        )
    
    async def capture_screenshot_async(
        self,
        url: str,
        path: str,
        wait_time_in_seconds: int | bool = 20,   # True → infinite wait
    ) -> ScrapeResult:
        res = await self._goto(url, wait_for_main=wait_time_in_seconds)
        if not res.success:
            return res

        try:
            page = await self._open_page()
            await page.goto(url, timeout=60_000)
            if wait_time_in_seconds:
                timeout_ms = (
                    wait_time_in_seconds * 1_000
                    if isinstance(wait_time_in_seconds, int) else 30_000
                )
                await page.wait_for_selector("#main", timeout=timeout_ms)
            pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=path, full_page=True)
            await page.context.close()
            return _make_result(url, success=True, status="ready", data=path)
        except Exception as e:
            return _make_result(url, success=False, status="error", error=str(e))

    # ────────────────────────────────────────────────────────────
    #   *Synchronous* wrappers – keep existing API surface intact
    #   (They just run the async version via asyncio.run)
    # ────────────────────────────────────────────────────────────
    def get_page_source(self, url: str) -> ScrapeResult:
        return asyncio.run(self.get_page_source_async(url))

    def get_page_source_with_a_delay(
        self, url: str, wait_time_in_seconds: int = 20
    ) -> ScrapeResult:
        return asyncio.run(
            self.get_page_source_with_a_delay_async(url, wait_time_in_seconds)
        )

    def capture_screenshot(
        self, url: str, path: str, wait_time_in_seconds: int | bool = 20
    ) -> ScrapeResult:
        return asyncio.run(
            self.capture_screenshot_async(url, path, wait_time_in_seconds)
        )


# ────────────────────────────────────────────────────────────────────────────
# Quick manual smoke-test ( `python -m brightdata.browser_api` )
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":          # pragma: no cover
    import asyncio, time, pprint

    TARGET = "https://openai.com"   # or "https://budgety.ai"

    async def _demo() -> None:
        api = BrowserAPI()          # uses env-vars for credentials
        t0 = time.time()

        # full-page HTML, waiting up to 25 s for <div id="main">
        res = await api.get_page_source_with_a_delay_async(
            TARGET,
            wait_time_in_seconds=25,
            load_state="domcontentloaded",   # change if you like
        )

        t1 = time.time()
       
        # ---- pretty print (similar to Selenium example) --------------
        print("success:",      res.success)
        print("root_domain:",  res.root_domain)
        print("status:",       res.status)
        print("cost:",         res.cost)
        print("data:",         (res.data or "")[:400])        # first 400 chars
        print("error:",        res.error)
        print("time elapsed:", round(t1 - t0, 3), "seconds")

        # close Playwright cleanly so the script exits promptly
        await api.close()
    
    asyncio.run(_demo())