#!/usr/bin/env python3
"""
brightdata.ready_scrapers.mouser.scraper
----------------------------------------

Simple wrapper around Bright Data’s *Mouser products* dataset.

Only one endpoint is documented by Bright Data at the moment:

* **collect_by_url** – scrape specific Mouser product pages.

The call is made in *async* mode (`sync_mode=async` is injected by the
shared base class), therefore it returns immediately with a **snapshot-id
string**.  Use the familiar helper `poll_until_ready()` or
`utils.async_poll.wait_ready()` to obtain the final JSON rows.
"""

from typing import Any, Dict, List, Sequence, Optional
from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# Static Bright-Data dataset ID (from the Mouser trigger example)
_DATASET_COLLECT_BY_URL = "gd_lfjty8942ogxzhmp8t"


@register("mouser")
class MouserScraper(BrightdataBaseSpecializedScraper):
    """
    ---
    agent_id: mouser
    title: MouserScraper
    desc: |
      Ready-made client for Bright Data’s Mouser product pages dataset.
      All calls run in async mode and return a snapshot-id immediately.
    example: |
      from brightdata.ready_scrapers.mouser import MouserScraper
      s = MouserScraper()
      snap = s.collect_by_url(["https://www.mouser.com/ProductDetail/ABRACON/ABM8-147456MHZ-D1X-T"])
      # → 's_abcdef12345'
    ---
    """

    def __init__(self, bearer_token: Optional[str] = None, **kw):
        """
        Initialize the MouserScraper.

        Parameters
        ----------
        bearer_token : str, optional
            Bright Data API token.  If omitted, reads BRIGHTDATA_TOKEN from the
            environment (a .env file is honoured).
        **kw :
            Extra keyword-arguments forwarded to the base class.
        """
        super().__init__(dataset_id=_DATASET_COLLECT_BY_URL,
                         bearer_token=bearer_token,
                         **kw)

    def collect_by_url(self, urls: Sequence[str]) -> str:
        """
        ---
        endpoint: collect_by_url
        desc: Scrape one or more Mouser **product detail pages**.
        params:
          urls:
            type: list[str]
            desc: Full Mouser product-page URLs.
        returns:
          type: str
          desc: snapshot_id string; poll until ready to retrieve JSON rows.
        example: |
          snap = scraper.collect_by_url([
            "https://www.mouser.com/ProductDetail/Diodes-Incorporated/DMN4035L-13?qs=EBDBlbfErPxf4bkLM3Jagg%3D%3D"
          ])
        ---
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET_COLLECT_BY_URL,
            # sync_mode=async is injected by the base class
        )
    def discover_by_category():
        pass

