# browser_config.py  (optional helper module)

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Tuple, Optional


def _env(name: str, default: str | int | bool):
    """Helper – fetch env-var, fall back to default and proper-cast."""
    raw = os.getenv(name)
    if raw is None:
        return default
    if isinstance(default, bool):
        return raw.lower() in {"1", "true", "yes"}
    if isinstance(default, int):
        return int(raw)
    return raw


@dataclass(slots=True)
class BrowserConfig:
    # ─── Bright-Data credentials ──────────────────────────────────────
    username: str = field(default_factory=lambda: os.getenv("BRIGHTDATA_BROWSERAPI_USERNAME", ""))
    password: str = field(default_factory=lambda: os.getenv("BRIGHTDATA_BROWSERAPI_PASSWORD", ""))
    
    host: str = _env("BROWSERAPI_HOST", "brd.superproxy.io")
    port: int = _env("BROWSERAPI_PORT", 9222)

    # ─── Playwright / navigation knobs ────────────────────────────────
    headless: bool = _env("BROWSERAPI_HEADLESS", True)
    window_size: Tuple[int, int] = (1920, 1080)
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    load_state: str = _env("BROWSERAPI_LOAD_STATE", "domcontentloaded")   # goto wait_until
    nav_timeout_ms: int = _env("BROWSERAPI_NAV_TIMEOUT_MS", 60_000)

    # ─── “wait for main” feature ──────────────────────────────────────
    main_selector: str = _env("BROWSERAPI_MAIN_SELECTOR", "#main")
    main_timeout_ms: int = _env("BROWSERAPI_MAIN_TIMEOUT_MS", 25_000)
    
    wait_after_main_ms: int = _env("BROWSERAPI_EXTRA_DELAY_MS", 0)   # optional sleep

    # ─── Retries & recycling ──────────────────────────────────────────
    retries: int = _env("BROWSERAPI_RETRIES", 1)                     # 0 = off
    max_pages_per_browser: int = _env("BROWSERAPI_MAX_PAGES", 28)    # PlaywrightSession uses this
