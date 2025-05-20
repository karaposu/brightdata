#!/usr/bin/env python3
from typing import Any, Dict, List, Sequence, Optional

from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper
from brightdata.registry import register

@register("digikey")
class DigikeyScraper(BrightdataBaseSpecializedScraper):
    """
    ---
    agent_id: digikey
    title: DigikeyScraper
    desc: >
      High-level wrapper around Bright Data’s Digi-Key datasets.
      A single dataset-id is used for both collect and discover.
    example: |
      from brightdata.ready_scrapers.digikey import DigikeyScraper
      scraper = DigikeyScraper()
      snap = scraper.collect_by_url([
        "https://www.digikey.com/en/products/detail/STMicroelectronics/STM32F407VGT6/2747117"
      ])
    ---
    """

    _DATASET_ID = "gd_lj74waf72416ro0k65"

    def __init__(self, bearer_token: Optional[str] = None, **kw):
        """
        ---
        endpoint: constructor
        desc: Instantiate a DigikeyScraper; bearer_token is optional.
        params:
          bearer_token:
            type: str
            desc: Bright Data API token (reads from BRIGHTDATA_TOKEN if None).
          kw:
            type: dict
            desc: Extra keyword-arguments forwarded to the base class.
        returns:
          type: DigikeyScraper
          desc: A configured scraper instance.
        ---
        """
        super().__init__(self._DATASET_ID, bearer_token, **kw)

    def collect_by_url(self, urls: Sequence[str]) -> str:
        """
        ---
        endpoint: collect_by_url
        desc: Scrape specific Digi-Key product pages.
        params:
          urls:
            type: list[str]
            desc: Full product-detail URLs.
        returns:
          type: str
          desc: snapshot_id; poll until ready to retrieve `list[dict]` rows.
        example: |
          snap = scraper.collect_by_url([
            "https://www.digikey.com/en/products/detail/STMicroelectronics/STM32F407VGT6/2747117",
            "https://www.digikey.com/en/products/detail/Texas-Instruments/TPS7A4901PWP/8280491"
          ])
        ---
        """
        payload = [{"url": u} for u in urls]
        return self._trigger(payload, dataset_id=self._DATASET_ID)

    def discover_by_category(self, category_urls: Sequence[str]) -> str:
        """
        ---
        endpoint: discover_by_category
        desc: >
          Crawl Digi-Key category pages and return links to *new* parts
          (Bright Data’s `discover_new` semantics).
        params:
          category_urls:
            type: list[str]
            desc: Full category-page URLs.
        returns:
          type: str
          desc: snapshot_id; poll until ready to retrieve `list[dict]` rows.
        example: |
          snap = scraper.discover_by_category([
            "https://www.digikey.com/en/products/filter/resistors/general-purpose-fixed/04"
          ])
        ---
        """
        payload = [{"category_url": url} for url in category_urls]
        return self._trigger(
            payload,
            dataset_id=self._DATASET_ID,
            extra_params={"type": "discover_new", "discover_by": "category"},
        )


