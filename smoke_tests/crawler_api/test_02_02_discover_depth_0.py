#!/usr/bin/env python3
"""
Test 02-02: Domain Discovery with depth=0 (single page only)

python -m smoke_tests.crawler_api.test_02_02_discover_depth_0
"""

from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def main():
    """Test domain discovery with depth=0 (single page only)."""
    print("\n" + "="*60)
    print("TEST 02-02: Domain with depth=0")
    print("="*60)
    
    api = CrawlerAPI()
    domain = "https://example.com"
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters: depth=0 (single page only)")
    
    result = api.discover_by_domain(domain, depth=0)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        print(f"  Polling for results...")
        result = api.poll_until_ready(result, poll_interval=15, timeout=300)
    
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
    
    # Verify depth=0 behavior
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        print(f"    URLs found: {urls}")
        print(f"\n  Verification:")
        print(f"    Expected: Exactly 1 page")
        print(f"    Actual: {result.page_count} page(s)")
        
        if result.page_count == 1:
            print(f"    ✓ Depth=0 working correctly")
        else:
            print(f"    ✗ Unexpected page count for depth=0")
    
    if result.error:
        print(f"    Error: {result.error}")
    
    test_passed = result.success and result.page_count == 1
    
    print("\n" + "="*60)
    print(f"Test {'PASSED ✓' if test_passed else 'FAILED ✗'}")
    print("="*60)


if __name__ == "__main__":
    main()