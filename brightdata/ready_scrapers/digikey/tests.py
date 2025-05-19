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
from pprint import pprint
from dotenv import load_dotenv

from brightdata.ready_scrapers.digikey import DigikeyScraper
from brightdata.base_specialized_scraper import ScrapeResult

# ─────────────────────────────────────────────────────────────
# 0. credentials
# ─────────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("BRIGHTDATA_TOKEN")
if not TOKEN:
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")



def main():

    scraper = DigikeyScraper(bearer_token=TOKEN)

    # ─────────────────────────────────────────────────────────────
    # helper – poll Bright Data until snapshot is ready
    # ─────────────────────────────────────────────────────────────
    def poll_until_ready(
        snapshot_id: str,
        poll: int = 10,
        timeout: int = 600,
    ) -> ScrapeResult:
        start = time.time()
        attempt = 0
        while True:
            attempt += 1
            res: ScrapeResult = scraper.get_data(snapshot_id)
            elapsed = int(time.time() - start)
            print(f"[#{attempt:<2} | +{elapsed:>4}s]  {res.status}")

            if res.status in {"ready", "error"}:
                return res
            if elapsed >= timeout:
                return ScrapeResult(False, "timeout",
                                    error=f"gave up after {timeout}s")
            time.sleep(poll)

    def show(label: str, snapshot_id: str):
        print(f"\n=== {label} ===  (snapshot: {snapshot_id})")
        res = poll_until_ready(snapshot_id, poll=10, timeout=600)
        if res.status == "ready":
            print(f"{label} ✓  received {len(res.data)} rows")
            pprint(res.data[:2])
        else:
            print(f"{label} ✗  {res.status} – {res.error or ''}")

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
    show("collect_by_url", snap)

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
    show("discover_by_category", snap)



if __name__ == "__main__":
    main()