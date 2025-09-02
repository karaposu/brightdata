#!/usr/bin/env python3
"""
Test 02-03: Domain Discovery with depth=1 (page + direct links)

python -m smoke_tests.crawler_api.test_02_03_discover_depth_1
"""

from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def main():
    """Test domain discovery with depth=1 (page + direct links)."""
    print("\n" + "="*60)
    print("TEST 02-03: Domain with depth=1")
    print("="*60)
    
    api = CrawlerAPI()
    domain = "https://example.com"
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters: depth=1 (main page + direct links)")
    
    result = api.discover_by_domain(domain, depth=1)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        print(f"  Polling for results...")
        result = api.poll_until_ready(result, poll_interval=15, timeout=400)
    
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
    
    # Show discovered URLs
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        print(f"    Total URLs discovered: {len(urls)}")
        
        if urls:
            print(f"    URLs found:")
            for url in urls[:10]:  # Show first 10
                print(f"      - {url}")
            if len(urls) > 10:
                print(f"      ... and {len(urls) - 10} more")
        
        print(f"\n  Verification:")
        print(f"    Expected: Multiple pages (more than depth=0)")
        print(f"    Actual: {result.page_count} pages")
        
        if result.page_count > 1:
            print(f"    ✓ Depth=1 discovered additional pages")
        else:
            print(f"    ✗ Depth=1 should find more than 1 page")
    
    if result.error:
        print(f"    Error: {result.error}")
    
    test_passed = result.success and result.page_count > 1
    
    print("\n" + "="*60)
    print(f"Test {'PASSED ✓' if test_passed else 'FAILED ✗'}")
    print("="*60)


if __name__ == "__main__":
    main()