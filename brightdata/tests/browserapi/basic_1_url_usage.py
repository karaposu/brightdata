#!/usr/bin/env python3
"""
brightdata.tests.browserapi.basic_1_url_usage.py

Smoke‐test for Bright Data’s BrowserAPI:

  • Fetch page source without extra delay
  • Fetch page source with a 5s hydration‐wait
  • Print out key metrics (success, timings, html size, etc.)

Usage:
  python -m brightdata.tests.browserapi.basic_1_url_usage
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from brightdata.browser_api import BrowserAPI

def _fmt(ts: datetime | None) -> str:
    return ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "–"

def show_result(label: str, res):
    print(f"\n{label}")
    print("─" * len(label))
    print(f"success            : {res.success}")
    print(f"status             : {res.status}")
    print(f"root_domain        : {res.root_domain!r}")
    print(f"request_sent_at    : {_fmt(res.request_sent_at)}")
    print(f"browser_warmed_at  : {_fmt(res.browser_warmed_at)}")
    print(f"data_received_at   : {_fmt(res.data_received_at)}")
    # html_char_size: length of the HTML string
    html = res.data if isinstance(res.data, str) else ""
    print(f"html_char_size     : {len(html)}")
    if res.error:
        print(f"error              : {res.error}")

def main():

    import logging
    logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s  %(message)s",
)
    

    url = "https://openai.com"
    api = BrowserAPI()
    # api = BrowserAPI(enable_networkidle_hydration_sign=True)
    
    # 1) quick fetch, no hydration wait
    res1 = api.get_page_source(url)
    show_result("get_page_source", res1)
    # api.close()  
    # asyncio.run(api.close())                # actually tear it down
     
    # 2) fetch with a 5s hydration wait
    res2 = api.get_page_source_with_a_delay(url, wait_time_in_seconds=5)
    show_result("get_page_source_with_a_delay", res2)
    # asyncio.run(api.close())                # tear that one down too
    # api.close()  
    
    # clean up (optional; this is async)
    try:
        import asyncio
        asyncio.run(api.close())
    except Exception:
        pass

if __name__ == "__main__":
    main()
