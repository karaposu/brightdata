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


@dataclass
class CrawlResult:
    """
    Result from Crawler API operations (collect or discover).
    
    Handles both single URL collection and domain discovery with multiple pages.
    Each page in the crawl contains markdown, HTML, text formats.
    """
    # Core fields
    success: bool                          # True if operation succeeded
    operation: str                         # "collect" or "discover"
    status: str                            # "ready" | "error" | "timeout" | "running"
    
    # Input tracking - what was sent to the API
    input_urls: Optional[List[str]] = None    # URLs requested (for collect)
    domain: Optional[str] = None              # Domain (for discover)
    crawl_params: Optional[Dict[str, Any]] = None  # All params sent (filter, exclude_filter, depth, ignore_sitemap, etc.)
    
    # Response data
    pages: Optional[List[Dict[str, Any]]] = None  # List of page data
    page_count: int = 0                           # Number of pages returned
    
    # Metadata
    snapshot_id: Optional[str] = None      # BrightData snapshot ID
    cost: Optional[float] = None           # Cost estimate
    error: Optional[str] = None            # Error message if failed
    
    # Timing
    request_sent_at: Optional[datetime] = None
    snapshot_id_received_at: Optional[datetime] = None
    snapshot_polled_at: List[datetime] = field(default_factory=list)
    data_received_at: Optional[datetime] = None
    collection_duration_ms: Optional[int] = None  # From API response
    
    # Analysis fields (populated after data received)
    urls_collected: List[str] = field(default_factory=list)
    formats_available: Dict[str, int] = field(default_factory=dict)  # Count of each format
    total_markdown_chars: int = 0
    total_html_chars: int = 0
    
    def get_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Get a specific page by URL from the results."""
        if not self.pages:
            return None
        for page in self.pages:
            if page.get("url") == url:
                return page
        return None
    
    def get_markdown_content(self) -> List[str]:
        """Get all markdown content from pages."""
        if not self.pages:
            return []
        return [p.get("markdown", "") for p in self.pages if p.get("markdown")]
    
    def get_urls(self) -> List[str]:
        """Get all URLs from the crawled pages."""
        if not self.pages:
            return []
        return [p.get("url", "") for p in self.pages if p.get("url")]
    
    def save_pages(self, dir_: str | Path = ".", format: str = "json") -> List[Path]:
        """
        Save all pages to individual files.
        Returns list of created file paths.
        """
        import json
        from pathlib import Path
        
        if not self.pages:
            raise RuntimeError("No pages to save")
        
        dir_path = Path(dir_)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        for i, page in enumerate(self.pages):
            # Create filename from URL or use index
            url = page.get("url", f"page_{i}")
            # Clean URL for filename
            filename = url.replace("https://", "").replace("http://", "")
            filename = filename.replace("/", "_").replace(":", "")
            if not filename:
                filename = f"page_{i}"
            
            filepath = dir_path / f"{filename}.{format}"
            
            if format == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(page, f, indent=2, ensure_ascii=False)
            elif format == "md":
                # Save just markdown content
                content = page.get("markdown", "")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif format == "html":
                # Save just HTML content
                content = page.get("page_html", "")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            saved_files.append(filepath)
        
        return saved_files
    
    def analyze_content(self):
        """Analyze the crawled content and populate analysis fields."""
        if not self.pages:
            return
        
        self.urls_collected = self.get_urls()
        self.page_count = len(self.pages)
        
        # Count available formats
        format_counts = {
            "markdown": 0,
            "html": 0,
            "text": 0,
            "json_ld": 0,
            "title": 0
        }
        
        for page in self.pages:
            if page.get("markdown"):
                format_counts["markdown"] += 1
                self.total_markdown_chars += len(page["markdown"])
            if page.get("page_html"):
                format_counts["html"] += 1
                self.total_html_chars += len(page["page_html"])
            if page.get("html2text"):
                format_counts["text"] += 1
            if page.get("ld_json"):
                format_counts["json_ld"] += 1
            if page.get("page_title"):
                format_counts["title"] += 1
        
        self.formats_available = format_counts
    
    