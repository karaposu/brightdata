import asyncio
from brightdata.ready_scrapers.amazon import AmazonScraper
from brightdata.utils.async_poll import  fetch_snapshots_async 

from dotenv import load_dotenv
import os
import sys

# run with:
#   python -m brightdata.ready_scrapers.amazon.async_tests
# ─────────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("BRIGHTDATA_TOKEN")
if not TOKEN:
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")


def main():

    scraper = AmazonScraper(bearer_token=TOKEN)

    # trigger 300 keyword-discover jobs (returns list[str] snapshot_ids)
    # ─────────────────────────────────────────────────────────────
    # 2.  example keywords (10 items)
    # ─────────────────────────────────────────────────────────────
    keywords = [
        "dog toys",
        "home decor",
        "wireless earbuds",
        "gaming chair",
        "coffee maker",
        "yoga mat",
        "laptop stand",
        "smart watch",
        "water bottle",
        "noise cancelling headphones",
    ]

    # ─────────────────────────────────────────────────────────────
    # 3.  trigger one job per keyword
    # ─────────────────────────────────────────────────────────────
    # each call returns a snapshot_id (string)
    snap_ids = [
        scraper.discover_by_keyword([kw])
        for kw in keywords
    ]

    # poll them in parallel
    results = asyncio.run(fetch_snapshots_async(scraper, snap_ids, poll=15))

    success = [r for r in results if r.status == "ready"]
    failed  = [r for r in results if r.status != "ready"]

    print("ready :", len(success))
    print("failed:", len(failed))



if __name__ == "__main__":
    main()