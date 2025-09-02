#!/usr/bin/env python3
"""
Test 02-07: Domain Discovery with exclude pattern

python -m smoke_tests.crawler_api.test_02_07_discover_exclude
"""

from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def main():
    """Test domain discovery with exclude pattern."""
    print("\n" + "="*60)
    print("TEST 02-07: Domain with Exclude Pattern")
    print("="*60)
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    exclude_pattern = "*/image/*,*/bytes/*"
    depth = 1
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters:")
    print(f"    - exclude_pattern: '{exclude_pattern}'")
    print(f"    - depth: {depth}")
    
    result = api.discover_by_domain(
        domain,
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
    
    # Verify exclusion worked
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        image_urls = [u for u in urls if "/image" in u]
        bytes_urls = [u for u in urls if "/bytes" in u]
        excluded_count = len(image_urls) + len(bytes_urls)
        
        print(f"    Total URLs discovered: {len(urls)}")
        print(f"    URLs with '/image': {len(image_urls)}")
        print(f"    URLs with '/bytes': {len(bytes_urls)}")
        print(f"    Total excluded: {excluded_count}")
        
        if urls:
            print(f"\n    Sample URLs (first 5):")
            for url in urls[:5]:
                excluded = "✗ EXCLUDED" if ("/image" in url or "/bytes" in url) else "✓"
                print(f"      {excluded} {url}")
        
        print(f"\n  Verification:")
        print(f"    Expected: No URLs with '/image' or '/bytes'")
        print(f"    Found {excluded_count} excluded URLs")
        
        if excluded_count == 0:
            print(f"    ✓ Exclusion pattern working correctly")
        else:
            print(f"    ✗ Found URLs that should be excluded:")
            for url in (image_urls + bytes_urls)[:3]:
                print(f"      - {url}")
        
        test_passed = result.success and excluded_count == 0
    else:
        test_passed = result.success
    
    if result.error:
        print(f"    Error: {result.error}")
    
    print("\n" + "="*60)
    print(f"Test {'PASSED ✓' if test_passed else 'FAILED ✗'}")
    print("="*60)


if __name__ == "__main__":
    main()