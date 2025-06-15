#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/mouser/tests.py
#
# Smoke-test for brightdata.ready_scrapers.mouser.MouserScraper
#   ▸ triggers a product-page scrape (sync path)
#   ▸ blocks with scraper.poll_until_ready()
#
# Run with:
#   python -m brightdata.ready_scrapers.mouser.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from brightdata.ready_scrapers.mouser import MouserScraper
from brightdata.models import ScrapeResult
from brightdata.utils import show_scrape_results   # pretty printer used by the Reddit test


def main() -> None:
    # ── credentials ───────────────────────────────────────────
    load_dotenv()
    if not os.getenv("BRIGHTDATA_TOKEN"):
        sys.exit("Set BRIGHTDATA_TOKEN environment variable first")

    # ── instantiate scraper ──────────────────────────────────
    scraper = MouserScraper()          # token is read from env var

    # ── COLLECT BY URL ───────────────────────────────────────
    product_urls = [
        "https://www.mouser.com/ProductDetail/Diodes-Incorporated/DMN4035L-13?qs=EBDBlbfErPxf4bkLM3Jagg%3D%3D",
    ]
    snapshot_id = scraper.collect_by_url(product_urls)
    result      = scraper.poll_until_ready(snapshot_id)
    
    show_scrape_results("collect_by_url", result)


if __name__ == "__main__":
    main()
