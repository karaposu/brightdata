#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/linkedin/tests.py
#
# Smoke-test for brightdata.ready_scrapers.linkedin.LinkedInScraper
#   ▸ no dataset-IDs needed – the scraper owns them internally
#   ▸ every endpoint returns a snapshot-id (engine forces async mode)
#   ▸ we block with scraper.poll_until_ready()
#
# Run with:
#     python -m brightdata.ready_scrapers.linkedin.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
from dotenv import load_dotenv

from brightdata.ready_scrapers.linkedin import LinkedInScraper
from brightdata.utils import show_scrape_results   # unified pretty-printer

# ─────────────────────────── credentials ───────────────────────────
load_dotenv()
if not os.getenv("BRIGHTDATA_TOKEN"):
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")

# ─────────────────────────────  main  ──────────────────────────────
def main() -> None:
    scraper = LinkedInScraper()           # token from env
    
    # 1. PEOPLE ▸ collect_by_url --------------------------------------------
    people_urls = ["https://www.linkedin.com/in/enes-kuzucu/"]
    sid = scraper.people_profiles__collect_by_url(people_urls)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("people_profiles__collect_by_url", res)

    # 2. PEOPLE ▸ discover_by_name ------------------------------------------
    queries = [
        {"first_name": "Enes", "last_name": "Kuzucu"}
    ]
    sid = scraper.people_profiles__discover_by_name(queries)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("people_profiles__discover_by_name", res)

    # 3. COMPANY ▸ collect_by_url -------------------------------------------
    company_urls = ["https://www.linkedin.com/company/bright-data/"]
    sid = scraper.company_information__collect_by_url(company_urls)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("company_information__collect_by_url", res)

    # 4. JOBS ▸ collect_by_url ----------------------------------------------
    job_urls = ["https://www.linkedin.com/jobs/view/4231516747/"]
    sid = scraper.job_listing_information__collect_by_url(job_urls)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("job_listing_information__collect_by_url", res)

    # 5. JOBS ▸ discover_by_keyword -----------------------------------------
    queries = [{
        "location": "Paris",
        "keyword":  "product manager",
        "country":  "FR",
    }]
    sid = scraper.job_listing_information__discover_by_keyword(queries)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("job_listing_information__discover_by_keyword", res)

    # 6. SMART ROUTER ▸ collect_by_url() ------------------------------------
    mixed = [
        "https://www.linkedin.com/in/enes-kuzucu/",
        "https://www.linkedin.com/company/bright-data/",
        "https://www.linkedin.com/jobs/view/4231516747/",
    ]
    sid_map = scraper.collect_by_url(mixed)
    for kind, sid in sid_map.items():
        res = scraper.poll_until_ready(sid)
        show_scrape_results(f"collect_by_url → {kind}", res)


if __name__ == "__main__":
    main()
