#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/digikey/tests.py
#
# Smoke-test for brightdata.ready_scrapers.digikey.DigikeyScraper.
# All Bright-Data calls run **asynchronously** (sync_mode=async),
# so each endpoint first returns only a snapshot-id string.
#
# Run with:
#     python -m brightdata.ready_scrapers.digikey.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
import time

from dotenv import load_dotenv

from brightdata.ready_scrapers.digikey import DigikeyScraper
from brightdata.base_specialized_scraper import ScrapeResult
from brightdata.utils.poll import poll_until_ready_and_show 

# ─────────────────────────────────────────────────────────────
# 0. credentials
# ─────────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("BRIGHTDATA_TOKEN")
if not TOKEN:
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")



def main():
    
    scraper = DigikeyScraper()

    
    # ─────────────────────────────────────────────────────────────
    # 1. COLLECT BY URL
    # ─────────────────────────────────────────────────────────────
    product_urls = [
        "https://www.digikey.com/en/products/detail/excelsys-advanced-energy/"
        "CX10S-BHDHCC-P-A-DK00000/13287513",

        "https://www.digikey.com/en/products/detail/vishay-foil-resistors-"
        "division-of-vishay-precision-group/Y1453100R000F9L/4228045",
    ]
    snap = scraper.collect_by_url(product_urls)
    poll_until_ready_and_show(scraper, "collect_by_url", snap)
    
    # ─────────────────────────────────────────────────────────────
    # 2. DISCOVER BY CATEGORY
    # ─────────────────────────────────────────────────────────────
    cat_urls = [
        "https://www.digikey.co.il/en/products/filter/anti-static-esd-bags-"
        "materials/605?s=N4IgjCBcoLQExVAYygFwE4FcCmAaEA9lANogCsIAugL74wCciIKk"
        "GO%2BRkpEN11QA",
    
        "https://www.digikey.co.il/en/products/filter/batteries-non-"
        "rechargeable-primary/90?s=N4IgjCBcoLQExVAYygFwE4FcCmAaEA9lANogCsIAugL"
        "74wCciIKkGO%2BRkpEN11QA",
    ]
    snap = scraper.discover_by_category(cat_urls)
    poll_until_ready_and_show(scraper,"discover_by_category", snap, timeout= 1000)



if __name__ == "__main__":
    main()