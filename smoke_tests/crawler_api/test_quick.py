#!/usr/bin/env python3
"""
Quick test with debug output
"""

import time
from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()

print("Starting test...")
print(f"Time: {time.strftime('%H:%M:%S')}")

try:
    api = CrawlerAPI()
    print("API initialized")
    
    url = "https://httpbin.org/html"
    print(f"Collecting: {url}")
    
    result = api.collect_by_url([url])
    print(f"Trigger response received - Snapshot ID: {result.snapshot_id}")
    print(f"Initial status: {result.status}")
    
    if result.success and result.snapshot_id:
        print("Starting polling...")
        max_polls = 12  # 12 polls * 5 seconds = 60 seconds max
        
        for i in range(max_polls):
            print(f"Poll {i+1}/{max_polls} at {time.strftime('%H:%M:%S')}")
            
            # Do one poll
            response = api.get_snapshot_data(result.snapshot_id)
            
            # Update result with the response
            if isinstance(response, dict):
                result.status = response.get('status', 'unknown')
                if response.get('data'):
                    result.pages = response['data']
                    result.page_count = len(response['data'])
            
            if result.status == "ready":
                print(f"Ready! Pages: {result.page_count}")
                break
            
            print(f"  Status: {result.status}")
            time.sleep(5)
        
        if result.status == "ready" and result.pages:
            print(f"\nSuccess! Collected {len(result.pages)} pages")
            page = result.pages[0]
            print(f"URL: {page.get('url')}")
            print(f"Has markdown: {bool(page.get('markdown'))}")
            print(f"Markdown length: {len(page.get('markdown', ''))}")
        else:
            print(f"Timed out or failed. Final status: {result.status}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\nTest ended at {time.strftime('%H:%M:%S')}")