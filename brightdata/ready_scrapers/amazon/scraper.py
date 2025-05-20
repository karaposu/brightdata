#!/usr/bin/env python3
from typing import Any, Dict, List, Optional, Sequence

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from collections import defaultdict
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

    
    # products__collect_by_url
    # products__discover_by_best_sellers_url
    # products__discover_by_category_url
    # products__discover_by_keyword
    # products__discoter_by_upc
    # reviews__collect_by_url
    # sellers_info__collect_by_url
    # products_search__collect_by_url

    
    # ═══════════════════════════════════════════════════════════════════ #
    # 0.  SMART ROUTER  ▸  collect_by_url()
    # ═══════════════════════════════════════════════════════════════════ #
    def collect_by_url(self, urls: Sequence[str], **kw) -> Dict[str, str]:
        """
        High-level “just scrape it” helper.

        It inspects each input URL, detects its type and forwards the sub-list
        to one of the specialised methods below.

        Parameters
        ----------
        urls : sequence[str]
            A mix of product, review, seller and search URLs.

        Returns
        -------
        dict[str, str]
            Keys: ``product | review | seller | search``  
            Values: snapshot-ids returned by the respective endpoints.

        Notes
        -----
        *The mapping ‹type → original-URLs› is stored on the instance under
        ``self._url_buckets`` so that external helpers (e.g. *scrape_url*) can
        reconcile results.*
        """
        buckets: DefaultDict[str, List[str]] = defaultdict(list)

        for u in urls:
            if   _RX_PRODUCT.search(u): buckets["product"].append(u)
            elif _RX_REVIEW.search(u):  buckets["review"].append(u)
            elif _RX_SELLER.search(u):  buckets["seller"].append(u)
            elif _RX_SEARCH.search(u):  buckets["search"].append(u)
            else:
                raise ValueError(f"Unrecognised Amazon URL: {u}")

        self._url_buckets: Dict[str, List[str]] = dict(buckets)  # expose

        out: Dict[str, str] = {}
        if buckets.get("product"):
            out["product"] = self.products__collect_by_url(buckets["product"], **kw)
        if buckets.get("review"):
            out["review"]  = self.reviews__collect_by_url(buckets["review"], **kw)   # stub
        if buckets.get("seller"):
            out["seller"]  = self.sellers_info__collect_by_url(buckets["seller"], **kw)  # stub
        if buckets.get("search"):
            out["search"]  = self.products_search__collect_by_url(buckets["search"], **kw)

        return out

    def products__collect_by_url(
        self,
        urls: Sequence[str],
        zipcodes: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]] | str:
        """
        ---
        endpoint: products__collect_by_url
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
          snap = scraper.products__collect_by_url(
            ["https://www.amazon.com/dp/B0CRMZHDG8"], zipcodes=["94107"]
          )
        ---
        """
        payload = [
            {"url": u, "zipcode": (zipcodes or [""] * len(urls))[i]}
            for i, u in enumerate(urls)
        ]
        return self._trigger(payload, dataset_id=self._DATASET["collect"])
    
    def products__discover_by_best_sellers_url():
        pass
    
    def products__discover_by_category_url( self,
        category_urls: Sequence[str],
        sorts: Optional[Sequence[str]] = None,
        zipcodes: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]] | str:
        """
        ---
        endpoint: products__discover_by_category_url
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
          snap = scraper.products__discover_by_category_url(
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
    

    def products__discover_by_keyword(self, keywords: Sequence[str]) -> List[Dict[str, Any]] | str:
        """
        ---
        endpoint: products__discover_by_keyword
        desc: Run an Amazon keyword search and return new product links.
        params:
          keywords:
            type: list[str]
            desc: Search terms (one job per keyword).
        returns:
          type: list[dict] | str
          desc: Immediate rows or snapshot_id.
        example: |
          snap = scraper.products__discover_by_keyword(["laptop", "headphones"])
        ---
        """
        payload = [{"keyword": kw} for kw in keywords]
        return self._trigger(
            payload,
            dataset_id=self._DATASET["discover_keyword"],
            extra_params={"type": "discover_new", "discover_by": "keyword"},
        )
    
    def products__discover_by_upc():
        pass
    
    def reviews__collect_by_url():
        pass
    
    def sellers_info__collect_by_url():
        pass

   
  

    def products_search__collect_by_url(
        self,
        keywords: Sequence[str],
        domains: Optional[Sequence[str]] = None,
        pages: Optional[Sequence[int]] = None,
    ) -> List[Dict[str, Any]] | str:
        """
        ---
        endpoint: products_search__collect_by_url
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
          snap = scraper.products_search__collect_by_url(
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

    