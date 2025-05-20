#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/instagram/tests.py
#
# Smoke-test for brightdata.ready_scrapers.instagram.InstagramScraper.
# All Bright-Data calls run **asynchronously** (sync_mode=async),
# so each endpoint first returns only a snapshot-id string.
#
# Run with:
#     python -m brightdata.ready_scrapers.instagram.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
import time

from dotenv import load_dotenv

from brightdata.ready_scrapers.instagram import InstagramScraper
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

    scraper = InstagramScraper(bearer_token=TOKEN)
    
    # collect_profiles_by_url
    # collect_posts_by_url
    # discover_posts_by_url
    # collect_comments_by_url
    # discover_reels_by_url
    # discover_reels_all_by_url
    
    # ─────────────────────────────────────────────────────────────
    # 1. profiles__collect_by_url
    # ─────────────────────────────────────────────────────────────
    sample_for_profiles__collect_by_url = [
        "https://www.instagram.com/leonardodicaprio/?hl=en",
    ]
    
    snap = scraper.profiles__collect_by_url(sample_for_profiles__collect_by_url)
    poll_until_ready_and_show(scraper, "profiles__collect_by_url", snap)
    
    # ─────────────────────────────────────────────────────────────
    # 2. posts__collect_by_url
    # ─────────────────────────────────────────────────────────────
    sample_for_posts__collect_by_url = [
        "https://www.instagram.com/p/DHtYVbIJiv4/?hl=en",
    ]
    snap = scraper.posts__collect_by_url(sample_for_posts__collect_by_url)
    poll_until_ready_and_show(scraper,"posts__collect_by_url", snap)



    # ─────────────────────────────────────────────────────────────
    # 3. posts__discover_by_url
    # ─────────────────────────────────────────────────────────────
    sample_for_posts__discover_by_url = [
        "https://www.instagram.com/p/DJpaR0nOrlf",
    ]
    snap = scraper.posts__discover_by_url(sample_for_posts__discover_by_url)
    poll_until_ready_and_show(scraper,"posts__discover_by_url", snap)


    # ─────────────────────────────────────────────────────────────
    # 4. comments__collect_by_url
    # ─────────────────────────────────────────────────────────────
    
    samples_for_comments__collect_by_url = [
        "https://www.instagram.com/cats_of_instagram/reel/C4GLo_eLO2e/",
    ]
    snap = scraper.comments__collect_by_url(samples_for_comments__collect_by_url)
    poll_until_ready_and_show(scraper,"comments__collect_by_url", snap)


    # ─────────────────────────────────────────────────────────────
    # 5. reels__discover_by_url
    # ─────────────────────────────────────────────────────────────
    
    sample_for_reels__discover_by_url = [
    {
        "url": "https://www.instagram.com/billieeilish",
        "num_of_posts": 20,
        "start_date": "",      # ""  ➜ no lower bound
        "end_date": ""         # ""  ➜ no upper bound
    }
    ]
    snap = scraper.reels__discover_by_url(sample_for_reels__discover_by_url)
    poll_until_ready_and_show(scraper,"reels__discover_by_url", snap)

    
    # ─────────────────────────────────────────────────────────────
    # 5. reels__discover_by_url_all_reels
    # ─────────────────────────────────────────────────────────────
    samples_for_reels__discover_by_url_all_reels = [
        "https://www.instagram.com/billieeilish",
    ]
    snap = scraper.reels__discover_by_url_all_reels(samples_for_reels__discover_by_url_all_reels)
    poll_until_ready_and_show(scraper,"reels__discover_by_url_all_reels", snap)






    






    






if __name__ == "__main__":
    main()