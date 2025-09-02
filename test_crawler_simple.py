#!/usr/bin/env python3
"""
Simple functional test for Crawler API
"""

import json
from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def test_simple_collect():
    """Test a simple collect operation"""
    print("Testing Crawler API - Simple Collect")
    print("=" * 50)
    
    api = CrawlerAPI()
    
    # Step 1: Trigger collection
    print("\n1. Triggering collection for httpbin.org/html...")
    result = api.collect_by_url(["https://httpbin.org/html"])
    
    if not result.success:
        print(f"   Failed to trigger: {result.error}")
        return
    
    print(f"   ✓ Snapshot ID: {result.snapshot_id}")
    
    # Step 2: Poll for results
    print("\n2. Polling for results...")
    result = api.poll_until_ready(result, poll_interval=5, timeout=60)
    
    if not result.success:
        print(f"   Failed: {result.error}")
        return
    
    print(f"   ✓ Status: {result.status}")
    print(f"   ✓ Pages collected: {result.page_count}")
    
    # Step 3: Analyze results
    if result.pages:
        result.analyze_content()
        print("\n3. Analysis:")
        print(f"   - URLs collected: {len(result.urls_collected)}")
        print(f"   - Formats available: {result.formats_available}")
        print(f"   - Total markdown chars: {result.total_markdown_chars}")
        print(f"   - Total HTML chars: {result.total_html_chars}")
        
        # Show sample of first page
        page = result.pages[0]
        print("\n4. Sample content from first page:")
        print(f"   - URL: {page.get('url')}")
        print(f"   - Title: {page.get('page_title', 'N/A')}")
        
        if page.get('markdown'):
            preview = page['markdown'][:200].replace('\n', ' ')
            print(f"   - Markdown preview: {preview}...")
    
    print("\n" + "=" * 50)
    print("Test completed successfully!")


if __name__ == "__main__":
    test_simple_collect()