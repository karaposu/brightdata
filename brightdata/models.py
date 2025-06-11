# brightdata/models.py

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ScrapeResult:
    success: bool                  # True if the operation succeeded
    url: str                       # The input URL associated with this scrape result
    status: str                    # "ready" | "error" | "timeout" | "in_progress" | …
    data: Optional[Any] = None     # The scraped rows (when status == "ready")
    error: Optional[str] = None    # Error code or message, if any
    snapshot_id: Optional[str] = None  # Bright Data snapshot ID for this job
    cost: Optional[float] = None       # Cost charged by Bright Data for this job
    fallback_used: bool = False        # True if a fallback (e.g., BrowserAPI) was used
    root_domain: Optional[str] = None  # Second‐level domain of the URL, for registry lookups
    # elapsed_time: Optional[float] = None   # seconds from trigger to result


