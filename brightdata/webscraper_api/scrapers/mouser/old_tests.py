#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/mouser/tests.py
#
# Smoke-test for brightdata.ready_scrapers.mouser.MouserScraper
#   ▸ all calls run in async mode → return snapshot-ids
#   ▸ use poll_until_ready_and_show to block until results arrive
#
# Run with:
#   python -m brightdata.ready_scrapers.mouser.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
from dotenv import load_dotenv

from brightdata.ready_scrapers.mouser import MouserScraper
from brightdata.utils import poll_until_ready_and_show

def main():
    # ─────────────────────────────────────────────────────────
    # 0.  credentials
    # ─────────────────────────────────────────────────────────
    load_dotenv()
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        sys.exit("Set BRIGHTDATA_TOKEN environment variable first")

    # ─────────────────────────────────────────────────────────
    # 1.  instantiate scraper
    # ─────────────────────────────────────────────────────────
    scraper = MouserScraper()   # reads token from env

    # ─────────────────────────────────────────────────────────
    # 2.  COLLECT BY URL
    # ─────────────────────────────────────────────────────────
    product_urls = [
        "https://www.mouser.com/ProductDetail/Diodes-Incorporated/DMN4035L-13?qs=EBDBlbfErPxf4bkLM3Jagg%3D%3D",
    ]
    snap = scraper.collect_by_url(product_urls)
    poll_until_ready_and_show(scraper, "collect_by_url", snap)

if __name__ == "__main__":
    main()
