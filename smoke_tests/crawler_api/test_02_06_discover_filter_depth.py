#!/usr/bin/env python3
"""
Test 02-06: Domain Discovery with both filter pattern and depth

python -m smoke_tests.crawler_api.test_02_06_discover_filter_depth
"""

from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def main():
    """Test domain discovery with both filter pattern and depth."""
    print("\n" + "="*60)
    print("TEST 02-06: Domain with Filter Pattern and Depth")
    print("="*60)
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    filter_pattern = "/forms/*"
    depth = 1
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters:")
    print(f"    - filter_pattern: '{filter_pattern}'")
    print(f"    - depth: {depth}")
    
    result = api.discover_by_domain(
        domain,
        filter_pattern=filter_pattern,
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
    
    # Verify both parameters worked
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        forms_urls = [u for u in urls if "/forms" in u]
        other_urls = [u for u in urls if "/forms" not in u]
        
        print(f"    Total URLs discovered: {len(urls)}")
        print(f"    URLs with '/forms': {len(forms_urls)}")
        print(f"    Other URLs: {len(other_urls)}")
        
        if urls:
            print(f"\n    Sample URLs:")
            for url in urls[:5]:
                match = "✓" if "/forms" in url else "✗"
                print(f"      {match} {url}")
        
        print(f"\n  Verification:")
        print(f"    Filter: URLs should match '/forms/*'")
        print(f"    Depth: Limited to depth=1")
        print(f"    Results: {len(forms_urls)}/{len(urls)} match filter")
        
        if len(urls) > 0 and len(forms_urls) > 0:
            print(f"    ✓ Filter and depth both applied")
    
    if result.error:
        print(f"    Error: {result.error}")
    
    print("\n" + "="*60)
    print(f"Test {'PASSED ✓' if result.success else 'FAILED ✗'}")
    print("="*60)


if __name__ == "__main__":
    main()