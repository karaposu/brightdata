#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/linkedin/tests.py
#
# Smoke-test for brightdata.ready_scrapers.linkedin.LinkedinScraper.
# All Bright-Data calls run **asynchronously** (sync_mode=async),
# so each endpoint first returns only a snapshot-id string.
#
# Run with:
#     python -m brightdata.ready_scrapers.linkedin.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
import time

from dotenv import load_dotenv

from brightdata.ready_scrapers.linkedin import LinkedInScraper
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



    # collect_people_by_url
    # discover_people_by_name
    # collect_company_by_url
    # collect_jobs_by_url
    # discover_jobs_by_keyword
    
    scraper = LinkedInScraper(bearer_token=TOKEN)

    sample_for__people_profiles__collect_by_url=[

       {"url":"https://www.linkedin.com/in/elad-moshe-05a90413/"}
    ]

    sample_for__people_profiles__discover_by_name=[
    
        {"first_name":"James","last_name":"Smith"}
    ]

    sample_for__company_information__collect_by_url=[
           {"url":"https://il.linkedin.com/company/ibm"},
	
    ]

    sample_for__jobs_by_url= [
    
       {"url":"https://www.linkedin.com/jobs/view/remote-typist-%E2%80%93-data-entry-specialist-work-from-home-at-cwa-group-4181034038?trk=public_jobs_topcard-title"},
    ]
    
    sample_for__jobs_by_keyword=[

    ]


    # collect_profiles_by_url
    # collect_posts_by_url
    # discover_posts_by_url
    # collect_comments_by_url
    # discover_reels_by_url
    # discover_reels_all_by_url
    
    # ─────────────────────────────────────────────────────────────
    # 1. collect_profiles_by_url
    # ─────────────────────────────────────────────────────────────
    profile_urls = [
        "https://www.instagram.com/leonardodicaprio/?hl=en",
    ]
    
    snap = scraper.collect_by_url(profile_urls)
    poll_until_ready_and_show(scraper, "collect_profiles_by_url", snap)
    
    # ─────────────────────────────────────────────────────────────
    # 2. collect_posts_by_url
    # ─────────────────────────────────────────────────────────────
    post_urls = [
        "https://www.instagram.com/p/DHtYVbIJiv4/?hl=en",
    ]
    snap = scraper.discover_by_category(post_urls)
    poll_until_ready_and_show(scraper,"collect_posts_by_url", snap)



    # ─────────────────────────────────────────────────────────────
    # 3. discover_posts_by_url
    # ─────────────────────────────────────────────────────────────
    discover_posts_urls = [
        "https://www.instagram.com/p/DJpaR0nOrlf",
    ]
    snap = scraper.discover_by_category(discover_posts_urls)
    poll_until_ready_and_show(scraper,"discover_posts_by_url", snap)


    # ─────────────────────────────────────────────────────────────
    # 4. collect_comments_by_url
    # ─────────────────────────────────────────────────────────────
    samples_for_collect_comments_by_urls = [
        "https://www.instagram.com/cats_of_instagram/reel/C4GLo_eLO2e/",
    ]
    snap = scraper.discover_by_category(samples_for_collect_comments_by_urls)
    poll_until_ready_and_show(scraper,"collect_comments_by_url", snap)



    # ─────────────────────────────────────────────────────────────
    # 5. discover_reels_by_url
    # ─────────────────────────────────────────────────────────────
    samples_for_discover_reels_by_url = [
        "https://www.instagram.com/espn",
    ]
    snap = scraper.discover_by_category(samples_for_discover_reels_by_url)
    poll_until_ready_and_show(scraper,"discover_reels_by_url", snap)


    # ─────────────────────────────────────────────────────────────
    # 5. discover_reels_all_by_url
    # ─────────────────────────────────────────────────────────────
    samples_for_discover_reels_all_by_url = [
        "https://www.instagram.com/billieeilish",
    ]
    snap = scraper.discover_by_category(samples_for_discover_reels_all_by_url)
    poll_until_ready_and_show(scraper,"discover_reels_all_by_url", snap)



    






    






if __name__ == "__main__":
    main()