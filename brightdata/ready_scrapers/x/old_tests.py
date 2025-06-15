#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/x/tests.py
#
# Smoke‐test for brightdata.ready_scrapers.x.XScraper
# ─────────────────────────────────────────────────────────────

import os
import sys
from dotenv import load_dotenv

from brightdata.ready_scrapers.x import XScraper
from brightdata.utils import poll_until_ready_and_show

# ─────────────────────────────────────────────────────────────
# 0. Credentials
# ─────────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("BRIGHTDATA_TOKEN")
if not TOKEN:
    sys.exit("Set BRIGHTDATA_TOKEN environment variable (or in .env)")

def main():
    scraper = XScraper()  # reads token from env

    # ─────────────────────────────────────────────────────────
    # 1. POSTS ▸ collect_by_url
    # ─────────────────────────────────────────────────────────
    tweet_urls = [
        "https://x.com/FabrizioRomano/status/1683559267524136962",
        "https://x.com/CNN/status/1796673270344810776",
    ]
    snap = scraper.posts__collect_by_url(tweet_urls)
    poll_until_ready_and_show(scraper, "posts__collect_by_url", snap)

    # ─────────────────────────────────────────────────────────
    # 2. POSTS ▸ discover_by_profile_url
    # ─────────────────────────────────────────────────────────
    queries = [
        {
            "url": "https://x.com/elonmusk",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
        },
        {
            "url": "https://x.com/cnn",
            "start_date": "",
            "end_date": "",
        },
    ]
    snap = scraper.posts__discover_by_profile_url(queries)
    poll_until_ready_and_show(scraper, "posts__discover_by_profile_url", snap)

    # ─────────────────────────────────────────────────────────
    # 3. PROFILES ▸ collect_by_url
    # ─────────────────────────────────────────────────────────
    profiles = [
        "https://x.com/elonmusk",
        "https://x.com/BillGates",
    ]
    snap = scraper.profiles__collect_by_url(profiles, max_posts=5)
    poll_until_ready_and_show(scraper, "profiles__collect_by_url", snap)

if __name__ == "__main__":
    main()
