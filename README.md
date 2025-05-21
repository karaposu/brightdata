
![BrightData Logo](https://raw.githubusercontent.com/karaposu/brightdata/refs/heads/main/brightdata.png)

---


``pip install brightdata``  →  one import away from grabbing JSON rows
from Amazon, Instagram, LinkedIn, Tiktok, Youtube, X, Reddit and more in a production-grade way.

(Scroll down in https://brightdata.com/products/web-scraper to see all specialized scrapers )

Note:  This is an unofficial SDK



---

## Features:
1. Simple usage for all "collect by url" endpoints.   ``scrape_url`` method auto recognizes url links and types. No need for complex imports for each scraper. 

2. Supports discovery and search APIs as well. for more granular control just triggering is supported

3. To enable agentic workflows package contains a Json file which contains information about all scrapers and their methods

4. Includes Web Unlocker which works with all websites




## 1. Quick start

 Obtain ``BRIGHTDATA_TOKEN`` from brightdata.com

 Create ``.env`` file and paste the token like this 

 ```bash
BRIGHTDATA_TOKEN=AJKSHKKJHKAJ…   # your token
````

install brightdata package via PyPI

```bash
pip install brightdata
````

## Table of Contents


1. [Usage](#1-usage)

   1. [Auto-URL scraping mode](#11-auto-url-scraping-mode)
   2. [Access scrapers directly](#12-access-scrapers-directly)
   3. [Async example](#13-async-example)
   4. [Thread-based PollWorker pattern usage](#14-thread-based-pollworker-pattern-usage)
   5. [Triggering in batches](#15-triggering-in-batches)
   6. [Concurrent triggering with a thread-pool](#16-concurrent-triggering-with-a-thread-pool)
2. [What’s included](#2-what’s-included)
3. [Contributing](#3-contributing)





## 1. Usage
## 1.1 Auto url scraping mode


`brightdata.auto.scrape_url` looks at the domain of a URL and
returns the scraper class that declared itself responsible for that domain.
With that you can all you have to do is feed the url.

```python
from brightdata import trigger_scrape_url, scrape_url

# trigger+wait and get the actual data
rows = scrape_url("https://www.amazon.com/dp/B0CRMZHDG8")

# just get the snapshot ID so you can collect the data later
snap = trigger_scrape_url("https://www.amazon.com/dp/B0CRMZHDG8")

```

it also works for sites which brightdata exposes several distinct “collect” endpoints.  
`LinkedInScraper` is a good example:


| LinkedIn dataset | method exposed by the scraper |
|------------------|------------------------------|
| *people profile – collect by URL*              | `collect_people_by_url()` |
| *company page  – collect by URL*               | `collect_company_by_url()` |
| *job post      – collect by URL*               | `collect_jobs_by_url()` |

In each scraper there is a smart dispatcher method which calls the right method based on link structure. 

```python

from brightdata import scrape_url

links_with_different_types = [
    "https://www.linkedin.com/in/enes-kuzucu/",
    "https://www.linkedin.com/company/105448508/",
    "https://www.linkedin.com/jobs/view/4231516747/",
]

for link in  links_with_different_types:
    rows = scrape_url(link, bearer_token=TOKEN)
    print(rows)

```


> **Note:** `trigger_scrape_url, scrape_url` methods only covers the “collect **by URL**” use-case.  
> Discovery-endpoints (keyword, category, …) are still called directly on a
> specific scraper class.

---

## 1.2 Access Scrapers Directly



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

## 1.3 Async example

- With ``fetch_snapshot_async`` you can trigger 1000 snapshots and each polling task yields control whenever it’s waiting
- All polls share one ``aiohttp.ClientSession`` (connection pool), so you’re not tearing down TCP connections for every check.

- fetch_snapshots_async is a convenience helper that wraps all the boilerplate needed when you fire off hundreds or thousands of scraping jobs—so you don’t have to manually spawn tasks and gather their results.It preserves the order of your snapshot list.
It surfaces all ScrapeResults in a single list, so you can correlate inputs → outputs easily.


```python
import asyncio
from brightdata.ready_scrapers.amazon import AmazonScraper
from brightdata.utils.async_poll import fetch_snapshots_async

# token comes from your .env
scraper = AmazonScraper(bearer_token=TOKEN)

# kick-off 100 keyword-discover jobs (all return snapshot-ids)
keywords   = ["dog food", "ssd", ...]               # 100 items
snapshots  = [scraper.discover_by_keyword([kw])     # one per call
              for kw in keywords]



# wait for *all* snapshots to finish (poll every 15 s, 10 min timeout)
results = asyncio.run(
    fetch_snapshots_async(scraper, snapshots, poll=15, timeout=600)
)

# split outcome
ready  = [r.data for r in results if r.status == "ready"]
errors = [r          for r in results if r.status != "ready"]

print("ready :", len(ready))
print("errors:", len(errors))

```



Memory footprint: few kB per job → thousands of parallel polls on a single VM.

---


## 1.4 Thread-based PollWorker pattern usage

- Running multiple (up to couple hundred max) scrape jobs with Zero changes to your sync code
- A callback to be invoked with your ScrapeResult when it’s ready or a file-path/directory to dump the JSON to disk.
- Easy to drop into any script, web-app or desktop app
- One OS thread per worker
- Ideal when your codebase is synchronous and you just want a background helper


Need fire-and-forget?
`brightdata.utils.thread_poll.PollWorker` (one line to start) runs in a
daemon thread, writes the JSON to disk or fires a callback and never blocks
your main code.

---

## 1.5 Triggering In Batches

Brightdata supports batch triggering. Which means you can do something like this

- it can be used when you dont need “one keyword → one snapshot-id” mapping.

```python
# trigger all 1 000 keywords at once ----------------------------
payload = [{"keyword": kw} for kw in keywords]       # 1 000 items
snap_id = scraper.discover_by_keyword(payload)       # ONE call

# the rest is the same as before
results = asyncio.run(
    fetch_snapshot_async(scraper, snap_id, poll=15, timeout=600)
)
rows = results.data   
```



## 1.6 Concurrent triggering with a thread-pool
- It keeps the one-kw → one-snapshot
behaviour but removes the serial wait between HTTP calls.

```python

from brightdata.utils.concurrent_trigger import trigger_keywords_concurrently
from brightdata.utils.async_poll import fetch_snapshots_async

scraper = AmazonScraper(bearer_token=TOKEN)

# 1) trigger – now takes seconds, not minutes
snapshot_map = trigger_keywords_concurrently(scraper, keywords, max_workers=64)

# 2) poll the 1 000 snapshot-ids in parallel
results = asyncio.run(
    fetch_snapshots_async(scraper,
                          list(snapshot_map.values()),
                          poll=15, timeout=600)
)

# 3) reconnect keyword ↔︎ result if you need to
kw_to_result = {
    kw: res
    for kw, sid in snapshot_map.items()
    for res in results
    if res.input_snapshot_id == sid        # you can add that attribute yourself
}

```

---

## 2. What’s included

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


---

## 3. Contributing

1. Fork, create a feature branch.
2. Keep the surface minimal – one scraper class per dataset family. 
3. Run the smoke-tests under `ready_scrapers/<dataset>/tests.py`.
4. Open PR.

---




