#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/scrapers/digikey/tests.py
#
# Smoke-test for brightdata.scrapers.digikey.DigikeyScraper
#
# Run with:
#     python -m brightdata.scrapers.digikey.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
from dotenv import load_dotenv

from brightdata.webscraper_api.scrapers.digikey import DigikeyScraper
from brightdata.utils import show_scrape_results   # ← unified pretty-printer

# ───────────────────────── credentials ───────────────────────
load_dotenv()
if not os.getenv("BRIGHTDATA_TOKEN"):
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")

# ───────────────────────── main test ─────────────────────────
def main() -> None:
    scraper = DigikeyScraper()          # token from env
    
    # 1. COLLECT BY URL ------------------------------------------------------
    product_url_sample =  "https://www.digikey.com/en/products/detail/excelsys-advanced-energy/CX10S-BHDHCC-P-A-DK00000/13287513"
      
    sid  = scraper.collect_by_url(product_url_sample)
    res  = scraper.poll_until_ready(sid)
    show_scrape_results("collect_by_url", res)
     
    # 2. DISCOVER BY CATEGORY -----------------------------------------------
    cat_urls = [
        "https://www.digikey.co.il/en/products/filter/anti-static-esd-bags-"
        "materials/605?s=N4IgjCBcoLQExVAYygFwE4FcCmAaEA9lANogCsIAugL74wCciIKk"
        "GO%2BRkpEN11QA",
        "https://www.digikey.co.il/en/products/filter/batteries-non-"
        "rechargeable-primary/90?s=N4IgjCBcoLQExVAYygFwE4FcCmAaEA9lANogCsIAugL"
        "74wCciIKkGO%2BRkpEN11QA",
    ]
    sid  = scraper.discover_by_category(cat_urls)
    res  = scraper.poll_until_ready(sid, timeout=1_000)
    show_scrape_results("discover_by_category", res)


if __name__ == "__main__":
    main()
