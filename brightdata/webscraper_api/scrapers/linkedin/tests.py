#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/scrapers/linkedin/tests.py
#
# Smoke-test for brightdata.scrapers.linkedin.LinkedInScraper
#   ▸ no dataset-IDs needed – the scraper owns them internally
#   ▸ collect_by_url now accepts exactly one URL at a time
#   ▸ we block with scraper.poll_until_ready()
#
# Run with:
#     python -m brightdata.scrapers.linkedin.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
from dotenv import load_dotenv

from brightdata.webscraper_api.scrapers.linkedin import LinkedInScraper
from brightdata.utils import show_scrape_results   # unified pretty-printer

# ─────────────────────────── credentials ───────────────────────────
load_dotenv()
if not os.getenv("BRIGHTDATA_TOKEN"):
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")

# ─────────────────────────────  main  ──────────────────────────────
def main() -> None:
    scraper = LinkedInScraper()  # token from env
    
    # 1. PEOPLE ▸ collect_by_url ----------------------------------------
    people_url = "https://www.linkedin.com/in/enes-kuzucu/"
    sid = scraper.collect_by_url(people_url)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("people_profiles__collect_by_url", res)

    

    # 3. COMPANY ▸ collect_by_url --------------------------------------
    company_url = "https://www.linkedin.com/company/bright-data/"
    sid = scraper.collect_by_url(company_url)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("company_information__collect_by_url", res)

    # 4. JOBS ▸ collect_by_url -----------------------------------------
    job_url = "https://www.linkedin.com/jobs/view/4231516747/"
    sid = scraper.collect_by_url(job_url)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("job_listing_information__collect_by_url", res)


    # 2. PEOPLE ▸ discover_by_name -------------------------------------
    queries = [{"first_name": "Enes", "last_name": "Kuzucu"}]
    sid = scraper.people_profiles__discover_by_name(queries)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("people_profiles__discover_by_name", res)

    # 5. JOBS ▸ discover_by_keyword -----------------------------------
    job_queries = [{
        "location": "Paris",
        "keyword":  "product manager",
        "country":  "FR",
    }]
    sid = scraper.job_listing_information__discover_by_keyword(job_queries)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("job_listing_information__discover_by_keyword", res)

    # 6. SMART LOOP ▸ collect_by_url() over mixed URLs ---------------
    mixed_urls = [
        people_url,
        company_url,
        job_url,
    ]
    for url in mixed_urls:
        sid = scraper.collect_by_url(url)
        res = scraper.poll_until_ready(sid)
        show_scrape_results(f"collect_by_url → {url}", res)


if __name__ == "__main__":
    main()
