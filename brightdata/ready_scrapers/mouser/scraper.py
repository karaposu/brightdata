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

Example
~~~~~~~
>>> from brightdata.ready_scrapers.mouser import MouserScraper
>>> s = MouserScraper(bearer_token=TOKEN)
>>> snap = s.collect_by_url(["https://www.mouser.com/ProductDetail/…"])
>>> rows = poll_until_ready(s, snap).data
"""

from typing import Any, Dict, List, Sequence
from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# dataset taken from the request you provided
_DATASET_COLLECT_BY_URL = "gd_lfjty8942ogxzhmp8t"


@register("mouser")        
class MouserScraper(BrightdataBaseSpecializedScraper):
    """
    Ready-made Bright Data client for Mouser product data.

    Endpoints
    ---------
    • collect_by_url(urls)

    All other Mouser dataset flavours (discover by category, keyword, …
    if Bright Data adds them later) can be implemented by copying the
    pattern shown for Digi-Key and Amazon.
    """

    # the base class only needs *one* dataset_id for initialisation;
    # individual methods can override with their own id if required.
    def __init__(
        self,
        bearer_token: str,
        *,
        dataset_id: str = _DATASET_COLLECT_BY_URL,
    ):
        super().__init__(dataset_id=dataset_id, bearer_token=bearer_token)

    # ─────────────────────────────────────────────────────────────
    # public endpoint
    # ─────────────────────────────────────────────────────────────
    def collect_by_url(
        self,
        urls: Sequence[str],
    ) -> str:
        """
        Bright Data → *mouser-products → Collect by URL*

        Parameters
        ----------
        urls : list[str]
            One or many full Mouser product-page URLs.

        Returns
        -------
        snapshot_id : str
            Pass to scraper.get_data() or an async/await poller.
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET_COLLECT_BY_URL,
            # no extra_params needed; _trigger already injects sync_mode=async
        )

    # inherited _trigger() already handles everything we need.


# so that “from brightdata.ready_scrapers.mouser import MouserScraper” works
# __all__ = ["MouserScraper"]
