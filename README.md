
brightdata 
==========

Unofficial **Python helper-SDK** for BrightData "Custom Web Scrapers"


``pip install brightdata``  →  one import away from grabbing JSON rows
from Amazon, Digi-Key, Mouser, LinkedIn, Tiktok, Youtube, Instagram and a lot more 

(Scroll down in https://brightdata.com/products/web-scraper to see all custom scrapers )

---

## 1 Quick start

```bash
export BRIGHTDATA_TOKEN=pk_live_…   # your bearer token
pip install brightdata
````

```python
import os
from dotenv import load_dotenv
from brightdata.ready_scrapers.amazon import AmazonScraper
from brightdata.utils.poll import poll_until_ready   # blocking helper
import sys

load_dotenv()
TOKEN = os.getenv("BRIGHTDATA_TOKEN")
if not TOKEN:
    sys.exit("Set BRIGHTDATA_TOKEN environment variable first")

scraper = AmazonScraper(bearer_token=TOKEN)

snap = scraper.collect_by_url([
    "https://www.amazon.com/dp/B0CRMZHDG8",
    "https://www.amazon.com/dp/B07PZF3QS3",
])

rows = poll_until_ready(scraper, snap).data    # list[dict]
print(rows[0]["title"])
```

---

## 2 What’s included

| Dataset family           | Ready-made class  | Implemented methods                                                                                                             |
| ------------------------ | ----------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Amazon products / search | `AmazonScraper`   | `collect_by_url`, `discover_by_keyword`, `discover_by_category`, `search_products`                                              |
| Digi-Key parts           | `DigiKeyScraper`  | `collect_by_url`, `discover_by_category`                                                                                        |
| Mouser parts             | `MouserScraper`   | `collect_by_url`                                                                                                                |
| LinkedIn                 | `LinkedInScraper` | `collect_people_by_url`, `discover_people_by_name`, `collect_company_by_url`, `collect_jobs_by_url`, `discover_jobs_by_keyword` |

Each call **returns a `snapshot_id` string** (sync\_mode = async).
Use one of the helpers to fetch the final data:

* `brightdata.utils.poll.poll_until_ready()` – blocking, linear
* `brightdata.utils.async_poll.wait_ready()` – single coroutine
* `brightdata.utils.async_poll.monitor_snapshots()` – fan-out hundreds using `asyncio` + `aiohttp`

---

## 3 Async example (100 keyword jobs)

```python
import asyncio
from brightdata.ready_scrapers.amazon import AmazonScraper
from brightdata.utils.async_poll import monitor_snapshots

scraper   = AmazonScraper(bearer_token=TOKEN)
snapshots = [scraper.discover_by_keyword([kw]) for kw in ["dog food", "ssd", …]]

results = asyncio.run(monitor_snapshots(scraper, snapshots, poll=15))
ready   = [r.data for r in results if r.status == "ready"]
```

Memory footprint: few kB per job → thousands of parallel polls on a single VM.

---

## 4 Mini-micro-service pattern

Need fire-and-forget?
`brightdata.utils.thread_poll.PollWorker` (one line to start) runs in a
daemon thread, writes the JSON to disk or fires a callback and never blocks
your main code.

---

## 5 Folder layout

```
brightdata/
├── base_specialized_scraper.py   ← shared HTTP logic
├── utils/
│   ├── poll.py                   ← blocking polling helper
│   └── async_poll.py             ← asyncio helpers
└── ready_scrapers/
    ├── amazon/
    ├── digikey/
    ├── mouser/
    └── linkedin/
```

---

## 6 Contributing

1. Fork, create a feature branch.
2. Keep the surface minimal – one scraper class per dataset family.
3. Run the smoke-tests under `ready_scrapers/<dataset>/tests.py`.
4. Open PR.

---




