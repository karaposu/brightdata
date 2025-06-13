# brightdata/models.py

from dataclasses import dataclass
from dataclasses import field
from typing import Any, Optional
from datetime import datetime
from typing import Any, Optional, List

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
    
    # -- timings (all ISO-8601 strings or datetime objects) --
    request_sent_at:     Optional[datetime] = None   # just before POST /trigger
    snapshot_id_received_at: Optional[datetime] = None   # when POST returns
    snapshot_polled_at:  List[datetime] = field(default_factory=list)  # every /progress check
    data_received_at:    Optional[datetime] = None   # when /snapshot?format=json succeeded
    event_loop_id: Optional[int] = None                      # id(asyncio.get_running_loop())


