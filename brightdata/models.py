# brightdata/models.py

from dataclasses import dataclass
from dataclasses import field
from typing import Any, Optional
from datetime import datetime
from typing import Dict
from typing import Any, Optional, List
from pathlib import Path            

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
    request_sent_at:     Optional[datetime] = None   # just before POST /trigger
    snapshot_id_received_at: Optional[datetime] = None   # when POST returns
    snapshot_polled_at:  List[datetime] = field(default_factory=list)  # every /progress check
    data_received_at:    Optional[datetime] = None   # when /snapshot?format=json succeeded
    event_loop_id: Optional[int] = None                      # id(asyncio.get_running_loop())
    browser_warmed_at: datetime | None = None
    html_char_size: int | None = None
    row_count: Optional[int] = None
    field_count: Optional[int] = None



    def save_data_to_file(
        self,
        filename: str | None = None,
        *,
        dir_: str | Path = ".",
        pretty_json: bool = True,
        overwrite: bool = False,
        raise_if_empty: bool = True
    ) -> Path:


        """
        Persist ``self.data`` to *dir_*/ *filename* and return the Path.

        ▸ If *filename* is **None** an automatic one is generated:
            ``<snapshot_id or 'no_id'>.<html|json>``  
          (prefixed with root-domain when available).

        ▸ ``str``  payload  → ``.html``  
          ``dict | list``   → ``.json``

        ▸ Raises ``RuntimeError`` if ``self.data is None``.
        """
        
        import json, uuid, datetime as _dt
        

        if self.data in (None, [], {}):
            if raise_if_empty:
                raise RuntimeError("ScrapeResult.data is empty – nothing to save")
            return Path()   
        

        # pick extension by payload type
        if isinstance(self.data, str):
            ext, payload = ".html", self.data
            mode, encoding = "w", "utf-8"
        else:  # list / dict / any json-serialisable obj
            ext = ".json"
            if pretty_json:
                payload = json.dumps(self.data, ensure_ascii=False, indent=2)
            else:
                payload = json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))
            mode, encoding = "w", "utf-8"

        # construct default filename if none given
        if filename is None:
            stem = (self.root_domain or "data") + "-" + (self.snapshot_id or uuid.uuid4().hex)
            filename = f"{stem}{ext}"
        elif not filename.lower().endswith(ext):
            filename += ext

        path = Path(dir_) / filename
        if path.exists() and not overwrite:
            raise FileExistsError(f"{path} already exists (set overwrite=True to replace)")

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(mode, encoding=encoding) as fh:
            fh.write(payload)

        # convenience: record where we stored it
        self.saved_to = path  # type: ignore[attr-defined]
        self.saved_at = _dt.datetime.utcnow()  # type: ignore[attr-defined]
        return path





@dataclass
class SnapshotBundle:
    """
    The result of triggering one (or more) endpoint(s) for a single URL.
    """
    url: str
    # maps endpoint name (e.g. "posts", "comments", "profiles") → snapshot_id
    snapshot_ids: Dict[str, str] = field(default_factory=dict)
    
    