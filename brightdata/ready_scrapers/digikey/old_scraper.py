"""
brightdata.ready_scrapers.digikey.scraper
-----------------------------------------

High-level wrapper around Bright Data’s *Digi-Key* datasets.

Implemented endpoints
~~~~~~~~~~~~~~~~~~~~~
• collect_by_url()
• discover_by_category()

Both endpoints are forced to run **asynchronously** (`sync_mode=async`
is injected by BrightdataBaseSpecializedScraper._trigger), so each call
always returns a *snapshot-id* string.  Use `poll_until_ready()` (see the
Amazon smoke-test) or any other polling helper to obtain the final data.

Usage
~~~~~
>>> from brightdata.ready_scrapers.digikey import DigikeyScraper
>>> scraper = DigikeyScraper(bearer_token=TOKEN)
>>> snap = scraper.collect_by_url(
...     ["https://www.digikey.com/en/products/detail/...",
...      "https://www.digikey.com/en/products/detail/..."])
>>> # poll snapshot-id ‘snap’ until status == ready  ➜  list[dict]
"""

from typing import Any, Dict, List, Sequence, Optional
from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

# default dataset-IDs taken from your examples
_DATASET_COLLECT_BY_URL       = "gd_lj74waf72416ro0k65"
_DATASET_DISCOVER_BY_CATEGORY = "gd_lj74waf72416ro0k65"   # same dataset, diff params


@register("digikey")              # ← one word, no TLD juggling
class DigikeyScraper(BrightdataBaseSpecializedScraper):
    """Ready-made Bright Data client for Digi-Key product data."""

    # we initialise the base with the *collect* dataset ID; discover method
    # overrides it when calling _trigger.
    def __init__(
        self,
        bearer_token: str,
        *,
        dataset_id: str = _DATASET_COLLECT_BY_URL,
    ):
        super().__init__(dataset_id=dataset_id, bearer_token=bearer_token)

    # ─────────────────────────────────────────────────────────────
    # PUBLIC ENDPOINTS
    # ─────────────────────────────────────────────────────────────
    def collect_by_url(
        self,
        urls: Sequence[str],
    ) -> str:
        """
        Bright Data  ➜  *digikey-products → Collect by URL*

        Returns
        -------
        snapshot_id : str
            Use scraper.get_data() or your polling helper to fetch the
            finished rows.
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET_COLLECT_BY_URL,   # always async
        )

    # ------------------------------------------------------------------ #
    def discover_by_category(
        self,
        category_urls: Sequence[str],
    ) -> str:
        """
        Bright Data  ➜  *digikey-products → Discover by category*

        Each entry in `category_urls` should be a full Digi-Key category
        link (as in the examples you supplied).

        Returns `snapshot_id` (string).
        """
        payload = [{"category_url": url} for url in category_urls]
        return self._trigger(
            payload,
            dataset_id=_DATASET_DISCOVER_BY_CATEGORY,
            extra_params={
                "type":        "discover_new",
                "discover_by": "category",
            },
        )

    # ─────────────────────────────────────────────────────────────
    # INTERNAL
    # ─────────────────────────────────────────────────────────────
    # _trigger is inherited; nothing extra needed here.


# make “from brightdata.ready_scrapers.digikey import DigikeyScraper” work
__all__ = ["DigikeyScraper"]
