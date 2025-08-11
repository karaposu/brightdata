#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/scrapers/amazon/tests.py
#
# Smoke-test for brightdata.scrapers.amazon.AmazonScraper
#   ▸ no dataset-IDs needed – the scraper holds them internally
#   ▸ every endpoint runs in *async* mode (sync_mode=async)
#   ▸ we block with scraper.poll_until_ready()
#
# Run with:
#   python -m brightdata.webscraper_api.scrapers.amazon.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
from dotenv import load_dotenv

from brightdata.webscraper_api.scrapers.amazon import AmazonScraper
from brightdata.utils import show_scrape_results   # unified pretty-printer

# ─────────────────────────── credentials ───────────────────────────
load_dotenv()
if not os.getenv("BRIGHTDATA_TOKEN"):
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")

# ─────────────────────────────  main  ──────────────────────────────
def main() -> None:
    scraper = AmazonScraper()      # token from env

    # 1. SMART ROUTER  ▸  collect_by_url on each URL --------------------
    mixed_urls = [
        "https://www.amazon.com/dp/B0CRMZHDG8",  # product
        "https://www.amazon.com/s?k=headphones", # search
    ]
    for url in mixed_urls:
        sid = scraper.collect_by_url(url)
        if not sid:
            print(f"⚠ no handler for {url!r}")
            continue
        res = scraper.poll_until_ready(sid)
        show_scrape_results(f"collect_by_url → {url}", res)

    # 2. PRODUCTS ▸ COLLECT BY URL (batch) -----------------------------
    prod_urls = [
        "https://www.amazon.com/dp/B0CRMZHDG8",
        "https://www.amazon.com/dp/B07PZF3QS3",
    ]
    sid = scraper.products__collect_by_url(prod_urls, zipcodes=["94107", ""])
    res = scraper.poll_until_ready(sid)
    show_scrape_results("products__collect_by_url", res)

    # 3. PRODUCTS ▸ DISCOVER BY KEYWORD ------------------------------
    sid = scraper.products__discover_by_keyword(["dog toys", "home decor"])
    res = scraper.poll_until_ready(sid)
    show_scrape_results("products__discover_by_keyword", res)

    # 4. PRODUCTS ▸ DISCOVER BY CATEGORY URL -------------------------
    cat_urls = [
        "https://www.amazon.com/s?i=luggage-intl-ship",
        "https://www.amazon.com/s?i=arts-crafts-intl-ship",
    ]
    sid = scraper.products__discover_by_category_url(
        cat_urls,
        sorts=["Best Sellers", ""],
        zipcodes=["", ""],
    )
    res = scraper.poll_until_ready(sid)
    show_scrape_results("products__discover_by_category_url", res)

    # 5. SEARCH SERP ▸ COLLECT BY URL (batch) ------------------------
    search_urls = [
        "https://www.amazon.de/s?k=PS5",
        "https://www.amazon.es/s?k=car+cleaning+kit",
    ]
    sid = scraper.products_search__collect_by_url(
        search_urls,
        pages=[1, 1],
    )
    res = scraper.poll_until_ready(sid)
    show_scrape_results("products_search__collect_by_url", res)


if __name__ == "__main__":
    main()
