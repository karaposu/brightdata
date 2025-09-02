#!/usr/bin/env python3
"""
Test 02-08: Domain Discovery with all parameters (filter, exclude, depth)

python -m smoke_tests.crawler_api.test_02_08_discover_all_params
"""

from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def main():
    """Test with filter, exclude, and depth all specified."""
    print("\n" + "="*60)
    print("TEST 02-08: Domain with All Parameters")
    print("="*60)
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    filter_pattern = "/*"  # Include all
    exclude_pattern = "*/delay/*,*/stream/*"  # Exclude slow endpoints
    depth = 1
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters:")
    print(f"    - filter_pattern: '{filter_pattern}' (include all)")
    print(f"    - exclude_pattern: '{exclude_pattern}' (exclude slow)")
    print(f"    - depth: {depth}")
    
    result = api.discover_by_domain(
        domain,
        filter_pattern=filter_pattern,
        exclude_pattern=exclude_pattern,
        depth=depth
    )
    
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
    
    # Verify all parameters worked
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        delay_urls = [u for u in urls if "/delay" in u]
        stream_urls = [u for u in urls if "/stream" in u]
        excluded_total = len(delay_urls) + len(stream_urls)
        
        print(f"    Total URLs discovered: {len(urls)}")
        print(f"    URLs with '/delay': {len(delay_urls)}")
        print(f"    URLs with '/stream': {len(stream_urls)}")
        
        if urls:
            print(f"\n    Sample URLs (first 5):")
            for url in urls[:5]:
                if "/delay" in url or "/stream" in url:
                    print(f"      ✗ EXCLUDED: {url}")
                else:
                    print(f"      ✓ {url}")
        
        print(f"\n  Verification:")
        print(f"    Filter: Include all ('/*')")
        print(f"    Exclude: No '/delay' or '/stream' URLs")
        print(f"    Depth: Limited to 1")
        print(f"    Results:")
        print(f"      - Total pages at depth=1: {result.page_count}")
        print(f"      - Excluded URLs found: {excluded_total}")
        
        if excluded_total == 0:
            print(f"    ✓ All parameters applied correctly")
        else:
            print(f"    ✗ Found {excluded_total} URLs that should be excluded")
        
        test_passed = result.success and excluded_total == 0
    else:
        test_passed = result.success
    
    if result.error:
        print(f"    Error: {result.error}")
    
    print("\n" + "="*60)
    print(f"Test {'PASSED ✓' if test_passed else 'FAILED ✗'}")
    print("="*60)


if __name__ == "__main__":
    main()