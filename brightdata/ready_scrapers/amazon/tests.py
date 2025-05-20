#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/amazon/tests.py
#
# Smoke-test for brightdata.ready_scrapers.amazon.AmazonScraper
#   ▸ no dataset-IDs needed – the scraper holds them internally
#   ▸ every endpoint is forced to run *asynchronously*
#
# run with:
#   python -m brightdata.ready_scrapers.amazon.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
import time
from pprint import pprint
from dotenv import load_dotenv

from brightdata.ready_scrapers.amazon import AmazonScraper
from brightdata.base_specialized_scraper import ScrapeResult
from brightdata.utils import poll_until_ready, poll_until_ready_and_show


# ─────────────────────────────────────────────────────────────
# 0.  credentials
# ─────────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("BRIGHTDATA_TOKEN")
if not TOKEN:
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")


def main():
    
    ## ─────────────────────────────────────────────────────────────
    # 1.  initialise one scraper instance
    # ─────────────────────────────────────────────────────────────
    scraper = AmazonScraper()
    
    # ─────────────────────────────────────────────────────────────
    # 2.  PRODUCTS ▸ COLLECT BY URL
    # ─────────────────────────────────────────────────────────────
    urls = [
        "https://www.amazon.com/dp/B0CRMZHDG8",
        "https://www.amazon.com/dp/B07PZF3QS3",
    ]
    snap = scraper.products__collect_by_url(urls, zipcodes=["94107", ""])
    poll_until_ready_and_show(scraper,"products__collect_by_url", snap)

    # ─────────────────────────────────────────────────────────────
    # 3.  PRODUCTS ▸ DISCOVER BY KEYWORD
    # ─────────────────────────────────────────────────────────────
    snap = scraper.products__discover_by_keyword(["dog toys", "home decor"])
    poll_until_ready_and_show(scraper,"products__discover_by_keyword", snap)

    # ─────────────────────────────────────────────────────────────
    # 4.  PRODUCTS ▸ DISCOVER BY CATEGORY URL
    # ─────────────────────────────────────────────────────────────
    cat_urls = [
        "https://www.amazon.com/s?i=luggage-intl-ship",
        "https://www.amazon.com/s?i=arts-crafts-intl-ship",
    ]
    snap = scraper.products__discover_by_category_url(
        cat_urls,
        sorts=["Best Sellers", ""],
        zipcodes=["", ""],
    )

    poll_until_ready_and_show(scraper,"products__discover_by_category_url", snap)

    # ─────────────────────────────────────────────────────────────
    # 5.  SEARCH SERP ▸ COLLECT BY URL
    # ─────────────────────────────────────────────────────────────
    search_urls = [
        "https://www.amazon.de/s?k=PS5",
        "https://www.amazon.es/s?k=car+cleaning+kit",
    ]
    snap = scraper.products_search__collect_by_url(
        search_urls,
        pages=[ 1, 1],        # walk two pages for the Spanish site
    )
    poll_until_ready_and_show(scraper,"products_search__collect_by_url", snap)

    # ─────────────────────────────────────────────────────────────
    # 6.  SMART ROUTER  ▸  collect_by_url()
    # ─────────────────────────────────────────────────────────────
    mixed_urls = [
        "https://www.amazon.com/dp/B0CRMZHDG8",          # product
        "https://www.amazon.com/s?k=headphones",         # search
    ]
    snap_map = scraper.collect_by_url(mixed_urls)
    for bucket, sid in snap_map.items():
        poll_until_ready_and_show(f"collect_by_url ▸ {bucket}", sid)



if __name__ == "__main__":
    main()