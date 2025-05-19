"""
AmazonScraper – Bright Data Amazon datasets wrapper
===================================================

• Ready-made helper around Bright Data’s Amazon datasets.  
• Picks the correct *dataset-id* for every endpoint automatically.

Example
-------
>>> from brightdata.ready_scrapers.amazon import AmazonScraper
>>> s = AmazonScraper()                       # token read from .env
>>> snap = s.collect_by_url(
...     ["https://www.amazon.com/dp/B0CRMZHDG8"],
...     zipcodes=["94107"]
... )
"""

from typing import Any, Dict, List, Optional, Sequence
from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register


@register("amazon")                  # handled by brightdata.registry
class AmazonScraper(BrightdataBaseSpecializedScraper):
    # ------------------------------------------------------------------ #
    # Bright Data dataset-ids (static, straight from BD console)
    # ------------------------------------------------------------------ #
    _DATASET = {
        "collect":           "gd_l7q7dkf244hwjntr0",
        "discover_keyword":  "gd_l7q7dkf244hwjntr0",
        "discover_category": "gd_l7q7dkf244hwjntr0",
        "search":            "gd_lwdb4vjm1ehb499uxs",
    }

    # ------------------------------------------------------------------ #
    # constructor — bearer_token is optional (taken from env if omitted)
    # ------------------------------------------------------------------ #
    def __init__(self, bearer_token: Optional[str] = None, **kw):
        """
        Parameters
        ----------
        bearer_token : str, optional
            Bright Data API token.  If *None*, the base class looks for an
            environment variable called ``BRIGHTDATA_TOKEN`` (``python-dotenv``
            is honoured so a *.env* file works).
        **kw :
            Extra keyword-arguments forwarded verbatim to the base class.
        """
        super().__init__(
            self._DATASET["collect"],     # default dataset for connectivity
            bearer_token,
            **kw,
        )

    # ──────────────────────────────────────────────────────────────────
    # COLLECT ▸ BY URL
    # ──────────────────────────────────────────────────────────────────
    def collect_by_url(
        self,
        urls: Sequence[str],
        zipcodes: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]] | str:
        """
        Scrape one or many Amazon **product pages**.

        Parameters
        ----------
        urls : sequence of str
            Product detail-page URLs.
        zipcodes : sequence of str or None
            Postal codes; must align with *urls* length.  
            Use an empty string to skip zip validation.

        Returns
        -------
        list[dict] | str  
            * **Sync-mode enabled** → a list of product-rows right away.  
            * **Async (default)**   → a *snapshot_id* (str).  Pass that id to
              ``get_data()`` or one of the poll helpers.
        """
        payload = [
            {"url": u, "zipcode": (zipcodes or [""] * len(urls))[i]}
            for i, u in enumerate(urls)
        ]
        return self._trigger(payload, dataset_id=self._DATASET["collect"])

    # ──────────────────────────────────────────────────────────────────
    # DISCOVER ▸ BY KEYWORD
    # ──────────────────────────────────────────────────────────────────
    def discover_by_keyword(self, keywords: Sequence[str]) -> List[Dict[str, Any]] | str:
        """
        Run an Amazon **keyword search** and return product links not seen
        before (*Bright Data’s “discover_new” semantics*).

        Parameters
        ----------
        keywords : sequence of str
            Search terms (one BD job per keyword).

        Returns
        -------
        list[dict] | str  
            Immediate JSON (sync mode) **or** snapshot-id (async).
        """
        payload = [{"keyword": kw} for kw in keywords]
        return self._trigger(
            payload,
            dataset_id=self._DATASET["discover_keyword"],
            extra_params={"type": "discover_new", "discover_by": "keyword"},
        )

    # ──────────────────────────────────────────────────────────────────
    # DISCOVER ▸ BY CATEGORY URL
    # ──────────────────────────────────────────────────────────────────
    def discover_by_category(
        self,
        category_urls: Sequence[str],
        sorts: Optional[Sequence[str]] = None,
        zipcodes: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]] | str:
        """
        Walk an Amazon **browse / category URL** and collect new ASINs.

        Parameters
        ----------
        category_urls : sequence of str
            e.g. ``https://www.amazon.com/s?i=arts-crafts-intl-ship`` …
        sorts : sequence of str, optional
            *Best Sellers*, *Price: Low to High*, *Avg. Customer Review* …  
            Pass an empty string for the default sort.
        zipcodes : sequence of str, optional
            Optional postal codes per URL.

        Returns
        -------
        list[dict] | str  
            Immediate rows or a snapshot-id depending on BD sync-mode.

        Raises
        ------
        ValueError
            If *category_urls*, *sorts* and *zipcodes* lengths don’t match.
        """
        sorts    = sorts    or [""] * len(category_urls)
        zipcodes = zipcodes or [""] * len(category_urls)
        if not (len(category_urls) == len(sorts) == len(zipcodes)):
            raise ValueError("category_urls, sorts and zipcodes must align")

        payload = [
            {"url": url, "sort_by": sorts[i], "zipcode": zipcodes[i]}
            for i, url in enumerate(category_urls)
        ]
        return self._trigger(
            payload,
            dataset_id=self._DATASET["discover_category"],
            extra_params={"type": "discover_new", "discover_by": "category_url"},
        )

    # ──────────────────────────────────────────────────────────────────
    # PRODUCTS ▸ SEARCH
    # ──────────────────────────────────────────────────────────────────
    def search_products(
        self,
        keywords: Sequence[str],
        domains: Optional[Sequence[str]] = None,
        pages: Optional[Sequence[int]] = None,
    ) -> List[Dict[str, Any]] | str:
        """
        Crawl Amazon **SERPs** (search results) across multiple storefronts.

        Parameters
        ----------
        keywords : sequence of str
            Search strings to submit to Amazon.
        domains : sequence of str, optional
            One marketplace domain per keyword  
            (defaults to ``https://www.amazon.com`` for all).
        pages : sequence of int, optional
            How many result pages to walk for each keyword.

        Returns
        -------
        list[dict] | str  
            Either the rows (sync) or a snapshot-id (async).

        Raises
        ------
        ValueError
            If *keywords*, *domains* and *pages* lengths differ.
        """
        domains = domains or ["https://www.amazon.com"] * len(keywords)
        pages   = pages   or [1] * len(keywords)
        if not (len(keywords) == len(domains) == len(pages)):
            raise ValueError("keywords, domains and pages lengths must match")

        payload = [
            {"keyword": kw, "url": domains[i], "pages_to_search": pages[i]}
            for i, kw in enumerate(keywords)
        ]
        return self._trigger(payload, dataset_id=self._DATASET["search"])

    # ------------------------------------------------------------------
    # Internal helper – delegates to the protected base implementation
    # ------------------------------------------------------------------
    def _trigger(
        self,
        data: List[Dict[str, Any]],
        *,
        dataset_id: str,
        include_errors: bool = True,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return super()._trigger(
            data,
            dataset_id=dataset_id,
            include_errors=include_errors,
            extra_params=extra_params,
        )
