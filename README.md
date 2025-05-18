
![PyTorch Logo](https://github.com/karaposu/brightdata/raw/main/docs/source/_static/img/pytorch-logo-dark.png)

brightdata 
==========

``pip install brightdata``  →  one import away from grabbing JSON rows
from Amazon, Digi-Key, Mouser, LinkedIn, Tiktok, Youtube, Instagram and a lot more in a production grade way

(Scroll down in https://brightdata.com/products/web-scraper to see all custom scrapers )

Unofficial **Python helper-SDK** for BrightData which wraps Bright Data’s **Dataset API** with small, ready-made
“scraper” classes



---

## Features:

1. If all you want to do is **fetch the data that belongs to a URL** you don’t
even need to know which scraper to instantiate—the toolkit can pick the right
one automatically. 

2. 






## 1 Quick start

 Obtain BRIGHTDATA_TOKEN from brightdata.com

 Create .env file and paste the token like this 

 ```bash
BRIGHTDATA_TOKEN=AJKSHKKJHKAJ…   # your token
````

install brightdata package via PyPI

```bash
pip install brightdata
````

## Table of Contents

1. [Quick start](#1-quick-start)  
2. [What’s included](#2-whats-included)  
3. [Auto url scraping mode](#3-auto-url-scraping-mode)  
4. [Access Scrapers Directly](#4-access-scrapers-directly)  
5. [Async example (100 keyword jobs)](#5-async-example-100-keyword-jobs)  
6. [Mini-micro-service pattern](#6-mini-micro-service-pattern)  
7. [Contributing](#7-contributing)  





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



## 3 Auto url scraping mode


`brightdata.auto.scrape_url` looks at the domain of a URL and
returns the scraper class that declared itself responsible for that domain.
With that you can all you have to do is feed the url

```python
from brightdata import trigger_scrape_url, scrape_url

# or trigger+wait and get the actual data
rows = scrape_url("https://www.amazon.com/dp/B0CRMZHDG8", bearer_token=TOKEN)

# just get the snapshot ID 
snap = trigger_scrape_url("https://www.amazon.com/dp/B0CRMZHDG8", bearer_token=TOKEN)

```

it also works for sites which expose several distinct “collect” datasets.  
`LinkedInScraper` is a good example:


| LinkedIn dataset | method exposed by the scraper |
|------------------|------------------------------|
| *people profile – collect by URL*              | `collect_people_by_url()` |
| *company page  – collect by URL*               | `collect_company_by_url()` |
| *job post      – collect by URL*               | `collect_jobs_by_url()` |


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


## 4 Access Scrapers Directly



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


## 5 Async example (100 keyword jobs)

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

## 6 Mini-micro-service pattern

Need fire-and-forget?
`brightdata.utils.thread_poll.PollWorker` (one line to start) runs in a
daemon thread, writes the JSON to disk or fires a callback and never blocks
your main code.

---


---

## 7 Contributing

1. Fork, create a feature branch.
2. Keep the surface minimal – one scraper class per dataset family. 
3. Run the smoke-tests under `ready_scrapers/<dataset>/tests.py`.
4. Open PR.

---




