#!/usr/bin/env python3
"""
Simple test for collect_by_url to show result summary
"""

import json
from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def main():
    """Run a simple collect test and show results."""
    print("\nCRAWLER API - COLLECT BY URL TEST")
    print("="*60)
    
    api = CrawlerAPI()
    
    # Test 1: Single URL
    print("\nTest 1: Single URL Collection")
    print("-"*40)
    url = "https://httpbin.org/html"
    print(f"Collecting: {url}")
    
    result = api.collect_by_url([url])
    print(f"Snapshot ID: {result.snapshot_id}")
    
    if result.success:
        result = api.poll_until_ready(result, poll_interval=5, timeout=60)
        
        print(f"\nResults Summary:")
        print(f"  Success: {result.success}")
        print(f"  Status: {result.status}")
        print(f"  Pages collected: {result.page_count}")
        
        if result.pages:
            result.analyze_content()
            print(f"  Formats available: {result.formats_available}")
            print(f"  Total markdown chars: {result.total_markdown_chars:,}")
            print(f"  Total HTML chars: {result.total_html_chars:,}")
            
            # Show first page details
            page = result.pages[0]
            print(f"\nFirst Page Details:")
            print(f"  URL: {page.get('url')}")
            print(f"  Has markdown: {bool(page.get('markdown'))}")
            print(f"  Has HTML: {bool(page.get('page_html'))}")
            print(f"  Has text: {bool(page.get('html2text'))}")
            
            if page.get('markdown'):
                preview = page['markdown'][:150].replace('\n', ' ')
                print(f"  Markdown preview: {preview}...")
    
    # Test 2: Multiple URLs
    print("\n" + "="*60)
    print("Test 2: Multiple URLs Collection")
    print("-"*40)
    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/anything"
    ]
    
    print(f"Collecting {len(urls)} URLs:")
    for u in urls:
        print(f"  - {u}")
    
    result = api.collect_by_url(urls)
    print(f"\nSnapshot ID: {result.snapshot_id}")
    
    if result.success:
        result = api.poll_until_ready(result, poll_interval=5, timeout=90)
        
        print(f"\nResults Summary:")
        print(f"  Success: {result.success}")
        print(f"  Status: {result.status}")
        print(f"  Pages collected: {result.page_count}")
        
        if result.pages:
            result.analyze_content()
            print(f"  URLs collected: {len(result.get_urls())}")
            for url in result.get_urls():
                print(f"    - {url}")
    
    print("\n" + "="*60)
    print("Test completed!")


if __name__ == "__main__":
    main()