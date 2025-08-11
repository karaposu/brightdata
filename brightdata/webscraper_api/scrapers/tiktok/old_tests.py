#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/tiktok/tests.py
#
# Smoke‐test for brightdata.ready_scrapers.tiktok.TikTokScraper
# ─────────────────────────────────────────────────────────────

import os
import sys
from dotenv import load_dotenv
from brightdata.ready_scrapers.tiktok import TikTokScraper
from brightdata.utils import poll_until_ready_and_show

# ─────────────────────────────────────────────────────────────
# 0.  credentials
# ─────────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("BRIGHTDATA_TOKEN")
if not TOKEN:
    sys.exit("Set BRIGHTDATA_TOKEN in your environment or .env")

def main():
    scraper = TikTokScraper()  # reads token from env

    # ─────────────────────────────────────────────────────────
    # 1.  PROFILES ▸ collect_by_url
    # ─────────────────────────────────────────────────────────
    profiles = [
        "https://www.tiktok.com/@fofimdmell",
        "https://www.tiktok.com/@s_o_h_e_l_46",
    ]
    snap = scraper.profiles__collect_by_url(profiles)
    poll_until_ready_and_show(scraper, "profiles__collect_by_url", snap)

    # ─────────────────────────────────────────────────────────
    # 2.  PROFILES ▸ discover_by_search_url
    # ─────────────────────────────────────────────────────────
    queries = [
        {"search_url": "https://www.tiktok.com/explore?lang=en", "country": "US"},
        {"search_url": "https://www.tiktok.com/search?lang=en&q=music&t=1685628060000", "country": "FR"},
    ]
    snap = scraper.profiles__discover_by_search_url(queries)
    poll_until_ready_and_show(scraper, "profiles__discover_by_search_url", snap)

    # ─────────────────────────────────────────────────────────
    # 3.  POSTS ▸ collect_by_url (fast API)
    # ─────────────────────────────────────────────────────────
    posts = [
        "https://www.tiktok.com/@heymrcat/video/7216019547806092550",
        "https://www.tiktok.com/@mmeowmmia/video/7077929908365823237",
    ]
    snap = scraper.posts__collect_by_url(posts)
    poll_until_ready_and_show(scraper, "posts__collect_by_url", snap)

    # ─────────────────────────────────────────────────────────
    # 4.  POSTS ▸ discover_by_keyword
    # ─────────────────────────────────────────────────────────
    snap = scraper.posts__discover_by_keyword(["#funnydogs", "dance"])
    poll_until_ready_and_show(scraper, "posts__discover_by_keyword", snap)

    # ─────────────────────────────────────────────────────────
    # 5.  POSTS ▸ discover_by_profile_url
    # ─────────────────────────────────────────────────────────
    snap = scraper.posts__discover_by_profile_url([
        {
            "url": "https://www.tiktok.com/@babyariel",
            "num_of_posts": 5,
            "posts_to_not_include": [],
            "what_to_collect": "Posts & Reposts",
            "start_date": "",
            "end_date": "",
            "post_type": "",
            "country": ""
        }
    ])
    poll_until_ready_and_show(scraper, "posts__discover_by_profile_url", snap)

    # ─────────────────────────────────────────────────────────
    # 6.  POSTS ▸ discover_by_url (feed / discover endpoint)
    # ─────────────────────────────────────────────────────────
    snap = scraper.posts__discover_by_url([{"url": "https://www.tiktok.com/discover/dog"}])
    poll_until_ready_and_show(scraper, "posts__discover_by_url", snap)

    # ─────────────────────────────────────────────────────────
    # 7.  POSTS (fast‐API “by URL” family)
    # ─────────────────────────────────────────────────────────
    snap = scraper.posts_by_url_fast_api__collect_by_url([
        "https://www.tiktok.com/discover/dog1",
        "https://www.tiktok.com/channel/anime",
        "https://www.tiktok.com/music/Nirvana-Steeve-West-Remix-7166220356133324802",
        "https://www.tiktok.com/explore?lang=en",
    ])
    poll_until_ready_and_show(scraper, "posts_by_url_fast_api__collect_by_url", snap)

    snap = scraper.posts_by_profile_fast_api__collect_by_url([
        "https://www.tiktok.com/@bbc",
        "https://www.tiktok.com/@portalotempo",
    ])
    poll_until_ready_and_show(scraper, "posts_by_profile_fast_api__collect_by_url", snap)

    snap = scraper.posts_by_search_url_fast_api__collect_by_url([
        {"url": "https://www.tiktok.com/search?lang=en&q=cats&t=1740648955524", "country": ""},
        {"url": "https://www.tiktok.com/search?lang=en&q=dogs&t=1740648968034", "num_of_posts": 10, "country": "US"},
    ])
    poll_until_ready_and_show(scraper, "posts_by_search_url_fast_api__collect_by_url", snap)

    # ─────────────────────────────────────────────────────────
    # 8.  COMMENTS ▸ collect_by_url
    # ─────────────────────────────────────────────────────────
    snap = scraper.comments__collect_by_url(posts)
    poll_until_ready_and_show(scraper, "comments__collect_by_url", snap)

    # ─────────────────────────────────────────────────────────
    # 9.  DISPATCHER ▸ collect_by_url()
    # ─────────────────────────────────────────────────────────
    mixed = profiles + posts
    snap_map = scraper.collect_by_url(mixed, include_comments=False)
    for bucket, sid in snap_map.items():
        poll_until_ready_and_show(scraper, f"dispatch: {bucket}", sid)

    # now with comments
    snap_map = scraper.collect_by_url(posts, include_comments=True)
    for bucket, sid in snap_map.items():
        poll_until_ready_and_show(scraper, f"dispatch (inc comments): {bucket}", sid)


if __name__ == "__main__":
    main()
