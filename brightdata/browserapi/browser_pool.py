# brightdata/browser_pool.py
# -------------------------
# A lightweight async pool that re-uses a *small* set of BrowserAPI
# (Playwright-based) connections instead of opening a new Chrome
# session for every URL.  Meant for fallback jobs inside
# brightdata.auto.scrape_urls_async.

from __future__ import annotations
import asyncio
from typing import List

from .browser_api import BrowserAPI


class BrowserPool:
    """
    Async, round-robin pool.

    Parameters
    ----------
    size : int, default 8
        Maximum number of concurrent BrowserAPI objects (and therefore
        remote Chrome instances on Bright Data) that will ever exist.
    browser_kwargs : dict, optional
        Extra keyword arguments forwarded to `BrowserAPI(**kwargs)`.
        Example: ``BrowserPool(size=6, browser_kwargs=dict(load_state="networkidle"))``
    """

    def __init__(self, *, size: int = 8, browser_kwargs: dict | None = None) -> None:
        if size < 1:
            raise ValueError("size must be ≥ 1")
        self._size = size
        self._browser_kwargs = browser_kwargs or {}

        self._apis: List[BrowserAPI] = []
        self._lock = asyncio.Lock()        # protects _apis list
        self._idx = 0                      # for round-robin selection

    # ------------------------------------------------------------------
    # internal helper – lazily create BrowserAPI objects until _size
    # ------------------------------------------------------------------
    async def _ensure_pool(self) -> None:
        async with self._lock:
            while len(self._apis) < self._size:
                self._apis.append(BrowserAPI(**self._browser_kwargs))

    # ------------------------------------------------------------------
    # public: get a BrowserAPI handle (re-uses existing ones)
    # ------------------------------------------------------------------
    async def acquire(self) -> BrowserAPI:
        await self._ensure_pool()
        api = self._apis[self._idx % self._size]
        self._idx += 1
        return api

    # ------------------------------------------------------------------
    # clean-up: close every Playwright connection gracefully
    # ------------------------------------------------------------------
    async def close(self) -> None:
        if not self._apis:
            return
        await asyncio.gather(*(api.close() for api in self._apis))
        self._apis.clear()

    # ------------------------------------------------------------------
    # async context-manager convenience
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "BrowserPool":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        await self.close()
        return False          # propagate any exception

