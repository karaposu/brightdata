#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/x/tests.py
#
# Smoke-test for brightdata.ready_scrapers.x.XScraper
#   ▸ every call returns a snapshot-ID (engine async-mode)
#   ▸ we block with scraper.poll_until_ready(), then render via
#     brightdata.utils.show_scrape_results
#
# Run with:
#   python -m brightdata.ready_scrapers.x.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
from dotenv import load_dotenv

from brightdata.ready_scrapers.x import XScraper
from brightdata.utils import show_scrape_results

# ───────────────────────── credentials ────────────────────────
load_dotenv()
if not os.getenv("BRIGHTDATA_TOKEN"):
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")

# ─────────────────────────── main ─────────────────────────────
def main() -> None:
    scraper = XScraper()                      # token from env

    # 1. posts__collect_by_url -------------------------------------------
    tweet_urls = [
        "https://x.com/FabrizioRomano/status/1683559267524136962",
        "https://x.com/CNN/status/1796673270344810776",
    ]
    sid = scraper.posts__collect_by_url(tweet_urls)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("posts__collect_by_url", res)

    # 2. posts__discover_by_profile_url ----------------------------------
    queries = [
        {
            "url": "https://x.com/elonmusk",
            "start_date": "2023-01-01",
            "end_date":   "2023-12-31",
        },
        {
            "url": "https://x.com/CNN",
            "start_date": "",
            "end_date":   "",
        },
    ]
    sid = scraper.posts__discover_by_profile_url(queries)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("posts__discover_by_profile_url", res)

    # 3. profiles__collect_by_url ----------------------------------------
    profiles = [
        "https://x.com/elonmusk",
        "https://x.com/BillGates",
    ]
    sid = scraper.profiles__collect_by_url(profiles, max_posts=5)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("profiles__collect_by_url", res)


if __name__ == "__main__":
    main()
