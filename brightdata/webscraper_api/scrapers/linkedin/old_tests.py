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
#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/linkedin/tests.py
#
# Smoke-test for brightdata.ready_scrapers.linkedin.LinkedInScraper
#   ▸ no dataset-IDs needed – the scraper holds them internally
#   ▸ every endpoint runs in async mode → returns snapshot-ids
#
# Run with:
#   python -m brightdata.ready_scrapers.linkedin.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
from dotenv import load_dotenv

from brightdata.ready_scrapers.linkedin import LinkedInScraper
from brightdata.utils import poll_until_ready_and_show

def main():
    # ─────────────────────────────────────────────────────────
    # 0.  credentials
    # ─────────────────────────────────────────────────────────
    load_dotenv()
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        sys.exit("Set BRIGHTDATA_TOKEN environment variable first")
    
    # ─────────────────────────────────────────────────────────
    # 1.  INSTANTIATE
    # ─────────────────────────────────────────────────────────
    scraper = LinkedInScraper()   # token read from env

    # ─────────────────────────────────────────────────────────
    # 2.  PROFILES ▸ collect_by_url
    # ─────────────────────────────────────────────────────────
    people_urls = ["https://www.linkedin.com/in/enes-kuzucu/"]
    snap = scraper.people_profiles__collect_by_url(people_urls)
    poll_until_ready_and_show(scraper, "people_profiles__collect_by_url", snap)

    # ─────────────────────────────────────────────────────────
    # 3.  PROFILES ▸ discover_by_name
    # ─────────────────────────────────────────────────────────
    snap = scraper.people_profiles__discover_by_name(["Enes Kuzucu"])
    poll_until_ready_and_show(scraper, "people_profiles__discover_by_name", snap)

    # ─────────────────────────────────────────────────────────
    # 4.  COMPANY ▸ collect_by_url
    # ─────────────────────────────────────────────────────────
    company_urls = ["https://www.linkedin.com/company/bright-data/"]
    snap = scraper.company_information__collect_by_url(company_urls)
    poll_until_ready_and_show(scraper, "company_information__collect_by_url", snap)

    # ─────────────────────────────────────────────────────────
    # 5.  JOBS ▸ collect_by_url
    # ─────────────────────────────────────────────────────────
    job_urls = ["https://www.linkedin.com/jobs/view/4231516747/"]
    snap = scraper.job_listing_information__collect_by_url(job_urls)
    poll_until_ready_and_show(scraper, "job_listing_information__collect_by_url", snap)

    # ─────────────────────────────────────────────────────────
    # 6.  JOBS ▸ discover_by_keyword
    # ─────────────────────────────────────────────────────────
    queries = [
        {
            "location": "Paris",
            "keyword":  "product manager",
            "country":  "FR",
        }
    ]
    snap = scraper.job_listing_information__discover_by_keyword(queries)
    poll_until_ready_and_show(
        scraper,
        "job_listing_information__discover_by_keyword",
        snap
    )

    # ─────────────────────────────────────────────────────────
    # 7.  SMART ROUTER ▸ collect_by_url()
    # ─────────────────────────────────────────────────────────
    mixed = [
        "https://www.linkedin.com/in/enes-kuzucu/",
        "https://www.linkedin.com/company/bright-data/",
        "https://www.linkedin.com/jobs/view/4231516747/",
    ]
    snap_map = scraper.collect_by_url(mixed)
    for kind, sid in snap_map.items():
        poll_until_ready_and_show(scraper, f"collect_by_url → {kind}", sid)


if __name__ == "__main__":
    main()
