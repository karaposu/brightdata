#!/usr/bin/env python3
"""
Test 02-01: Basic Domain Discovery with default parameters

python -m smoke_tests.crawler_api.test_02_01_discover_basic
"""

from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def main():
    """Test basic domain discovery with default parameters."""
    print("\n" + "="*60)
    print("TEST 02-01: Basic Domain Discovery (defaults)")
    print("="*60)
    
    api = CrawlerAPI()
    domain = "https://example.com"  # Using simpler domain for faster results
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters: All defaults (no depth, filter, or exclude)")
    
    result = api.discover_by_domain(domain)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        print(f"  Polling for results (may take 5+ minutes)...")
        result = api.poll_until_ready(result, poll_interval=20, timeout=600)
    
    # Print results
    print(f"\n  Results:")
    print(f"    Success: {result.success}")
    print(f"    Status: {result.status}")
    print(f"    Pages discovered: {result.page_count}")
    
    if result.crawl_params:
        print(f"    Crawl parameters used:")
        for key, value in result.crawl_params.items():
            if value not in [None, "", []]:
                print(f"      - {key}: {value}")
    
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        print(f"    Total URLs discovered: {len(urls)}")
        
        if urls:
            print(f"    Sample URLs (first 5):")
            for url in urls[:5]:
                print(f"      - {url}")
    
    if result.error:
        print(f"    Error: {result.error}")
    
    print("\n" + "="*60)
    print(f"Test {'PASSED ✓' if result.success else 'FAILED ✗'}")
    print("="*60)


if __name__ == "__main__":
    main()