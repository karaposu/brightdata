#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/scrapers/instagram/tests.py
#
# Smoke-test for brightdata.scrapers.instagram.InstagramScraper.
# All endpoints return a snapshot-ID (engine enforces async mode);
# we block with scraper.poll_until_ready().
#
# Run with:
#     python -m brightdata.scrapers.instagram.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
from dotenv import load_dotenv

from brightdata.webscraper_api.scrapers.instagram import InstagramScraper
from brightdata.utils import show_scrape_results

# ───────────────────────────── credentials ─────────────────────────────
load_dotenv()
if not os.getenv("BRIGHTDATA_TOKEN"):
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")

# ──────────────────────────────── main ─────────────────────────────────
def main() -> None:
    scraper = InstagramScraper()  # token from env

    # 1. profiles__collect_by_url
    profiles = ["https://www.instagram.com/leonardodicaprio/?hl=en"]
    sid = scraper.profiles__collect_by_url(profiles)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("profiles__collect_by_url", res)

    # 2. posts__collect_by_url
    posts = ["https://www.instagram.com/p/DHtYVbIJiv4/?hl=en"]
    sid = scraper.posts__collect_by_url(posts)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("posts__collect_by_url", res)

    # 3. posts__discover_by_url
    post_queries = [{
        "url": "https://www.instagram.com/p/DJpaR0nOrlf",
        "num_of_posts": 5,
        "start_date": "",
        "end_date": "",
        "post_type": "",
        "posts_to_not_include": []
    }]
    sid = scraper.posts__discover_by_url(post_queries)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("posts__discover_by_url", res)

    # 4. comments__collect_by_url
    comment_targets = [
        "https://www.instagram.com/cats_of_instagram/reel/C4GLo_eLO2e/"
    ]
    sid = scraper.comments__collect_by_url(comment_targets)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("comments__collect_by_url", res)

    # 5. reels__discover_by_url
    reel_queries = [{
        "url": "https://www.instagram.com/billieeilish",
        "num_of_posts": 20,
        "start_date": "",
        "end_date": ""
    }]
    sid = scraper.reels__discover_by_url(reel_queries)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("reels__discover_by_url", res)

    # 6. reels__discover_by_url_all_reels
    reel_all_queries = [{
        "url": "https://www.instagram.com/billieeilish",
        "num_of_posts": "",
        "start_date": "",
        "end_date": ""
    }]
    sid = scraper.reels__discover_by_url_all_reels(reel_all_queries)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("reels__discover_by_url_all_reels", res)


if __name__ == "__main__":
    main()
