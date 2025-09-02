#!/usr/bin/env python3
"""
Working test using the built-in polling method
"""

import time
from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()

print("CRAWLER API TEST - COLLECT BY URL")
print("="*60)

api = CrawlerAPI()

# Test 1: Single URL with full polling
print("\nTest 1: Single URL")
url = "https://httpbin.org/html"
print(f"Collecting: {url}")

result = api.collect_by_url([url])
print(f"Triggered - Snapshot ID: {result.snapshot_id}")

if result.success:
    print("Polling for results (this may take 30-60 seconds)...")
    result = api.poll_until_ready(result, poll_interval=10, timeout=120)
    
    print(f"\nResults:")
    print(f"  Status: {result.status}")
    print(f"  Success: {result.success}")
    print(f"  Pages: {result.page_count}")
    
    if result.pages:
        result.analyze_content()
        print(f"  Formats: {result.formats_available}")
        print(f"  Markdown chars: {result.total_markdown_chars:,}")
        
        page = result.pages[0]
        print(f"\nFirst page:")
        print(f"  URL: {page.get('url')}")
        markdown = page.get('markdown', '')
        if markdown:
            preview = markdown[:100].replace('\n', ' ')
            print(f"  Preview: {preview}...")

print("\n" + "="*60)

# Test 2: Multiple URLs
print("\nTest 2: Multiple URLs")
urls = [
    "https://httpbin.org/html",
    "https://httpbin.org/json"
]
print(f"Collecting {len(urls)} URLs")

result = api.collect_by_url(urls)
print(f"Triggered - Snapshot ID: {result.snapshot_id}")

if result.success:
    print("Polling...")
    result = api.poll_until_ready(result, poll_interval=10, timeout=120)
    
    print(f"\nResults:")
    print(f"  Status: {result.status}")
    print(f"  Pages collected: {result.page_count}")
    
    if result.pages:
        for i, page in enumerate(result.pages):
            print(f"  Page {i+1}: {page.get('url')}")

print("\nTest complete!")