"""
AmazonScraper – Bright Data Amazon datasets wrapper
Automatically chooses the correct dataset-id for each endpoint, so callers
never pass dataset_id explicitly.
"""
from typing import Any, Dict, List, Optional, Sequence
from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper


# to run python -m brightdata.ready_scrapers.amazon.tests


class AmazonScraper(BrightdataBaseSpecializedScraper):
    # ------------------------------------------------------------------ #
    # Bright Data dataset-ids (static, per console) – edit only here
    # ------------------------------------------------------------------ #
    _DATASET = {
        "collect":  "gd_l7q7dkf244hwjntr0",
        "discover_keyword":  "gd_l7q7dkf244hwjntr0",
        "discover_category": "gd_l7q7dkf244hwjntr0",
        "search":   "gd_lwdb4vjm1ehb499uxs",
        # "reviews": "gd_le8e811kzy4ggddlq",            # keep for future use
    }

    # ------------------------------------------------------------------ #
    # constructor – default to the “collect” dataset so the base-class
    # has something valid for its own test_connection, etc.
    # ------------------------------------------------------------------ #
    def __init__(self, bearer_token: str, dataset_id: Optional[str] = None, **kw):
        super().__init__(
            dataset_id or self._DATASET["collect"],
            bearer_token,
            **kw,
        )

    # ──────────────────────────────────────────────────────────────────
    # COLLECT  ▸  BY URL
    # ──────────────────────────────────────────────────────────────────
    def collect_by_url(
        self,
        urls: Sequence[str],
        zipcodes: Optional[Sequence[str]] = None,
        *,
        dataset_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        payload = [
            {"url": u, "zipcode": (zipcodes or [""] * len(urls))[i]}
            for i, u in enumerate(urls)
        ]
        trigger_result= self._trigger(
            payload,
            dataset_id=dataset_id or self._DATASET["collect"],
        )
        # print("trigger_result:  ", trigger_result)
        return trigger_result

    # ──────────────────────────────────────────────────────────────────
    # DISCOVER  ▸  BY KEYWORD
    # ──────────────────────────────────────────────────────────────────
    def discover_by_keyword(
        self,
        keywords: Sequence[str],
        *,
        dataset_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        payload = [{"keyword": kw} for kw in keywords]
        return self._trigger(
            payload,
            dataset_id=dataset_id or self._DATASET["discover_keyword"],
            extra_params={"type": "discover_new", "discover_by": "keyword"},
        )

    # ──────────────────────────────────────────────────────────────────
    # DISCOVER  ▸  BY CATEGORY URL
    # ──────────────────────────────────────────────────────────────────
    def discover_by_category(
        self,
        category_urls: Sequence[str],
        sorts: Optional[Sequence[str]] = None,
        zipcodes: Optional[Sequence[str]] = None,
        *,
        dataset_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
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
            dataset_id=dataset_id or self._DATASET["discover_category"],
            extra_params={"type": "discover_new", "discover_by": "category_url"},
        )

    # ──────────────────────────────────────────────────────────────────
    # PRODUCTS  ▸  SEARCH
    # ──────────────────────────────────────────────────────────────────
    def search_products(
        self,
        keywords: Sequence[str],
        domains: Optional[Sequence[str]] = None,
        pages: Optional[Sequence[int]] = None,
        *,
        dataset_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        domains = domains or ["https://www.amazon.com"] * len(keywords)
        pages   = pages   or [1] * len(keywords)
        if not (len(keywords) == len(domains) == len(pages)):
            raise ValueError("keywords, domains and pages lengths must match")

        payload = [
            {"keyword": kw, "url": domains[i], "pages_to_search": pages[i]}
            for i, kw in enumerate(keywords)
        ]
        return self._trigger(
            payload,
            dataset_id=dataset_id or self._DATASET["search"],
        )

    # ------------------------------------------------------------------
    # all public calls delegate to the protected super()._trigger
    # ------------------------------------------------------------------
    def _trigger(
        self,
        data: List[Dict[str, Any]],
        *,
        dataset_id: Optional[str],
        include_errors: bool = True,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return super()._trigger(
            data,
            dataset_id=dataset_id,
            include_errors=include_errors,
            extra_params=extra_params,
        )
