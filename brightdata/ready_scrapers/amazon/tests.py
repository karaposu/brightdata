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
from brightdata.utils import poll_until_ready


# ─────────────────────────────────────────────────────────────
# 0.  credentials
# ─────────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("BRIGHTDATA_TOKEN")
if not TOKEN:
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")


def main():

    # single instance handles all Amazon endpoints
    scraper = AmazonScraper(bearer_token=TOKEN)

    # ─────────────────────────────────────────────────────────────
    # helper – poll Bright Data until the snapshot is ready
    # ─────────────────────────────────────────────────────────────
    # def poll_until_ready(
    #     snapshot_id: str,
    #     poll: int = 10,
    #     timeout: int = 600,
    # ) -> ScrapeResult:
    #     """
    #     Keep querying /progress until Bright Data marks the job ‘ready’, an
    #     error occurs, or *timeout* seconds elapse.  Never raises; always
    #     returns a ScrapeResult whose .status is one of:
    #         • ready      – .data holds the records list
    #         • error      – Bright Data reported a failure
    #         • timeout    – we gave up waiting
    #     """
    #     t0 = time.time()
    #     while time.time() - t0 < timeout:
    #         res: ScrapeResult = scraper.get_data(snapshot_id)
    #         if res.status in {"ready", "error"}:
    #             return res
    #         time.sleep(poll)
    #     return ScrapeResult(False, "timeout", error="poll_timeout")



    # def poll_until_ready(
    #     scraper,
    #     snapshot_id: str,
    #     *,
    #     poll: int = 10,        # seconds between checks
    #     timeout: int = 600,    # give up after this many seconds
    # ) -> ScrapeResult:
    #     """
    #     Poll Bright Data until the job is ready or we hit *timeout*.

    #     Console log on every iteration:   [#3 | +31s]  not_ready
    #     Returns a ScrapeResult; never raises.
    #     """
    #     start = time.time()
    #     attempt = 0

    #     while True:
    #         attempt += 1
    #         res: ScrapeResult = scraper.get_data(snapshot_id)

    #         elapsed = int(time.time() - start)
    #         print(f"[#{attempt:<2} | +{elapsed:>4}s]  {res.status}")

    #         # finished or failed
    #         if res.status in {"ready", "error"}:
    #             return res

    #         # timeout?
    #         if elapsed >= timeout:
    #             return ScrapeResult(
    #                 success=False,
    #                 status="timeout",
    #                 error=f"gave up after {timeout}s",
    #                 data=None,
    #             )

    #         time.sleep(poll)

    def show(label: str, snap_id: str):
        print(f"\n=== {label} ===  (snapshot: {snap_id})")
        res = poll_until_ready(scraper, snap_id, poll=10, timeout=600)

        if res.status == "ready":
            print(f"{label} ✓  received {len(res.data)} rows")
            pprint(res.data[:2])
        else:
            print(f"{label} ✗  {res.status} – {res.error or ''}")

    # ─────────────────────────────────────────────────────────────
    # 1.  COLLECT BY URL
    # ─────────────────────────────────────────────────────────────
    urls = [
        "https://www.amazon.com/dp/B0CRMZHDG8",
        "https://www.amazon.com/dp/B07PZF3QS3",
    ]
    snap = scraper.collect_by_url(urls, ["94107", ""])
    show("collect_by_url", snap)

    # ─────────────────────────────────────────────────────────────
    # 2.  DISCOVER ▸ keyword
    # ─────────────────────────────────────────────────────────────
    snap = scraper.discover_by_keyword(["dog toys", "home decor"])
    show("discover_by_keyword", snap)




    # ─────────────────────────────────────────────────────────────
    # 3.  DISCOVER ▸ category
    # ─────────────────────────────────────────────────────────────
    cat_urls = [
        "https://www.amazon.com/s?i=luggage-intl-ship",
        "https://www.amazon.com/s?i=arts-crafts-intl-ship",
    ]
    snap = scraper.discover_by_category(cat_urls, ["Best Sellers", ""])
    show("discover_by_category", snap)

    # ─────────────────────────────────────────────────────────────
    # 4.  SEARCH PRODUCTS
    # ─────────────────────────────────────────────────────────────
    keywords = ["X-box", "PS5", "car cleaning kit"]
    domains  = ["https://www.amazon.com",
                "https://www.amazon.de",
                "https://www.amazon.es"]
    pages    = [1, 1, 12]
    snap = scraper.search_products(keywords, domains, pages)
    show("search_products", snap)




if __name__ == "__main__":
    main()