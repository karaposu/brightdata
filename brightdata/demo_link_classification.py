# demo_link_classification.py


# python -m brightdata.demo_link_classification
import os, sys
from pprint import pprint
from dotenv import load_dotenv

from brightdata.registry import get_scraper_for
from brightdata.utils.poll import poll_until_ready

load_dotenv()
TOKEN = os.getenv("BRIGHTDATA_TOKEN") or sys.exit("Set BRIGHTDATA_TOKEN")

from brightdata.ready_scrapers.linkedin import LinkedInScraper
from brightdata.utils.poll import poll_until_ready

scraper = LinkedInScraper(bearer_token=TOKEN)

snapshot_ids = scraper.collect_by_url([
    "https://www.linkedin.com/in/enes-kuzucu/",
    "https://www.linkedin.com/company/105448508/",
    "https://www.linkedin.com/jobs/view/4231516747/",
])

people_rows  = poll_until_ready(scraper, snapshot_ids["people"]).data
company_rows = poll_until_ready(scraper, snapshot_ids["company"]).data
job_rows     = poll_until_ready(scraper, snapshot_ids["job"]).data



print("people_rows:", people_rows)
print(" ")
print(" ")

print("company_rows:", company_rows)

print(" ")
print(" ")

print("job_rows:", job_rows)