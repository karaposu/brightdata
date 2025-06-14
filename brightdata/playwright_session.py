# brightdata/playwright_session.py
"""
A *singleton* wrapper that keeps exactly **one** Chromium instance
connected to Bright Data’s Browser-API (CDP) for the entire Python
process.

• `PlaywrightSession.get(**cfg)`   → returns the singleton (creates it on
  first call, re-uses it afterwards).  
• `.new_page( … )`                 → opens a **fresh incognito context**
  and returns an *open* Playwright `Page`.  
• `.close()`                       → gracefully shuts everything down.
"""

from __future__ import annotations

import asyncio
from typing import Optional, Tuple

from playwright.async_api import (
    async_playwright,
    Browser,
    Page,
)

# ────────────────────────────────────────────────────────────────────────────
class PlaywrightSession:
    """
    One-per-process connection to Bright Data’s CDP host.

    Parameters accepted by `get()` (and forwarded to `__init__`):

        username : str
        password : str
        host     : str   (default "brd.superproxy.io")
        port     : int   (default 9222)
    """

    _instance: "PlaywrightSession | None" = None

    # ─────────────────────────────────────────────────────────────── class api
    @classmethod
    async def get(
        cls,
        *,
        username: str,
        password: str,
        host: str,
        port: int,
    ) -> "PlaywrightSession":
        """Lazily create (or re-use) the process-wide singleton."""
        if cls._instance is None:
            cls._instance = PlaywrightSession(
                username=username,
                password=password,
                host=host,
                port=port,
            )
            await cls._instance._connect()
        return cls._instance

    # ─────────────────────────────────────────────────────────────── lifecycle
    def __init__(self, *, username: str, password: str, host: str, port: int):
        self.username = username
        self.password = password
        self.host     = host
        self.port     = port

        self._pw_ctx  = None                # type: ignore
        self._browser: Browser | None = None

    async def _connect(self) -> None:
        """Establish the CDP websocket connection once."""
        self._pw_ctx = await async_playwright().start()

        ws_url = (
            f"wss://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/"
        )
        self._browser = await self._pw_ctx.chromium.connect_over_cdp(ws_url)

    async def close(self) -> None:
        """Tear everything down (useful when a BrowserPool is retired)."""
        if self._browser and self._browser.is_connected():
            await self._browser.close()
        if self._pw_ctx is not None:
            await self._pw_ctx.stop()
        self._browser = None
        self._pw_ctx  = None
        PlaywrightSession._instance = None  # allow a fresh singleton later

    # ─────────────────────────────────────────────────────────────── per page
    async def new_page(
        self,
        *,
        headless: bool,
        window_size: Tuple[int, int] | None = None,
    ) -> Page:
        """
        Return a **brand-new** Page (new incognito context).

        `window_size` defaults to 1920×1080 when omitted.
        """
        # Re-connect automatically if the browser got recycled server-side.
        if self._browser is None or not self._browser.is_connected():
            await self._connect()
        if self._browser is None:
            raise RuntimeError("Unable to establish Browser-API connection")

        width, height = window_size or (1920, 1080)

        ctx = await self._browser.new_context(
            viewport={"width": width, "height": height},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            # Bright Data CDP sessions are always headless on their side,
            # but we keep the `headless` flag for completeness / future use.
            accept_downloads=False,
        )
        return await ctx.new_page()
