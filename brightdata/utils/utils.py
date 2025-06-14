# brightdata/utils.py  (append near the bottom or any sensible place)

from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Any
import tldextract

from brightdata.models import ScrapeResult


def _make_result_browserapi(                       # ← distinct name
    url: str,
    *,
    success: bool,
    status: str,
    data: Any = None,
    error: str | None = None,
    request_sent_at: datetime | None = None,
    data_received_at: datetime | None = None,
) -> ScrapeResult:
    """
    Internal helper for BrowserAPI – parallels the `_make_result` helper
    that Bright-Data scrapers use, but lives in utils so we avoid code
    duplication and name clashes.
    """
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
        request_sent_at=request_sent_at,
        data_received_at=data_received_at,
        event_loop_id=id(asyncio.get_running_loop()),
    )
