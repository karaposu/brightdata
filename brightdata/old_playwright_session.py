"""
playwright_session.py
~~~~~~~~~~~~~~~~~~~~~

One-per-process singleton that manages a single Bright-Data *Browser-API*
web-socket and hands out fresh Playwright pages on demand.

*   Auto-reconnects if the CDP socket is dropped.
*   Recycles the whole browser after `_NAV_LIMIT` navigations to avoid
    Bright-Data’s hard cap (30 concurrent pages) and some lingering-context
    edge-cases.
"""

from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page


class PlaywrightSession:
    """Singleton wrapper around Bright-Data’s Browser-API (CDP-over-WS)."""

    _instance: Optional["PlaywrightSession"] = None       # singleton
    _NAV_LIMIT = 28                                       # keep a safety margin
    

    # ────────────────────────────────────────────────
    # Construction helpers
    # ────────────────────────────────────────────────
    def __init__(self, *, username: str, password: str,
                 host: str = "brd.superproxy.io", port: int = 9222) -> None:
        self.username   = username
        self.password   = password
        self.host       = host
        self.port       = port

        self._pw_ctx    = None            # playwright context (async_playwright())
        self._browser: Browser | None = None
        self._nav_count = 0               # “how many pages have we opened?”

    @classmethod
    async def get(cls, **cfg) -> "PlaywrightSession":
        """Return the *one* session object – create it lazily on first call."""
        if cls._instance is None:
            cls._instance = PlaywrightSession(**cfg)
            await cls._instance._connect()
        return cls._instance

    # ────────────────────────────────────────────────
    # Internal – (re)connect to Bright-Data’s CDP hub
    # ────────────────────────────────────────────────
    async def _connect(self) -> None:
        if self._pw_ctx is None:
            self._pw_ctx = await async_playwright().start()

        ws_url = (
            f"wss://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/"
        )
        # Close any dangling browser first (paranoia)
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                pass

        self._browser = await self._pw_ctx.chromium.connect_over_cdp(ws_url)
        self._nav_count = 0                     # reset counter on fresh connect

    # ────────────────────────────────────────────────
    # Public – hand out a *new* Page each call
    # ────────────────────────────────────────────────
    async def new_page(self, *, headless: bool = True,
                       window_size: tuple[int, int] = (1920, 1080)) -> Page:
        """
        Return a freshly-created Page (in its own incognito context).

        * Transparently re-connect if the socket died.
        * Recycle the entire browser when `_NAV_LIMIT` is reached.
        """
        # 1) reconnect if the socket is closed or we hit the per-browser limit
        if (self._browser is None or not self._browser.is_connected()
                or self._nav_count >= self._NAV_LIMIT):
            await self._connect()

        if self._browser is None:             # still no luck → escalate
            raise RuntimeError("Unable to connect to Bright-Data Browser-API")

        # 2) create a fresh incognito context + page
        ctx = await self._browser.new_context(
            viewport={"width": window_size[0], "height": window_size[1]},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        self._nav_count += 1                  # count this navigation
        return await ctx.new_page()

    # ────────────────────────────────────────────────
    # Optional – graceful shutdown (rarely needed)
    # ────────────────────────────────────────────────
    async def close(self) -> None:
        """Close browser + Playwright to let the event-loop exit quickly."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._pw_ctx:
            await self._pw_ctx.stop()
            self._pw_ctx = None



# """
# Thread-/task-safe singleton wrapper around Bright Data’s Browser-API
# Chrome session.  The class is intentionally **stand-alone** so it can be
# imported from multiple modules (e.g. `browser_api.py`, your own helpers,
# tests) without ever creating more than one underlying CDP connection.

# Usage
# -----
# from brightdata.playwright_session import PlaywrightSession

# session = await PlaywrightSession.get(
#     username=BD_USER,
#     password=BD_PASS,
#     host="brd.superproxy.io",
#     port=9222,
# )
# page = await session.new_page(window_size=(1920, 1080))
# """
# from __future__ import annotations

# import asyncio
# from typing import Tuple, Optional

# from playwright.async_api import async_playwright, Browser, Page


# class PlaywrightSession:
#     # ------------------------------------------------------------------ #
#     # class-level singletons & locks
#     # ------------------------------------------------------------------ #
#     _instance: "PlaywrightSession | None" = None          # the one-and-only
#     _instance_lock = asyncio.Lock()                       # guards singleton
#     _tab_lock = asyncio.Lock()                            # guards new_page()

#     # ------------------------------------------------------------------ #
#     # constructor (called only from `get`)
#     # ------------------------------------------------------------------ #
#     def __init__(self, username: str, password: str,
#                  host: str, port: int):
#         self.username = username
#         self.password = password
#         self.host = host
#         self.port = port

#         self._pw_ctx = None                # type: ignore
#         self._browser: Optional[Browser] = None

#     # ------------------------------------------------------------------ #
#     # public: obtain / create the singleton
#     # ------------------------------------------------------------------ #
#     @classmethod
#     async def get(cls, **cfg) -> "PlaywrightSession":
#         """
#         Awaitable singleton accessor.  Ensures that *at most* one underlying
#         CDP connection is created per Python process.
#         """
#         async with cls._instance_lock:
#             if cls._instance is None:
#                 cls._instance = PlaywrightSession(**cfg)
#                 await cls._instance._connect()
#             return cls._instance

#     # ------------------------------------------------------------------ #
#     # private: (re)-connect to Bright Data’s Browser-API
#     # ------------------------------------------------------------------ #
#     async def _connect(self) -> None:
#         self._pw_ctx = await async_playwright().start()
#         ws_url = (
#             f"wss://{self.username}:{self.password}"
#             f"@{self.host}:{self.port}/"
#         )
#         self._browser = await self._pw_ctx.chromium.connect_over_cdp(ws_url)

#     # ------------------------------------------------------------------ #
#     # public: create a brand-new tab (context + page) safely
#     # ------------------------------------------------------------------ #
#     async def new_page(
#         self,
#         *,
#         headless: bool = True,              # kept for API compatibility
#         window_size: Tuple[int, int] = (1920, 1080),
#     ) -> Page:
#         """
#         Returns a *fresh* Playwright Page.  All calls are serialised so that
#         we never hammer the CDP session with concurrent `new_context()` calls.
#         """
#         async with self._tab_lock:
#             if self._browser is None or not self._browser.is_connected():
#                 await self._connect()

#             if self._browser is None:                     # still no luck
#                 raise RuntimeError("Unable to connect to Bright Data Browser-API")

#             ctx = await self._browser.new_context(
#                 viewport={"width": window_size[0], "height": window_size[1]},
#                 user_agent=(
#                     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
#                     "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
#                 ),
#             )
#             return await ctx.new_page()
