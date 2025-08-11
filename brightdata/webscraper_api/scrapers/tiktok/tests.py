#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/scrapers/tiktok/tests.py
#
# Smoke-test for brightdata.scrapers.tiktok.TikTokScraper
# ─────────────────────────────────────────────────────────────

import os
import sys
from dotenv import load_dotenv

from brightdata.webscraper_api.scrapers.tiktok import TikTokScraper
from brightdata.models import ScrapeResult
from brightdata.utils import show_scrape_results

# ─────────────────────────────────────────────────────────────
# 0.  credentials
# ─────────────────────────────────────────────────────────────
load_dotenv()
if not os.getenv("BRIGHTDATA_TOKEN"):
    sys.exit("Set BRIGHTDATA_TOKEN in your environment or .env")

# ─────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────
def _display(label: str, res_or_map):
    """Handle both single and multi-bucket returns."""
    if isinstance(res_or_map, ScrapeResult):
        show_scrape_results(label, res_or_map)
    else:                                    # {bucket: ScrapeResult}
        for bucket, sub in res_or_map.items():
            show_scrape_results(f"{label}/{bucket}", sub)

# ─────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────
def main() -> None:
    scraper = TikTokScraper()            # token read from env

    # 1. PROFILES ▸ collect_by_url -----------------------------------------
    profiles = [
        "https://www.tiktok.com/@fofimdmell",
        "https://www.tiktok.com/@s_o_h_e_l_46",
    ]
    sid = scraper.profiles__collect_by_url(profiles)
    res = scraper.poll_until_ready(sid)
    _display("profiles__collect_by_url", res)

    # 2. PROFILES ▸ discover_by_search_url ---------------------------------
    queries = [
        {"search_url": "https://www.tiktok.com/explore?lang=en", "country": "US"},
        {"search_url": "https://www.tiktok.com/search?lang=en&q=music&t=1685628060000",
         "country": "FR"},
    ]
    sid = scraper.profiles__discover_by_search_url(queries)
    res = scraper.poll_until_ready(sid)
    _display("profiles__discover_by_search_url", res)

    # 3. POSTS ▸ collect_by_url (fast API) ---------------------------------
    posts = [
        "https://www.tiktok.com/@heymrcat/video/7216019547806092550",
        "https://www.tiktok.com/@mmeowmmia/video/7077929908365823237",
    ]
    sid = scraper.posts__collect_by_url(posts)
    res = scraper.poll_until_ready(sid)
    _display("posts__collect_by_url", res)

    # 4. POSTS ▸ discover_by_keyword ---------------------------------------
    sid = scraper.posts__discover_by_keyword(["#funnydogs", "dance"])
    res = scraper.poll_until_ready(sid)
    _display("posts__discover_by_keyword", res)

    # 5. POSTS ▸ discover_by_profile_url -----------------------------------
    sid = scraper.posts__discover_by_profile_url([{
        "url": "https://www.tiktok.com/@babyariel",
        "num_of_posts": 5,
        "posts_to_not_include": [],
        "what_to_collect": "Posts & Reposts",
        "start_date": "",
        "end_date": "",
        "post_type": "",
        "country": ""
    }])
    res = scraper.poll_until_ready(sid)
    _display("posts__discover_by_profile_url", res)

    # 6. POSTS ▸ discover_by_url -------------------------------------------
    sid = scraper.posts__discover_by_url([{"url": "https://www.tiktok.com/discover/dog"}])
    res = scraper.poll_until_ready(sid)
    _display("posts__discover_by_url", res)

    # 7a. Fast-API ▸ posts_by_url_fast_api ---------------------------------
    sid = scraper.posts_by_url_fast_api__collect_by_url([
        "https://www.tiktok.com/discover/dog1",
        "https://www.tiktok.com/channel/anime",
        "https://www.tiktok.com/music/Nirvana-Steeve-West-Remix-7166220356133324802",
        "https://www.tiktok.com/explore?lang=en",
    ])
    res = scraper.poll_until_ready(sid)
    _display("posts_by_url_fast_api__collect_by_url", res)

    # 7b. Fast-API ▸ posts_by_profile_fast_api ------------------------------
    sid = scraper.posts_by_profile_fast_api__collect_by_url([
        "https://www.tiktok.com/@bbc",
        "https://www.tiktok.com/@portalotempo",
    ])
    res = scraper.poll_until_ready(sid)
    _display("posts_by_profile_fast_api__collect_by_url", res)

    # 7c. Fast-API ▸ posts_by_search_url_fast_api ---------------------------
    sid = scraper.posts_by_search_url_fast_api__collect_by_url([
        {"url": "https://www.tiktok.com/search?lang=en&q=cats&t=1740648955524",
         "country": ""},
        {"url": "https://www.tiktok.com/search?lang=en&q=dogs&t=1740648968034",
         "num_of_posts": 10, "country": "US"},
    ])
    res = scraper.poll_until_ready(sid)
    _display("posts_by_search_url_fast_api__collect_by_url", res)

    # 8. COMMENTS ▸ collect_by_url -----------------------------------------
    sid = scraper.comments__collect_by_url(posts)
    res = scraper.poll_until_ready(sid)
    _display("comments__collect_by_url", res)

    # 9a. Smart router ▸ collect_by_url  (posts & profiles) -----------------
    mixed = profiles + posts
    sid_map = scraper.collect_by_url(mixed, include_comments=False)
    res_map = {k: scraper.poll_until_ready(v) for k, v in sid_map.items()}
    _display("collect_by_url", res_map)

    # 9b. Smart router with comments ---------------------------------------
    sid_map = scraper.collect_by_url(posts, include_comments=True)
    res_map = {k: scraper.poll_until_ready(v) for k, v in sid_map.items()}
    _display("collect_by_url (incl. comments)", res_map)


if __name__ == "__main__":
    main()
