#!/usr/bin/env python3
from typing import Any, Dict, List, Optional, Sequence

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

@register("amazon")
class AmazonScraper(BrightdataBaseSpecializedScraper):
    """
    ---
    agent_id: amazon
    title: AmazonScraper
    desc: >
      Ready-made helper around Bright Data’s Amazon datasets.
      Automatically picks the right dataset-id for every endpoint.
    example: |
      from brightdata.ready_scrapers.amazon import AmazonScraper
      scraper = AmazonScraper()
      snap = scraper.collect_by_url(
        ["https://www.amazon.com/dp/B0CRMZHDG8"],
        zipcodes=["94107"]
      )
    ---
    """

    _DATASET = {
        "collect":           "gd_l7q7dkf244hwjntr0",
        "discover_keyword":  "gd_l7q7dkf244hwjntr0",
        "discover_category": "gd_l7q7dkf244hwjntr0",
        "search":            "gd_lwdb4vjm1ehb499uxs",
    }

    def __init__(self, bearer_token: Optional[str] = None, **kw):
        super().__init__(
            self._DATASET["collect"],  # default for connectivity checks
            bearer_token,
            **kw,
        )

    def collect_by_url(
        self,
        urls: Sequence[str],
        zipcodes: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]] | str:
        """
        ---
        endpoint: collect_by_url
        desc: Scrape one or many Amazon product pages (ASIN detail).
        params:
          urls:
            type: list[str]
            desc: Product detail-page URLs.
          zipcodes:
            type: list[str]
            desc: Postal codes aligned with URLs; empty string to skip.
        returns:
          type: list[dict] | str
          desc: Immediate rows (sync) or snapshot_id (async).
        example: |
          snap = scraper.collect_by_url(
            ["https://www.amazon.com/dp/B0CRMZHDG8"], zipcodes=["94107"]
          )
        ---
        """
        payload = [
            {"url": u, "zipcode": (zipcodes or [""] * len(urls))[i]}
            for i, u in enumerate(urls)
        ]
        return self._trigger(payload, dataset_id=self._DATASET["collect"])

    def discover_by_keyword(self, keywords: Sequence[str]) -> List[Dict[str, Any]] | str:
        """
        ---
        endpoint: discover_by_keyword
        desc: Run an Amazon keyword search and return new product links.
        params:
          keywords:
            type: list[str]
            desc: Search terms (one job per keyword).
        returns:
          type: list[dict] | str
          desc: Immediate rows or snapshot_id.
        example: |
          snap = scraper.discover_by_keyword(["laptop", "headphones"])
        ---
        """
        payload = [{"keyword": kw} for kw in keywords]
        return self._trigger(
            payload,
            dataset_id=self._DATASET["discover_keyword"],
            extra_params={"type": "discover_new", "discover_by": "keyword"},
        )

    def discover_by_category(
        self,
        category_urls: Sequence[str],
        sorts: Optional[Sequence[str]] = None,
        zipcodes: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]] | str:
        """
        ---
        endpoint: discover_by_category
        desc: Collect new ASINs from category/browse URLs.
        params:
          category_urls:
            type: list[str]
            desc: Browse-node URLs.
          sorts:
            type: list[str]
            desc: Sort options aligned with URLs.
          zipcodes:
            type: list[str]
            desc: Postal codes aligned with URLs.
        returns:
          type: list[dict] | str
          desc: Immediate rows or snapshot_id.
        raises:
          ValueError:
            desc: If the three input lists’ lengths don’t match.
        example: |
          snap = scraper.discover_by_category(
            ["https://www.amazon.com/s?i=electronics"],
            sorts=["Best Sellers"],
            zipcodes=["94107"]
          )
        ---
        """
        sorts = sorts or [""] * len(category_urls)
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

    def search_products(
        self,
        keywords: Sequence[str],
        domains: Optional[Sequence[str]] = None,
        pages: Optional[Sequence[int]] = None,
    ) -> List[Dict[str, Any]] | str:
        """
        ---
        endpoint: search_products
        desc: Crawl Amazon SERPs across multiple storefronts.
        params:
          keywords:
            type: list[str]
            desc: Search strings.
          domains:
            type: list[str]
            desc: Marketplace domains aligned with keywords.
          pages:
            type: list[int]
            desc: Number of pages per keyword.
        returns:
          type: list[dict] | str
          desc: Rows (sync) or snapshot_id (async).
        raises:
          ValueError:
            desc: If keywords, domains, and pages lengths differ.
        example: |
          snap = scraper.search_products(
            ["laptop"], domains=["https://www.amazon.com"], pages=[2]
          )
        ---
        """
        domains = domains or ["https://www.amazon.com"] * len(keywords)
        pages = pages or [1] * len(keywords)
        if not (len(keywords) == len(domains) == len(pages)):
            raise ValueError("keywords, domains and pages lengths must match")

        payload = [
            {"keyword": kw, "url": domains[i], "pages_to_search": pages[i]}
            for i, kw in enumerate(keywords)
        ]
        return self._trigger(payload, dataset_id=self._DATASET["search"])

    def _trigger(
        self,
        data: List[Dict[str, Any]],
        *,
        dataset_id: str,
        include_errors: bool = True,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]] | str:
        """
        ---
        endpoint: _trigger
        desc: Internal helper delegating to the base class.
        params:
          data:
            type: list[dict]
            desc: Payload for Bright Data.
          dataset_id:
            type: str
            desc: Dataset identifier.
          include_errors:
            type: bool
            desc: Include error objects in response.
          extra_params:
            type: dict
            desc: Additional query parameters.
        returns:
          type: list[dict] | str
          desc: JSON rows or snapshot_id.
        ---
        """
        return super()._trigger(
            data,
            dataset_id=dataset_id,
            include_errors=include_errors,
            extra_params=extra_params,
        )
