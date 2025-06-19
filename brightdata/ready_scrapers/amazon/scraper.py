#!/usr/bin/env python3
"""
brightdata.ready_scrapers.amazon.scraper
----------------------------------------

Wrapper for Bright Data’s Amazon datasets.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence
import re, asyncio
from collections import defaultdict

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register


@register("amazon")
class AmazonScraper(BrightdataBaseSpecializedScraper):

    _DATASET = {
        "collect":           "gd_l7q7dkf244hwjntr0",
        "discover_keyword":  "gd_l7q7dkf244hwjntr0",
        "discover_category": "gd_l7q7dkf244hwjntr0",
        "search":            "gd_lwdb4vjm1ehb499uxs",
    }

    PATTERNS = {
        "product": re.compile(r"/dp/|/gp/product/"),
        "review":  re.compile(r"/product-reviews/"),
        "seller":  re.compile(r"/sp[\?&]seller="),
        "search":  re.compile(r"/s\?"),
    }

    # ───────────────────────── constructor ─────────────────────────
    def __init__(self, bearer_token: Optional[str] = None, **kw):
        super().__init__(self._DATASET["collect"], bearer_token, **kw)

    
    def classify_url(self, url: str) -> str:
        for kind, rx in self.PATTERNS.items():
            if rx.search(url):
                return kind
        raise ValueError(f"Unrecognised Amazon URL: {url}")
    
    
    def collect_by_url(
        self,
        url: str,
        **kw: Any
    ) -> str | None:
        """
        1) classify the single URL
        2) dispatch to the appropriate handler (wrapping it in a one-element list)
        3) return that handler’s snapshot_id, or None if the URL isn’t recognised
        """
        try:
            kind = self.classify_url(url)
        except ValueError:
            # unrecognised URL → nothing to trigger
            return None

        if kind == "product":
            return self.products__collect_by_url([url], **kw)
        elif kind == "review":
            return self.reviews__collect_by_url([url], **kw)
        elif kind == "seller":
            return self.sellers_info__collect_by_url([url], **kw)
        elif kind == "search":
            return self.products_search__collect_by_url([url], **kw)

        # fallback, should never hit
        return None
    
    async def collect_by_url_async(
        self,
        url: str,
        **kw: Any
    ) -> str | None:
        """
        Async version of collect_by_url:
        1) classify the single URL
        2) dispatch to the appropriate async handler
        3) return that handler’s snapshot_id, or None if the URL isn’t recognised
        """
        try:
            kind = self.classify_url(url)
        except ValueError:
            return None

        if kind == "product":
            return await self.products__collect_by_url_async([url], **kw)
        elif kind == "review":
            return await self.reviews__collect_by_url_async([url], **kw)
        elif kind == "seller":
            return await self.sellers_info__collect_by_url_async([url], **kw)
        elif kind == "search":
            return await self.products_search__collect_by_url_async([url], **kw)

        # fallback, should never hit
        return None

 

    

    # def collect_by_url(self, urls: Sequence[str], **kw) -> Dict[str, str]:
    #     buckets = self.dispatch_by_regex(urls, self.PATTERNS)
    #     unmatched = set(urls) - {u for lst in buckets.values() for u in lst}
    #     if unmatched:
    #         raise ValueError(f"Unrecognised Amazon URL(s): {unmatched}")
         
    #     out: Dict[str, str] = {}
    #     if "product" in buckets:
    #         out["product"] = self.products__collect_by_url(buckets["product"], **kw)
    #     if "review" in buckets:
    #         out["review"]  = self.reviews__collect_by_url(buckets["review"], **kw)      # stub
    #     if "seller" in buckets:
    #         out["seller"]  = self.sellers_info__collect_by_url(buckets["seller"], **kw) # stub
    #     if "search" in buckets:
    #         out["search"]  = self.products_search__collect_by_url(buckets["search"], **kw)
    #     return out

    # ────────────────────── products__collect_by_url ─────────────────────
    def products__collect_by_url(
        self,
        urls: Sequence[str],
        zipcodes: Optional[Sequence[str]] = None,
    ) -> str:
        payload = [
            {"url": u, "zipcode": (zipcodes or [""] * len(urls))[i]}
            for i, u in enumerate(urls)
        ]
        return self.trigger(payload, dataset_id=self._DATASET["collect"])

    # ───────────────── products__discover_by_category_url ────────────────
    def products__discover_by_category_url(
        self,
        category_urls: Sequence[str],
        sorts: Optional[Sequence[str]] = None,
        zipcodes: Optional[Sequence[str]] = None,
    ) -> str:
        sorts    = sorts    or [""] * len(category_urls)
        zipcodes = zipcodes or [""] * len(category_urls)
        if not (len(category_urls) == len(sorts) == len(zipcodes)):
            raise ValueError("category_urls, sorts and zipcodes must align")

        payload = [
            {"url": url, "sort_by": sorts[i], "zipcode": zipcodes[i]}
            for i, url in enumerate(category_urls)
        ]
        return self.trigger(
            payload,
            dataset_id=self._DATASET["discover_category"],
            extra_params={"type": "discover_new", "discover_by": "category_url"},
        )

    # ───────────────── products__discover_by_keyword ─────────────────────
    def products__discover_by_keyword(self, keywords: Sequence[str]) -> str:
        payload = [{"keyword": kw} for kw in keywords]
        return self.trigger(
            payload,
            dataset_id=self._DATASET["discover_keyword"],
            extra_params={"type": "discover_new", "discover_by": "keyword"},
        )

    # ───────────────── products_search__collect_by_url ───────────────────
    def products_search__collect_by_url(
        self,
        keywords: Sequence[str],
        domains: Optional[Sequence[str]] = None,
        pages: Optional[Sequence[int]] = None,
    ) -> str:
        domains = domains or ["https://www.amazon.com"] * len(keywords)
        pages   = pages   or [1] * len(keywords)
        if not (len(keywords) == len(domains) == len(pages)):
            raise ValueError("keywords, domains and pages lengths must match")

        payload = [
            {"keyword": kw, "url": domains[i], "pages_to_search": pages[i]}
            for i, kw in enumerate(keywords)
        ]
        return self.trigger(payload, dataset_id=self._DATASET["search"])

    # =====================================================================
    # ASYNC variants (use _trigger_async)
    # =====================================================================
    async def collect_by_url_async(
        self, urls: Sequence[str], zipcodes: Optional[Sequence[str]] = None
    ) -> Dict[str, str]:
        buckets = self.dispatch_by_regex(urls, self.PATTERNS)
        unmatched = set(urls) - {u for lst in buckets.values() for u in lst}
        if unmatched:
            raise ValueError(f"Unrecognised Amazon URL(s): {unmatched}")

        tasks: Dict[str, asyncio.Task[str]] = {}
        if "product" in buckets:
            payload = [
                {"url": u, "zipcode": (zipcodes or [""] * len(buckets['product']))[i]}
                for i, u in enumerate(buckets["product"])
            ]
            tasks["product"] = asyncio.create_task(
                self._trigger_async(payload, dataset_id=self._DATASET["collect"])
            )
        if "search" in buckets:
            domains = self.config.get("domains", ["https://www.amazon.com"] * len(buckets["search"]))
            pages   = self.config.get("pages",   [1] * len(buckets["search"]))
            payload = [
                {"keyword": kw, "url": domains[i], "pages_to_search": pages[i]}
                for i, kw in enumerate(buckets["search"])
            ]
            tasks["search"] = asyncio.create_task(
                self._trigger_async(payload, dataset_id=self._DATASET["search"])
            )
        # stubs for review / seller …
        results = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), results))

    async def products__collect_by_url_async(
        self, urls: Sequence[str], zipcodes: Optional[Sequence[str]] = None
    ) -> str:
        payload = [
            {"url": u, "zipcode": (zipcodes or [""] * len(urls))[i]}
            for i, u in enumerate(urls)
        ]
        return await self._trigger_async(payload, dataset_id=self._DATASET["collect"])

    async def products__discover_by_category_url_async(
        self,
        category_urls: Sequence[str],
        sorts: Optional[Sequence[str]] = None,
        zipcodes: Optional[Sequence[str]] = None,
    ) -> str:
        sorts    = sorts    or [""] * len(category_urls)
        zipcodes = zipcodes or [""] * len(category_urls)
        if not (len(category_urls) == len(sorts) == len(zipcodes)):
            raise ValueError("category_urls, sorts and zipcodes must align")

        payload = [
            {"url": url, "sort_by": sorts[i], "zipcode": zipcodes[i]}
            for i, url in enumerate(category_urls)
        ]
        return await self._trigger_async(
            payload,
            dataset_id=self._DATASET["discover_category"],
            extra_params={"type": "discover_new", "discover_by": "category_url"},
        )

    async def products__discover_by_keyword_async(
        self, keywords: Sequence[str]
    ) -> str:
        payload = [{"keyword": kw} for kw in keywords]
        return await self._trigger_async(
            payload,
            dataset_id=self._DATASET["discover_keyword"],
            extra_params={"type": "discover_new", "discover_by": "keyword"},
        )

    async def products_search__collect_by_url_async(
        self,
        keywords: Sequence[str],
        domains: Optional[Sequence[str]] = None,
        pages: Optional[Sequence[int]] = None,
    ) -> str:
        domains = domains or ["https://www.amazon.com"] * len(keywords)
        pages   = pages   or [1] * len(keywords)
        if not (len(keywords) == len(domains) == len(pages)):
            raise ValueError("keywords, domains and pages lengths must match")

        payload = [
            {"keyword": kw, "url": domains[i], "pages_to_search": pages[i]}
            for i, kw in enumerate(keywords)
        ]
        return await self._trigger_async(payload, dataset_id=self._DATASET["search"])
    
    # ----------------------------------------------------------------------
    # Stubs for not-yet-wrapped endpoints (keep interface stable)
    # ----------------------------------------------------------------------
    def products__discover_by_best_sellers_url(self): ...
    def products__discover_by_upc(self): ...
    def reviews__collect_by_url(self): ...
    def sellers_info__collect_by_url(self): ...
