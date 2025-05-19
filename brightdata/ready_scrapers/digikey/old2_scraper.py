"""
brightdata.ready_scrapers.digikey.scraper
-----------------------------------------

High-level wrapper around Bright Data’s **Digi-Key** datasets.

Implemented endpoints
~~~~~~~~~~~~~~~~~~~~~
• collect_by_url()        – scrape explicit product links  
• discover_by_category()  – crawl category pages for *new* parts

Both endpoints are forced to run **asynchronously** (`sync_mode=async`
is injected by the base class), therefore each call returns a **snapshot-id**
string.  Feed that id to:

    poll_until_ready()  │  fetch_snapshot_async()  │  get_data()

to obtain the final JSON rows.
"""

from typing import Any, Dict, List, Sequence, Optional
from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# Bright-Data dataset-ids (static, copied from your examples)
_DATASET_ID = "gd_lj74waf72416ro0k65"      # same id, different params decide the mode


@register("digikey")                       # one word – registry handles *.com, *.de, …
class DigikeyScraper(BrightdataBaseSpecializedScraper):
    """
    Ready-made Bright Data client for Digi-Key product data.

    A single dataset-id is used for both *collect* and *discover*;
    we simply vary the ``extra_params`` when triggering the job.
    """

    # ------------------------------------------------------------------ #
    # constructor – bearer_token optional (picked up from environment)
    # ------------------------------------------------------------------ #
    def __init__(self, bearer_token: Optional[str] = None, **kw):
        """
        Parameters
        ----------
        bearer_token : str, optional
            Bright Data API token.  If *None*, ``BRIGHTDATA_TOKEN`` is read
            from the environment (a *.env* file is honoured).
        **kw :
            Extra keyword-arguments forwarded to the base class.
        """
        super().__init__(_DATASET_ID, bearer_token, **kw)

    # ──────────────────────────────────────────────────────────────────
    # COLLECT ▸ BY URL
    # ──────────────────────────────────────────────────────────────────
    def collect_by_url(self, urls: Sequence[str]) -> str:
        """
        Scrape **specific Digi-Key product pages**.

        Parameters
        ----------
        urls : sequence of str
            Full product URLs (one BD job handles *all* of them).

        Returns
        -------
        snapshot_id : str  
            Poll this id until the status becomes *ready* to retrieve
            ``list[dict]`` rows.
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(payload, dataset_id=_DATASET_ID)

    # ──────────────────────────────────────────────────────────────────
    # DISCOVER ▸ BY CATEGORY
    # ──────────────────────────────────────────────────────────────────
    def discover_by_category(self, category_urls: Sequence[str]) -> str:
        """
        Crawl **Digi-Key category pages** and return links to *new* parts
        (Bright Data “discover_new → category” workflow).

        Parameters
        ----------
        category_urls : sequence of str
            e.g. ``https://www.digikey.com/en/products/filter/...``

        Returns
        -------
        snapshot_id : str  
            Use any polling helper to fetch the finished JSON.
        """
        payload = [{"category_url": url} for url in category_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET_ID,
            extra_params={"type": "discover_new", "discover_by": "category"},
        )

    # ------------------------------------------------------------------
    # _trigger is inherited – no override needed
    # ------------------------------------------------------------------ #


# allow “from brightdata.ready_scrapers.digikey import DigiKeyScraper”
__all__ = ["DigiKeyScraper"]
