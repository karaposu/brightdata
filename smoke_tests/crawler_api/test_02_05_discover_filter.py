#!/usr/bin/env python3
"""
Test 02-05: Domain Discovery with filter pattern only

python -m smoke_tests.crawler_api.test_02_05_discover_filter
"""

from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def main():
    """Test domain discovery with filter pattern only."""
    print("\n" + "="*60)
    print("TEST 02-05: Domain with Filter Pattern")
    print("="*60)
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    filter_pattern = "/status/*"
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters: filter_pattern='{filter_pattern}'")
    print(f"  Note: No depth specified (using default)")
    
    result = api.discover_by_domain(domain, filter_pattern=filter_pattern)
    
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
    
    # Verify filter worked
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        matching_urls = [u for u in urls if "/status" in u]
        non_matching = [u for u in urls if "/status" not in u]
        
        print(f"    Total URLs discovered: {len(urls)}")
        print(f"    URLs matching '/status/*': {len(matching_urls)}")
        print(f"    URLs NOT matching: {len(non_matching)}")
        
        if urls:
            print(f"\n    Sample URLs:")
            for url in urls[:5]:
                match = "✓" if "/status" in url else "✗"
                print(f"      {match} {url}")
        
        print(f"\n  Verification:")
        print(f"    Expected: All URLs should match '/status/*'")
        print(f"    Matching: {len(matching_urls)}/{len(urls)}")
        
        if non_matching:
            print(f"    Non-matching URLs found:")
            for url in non_matching[:3]:
                print(f"      - {url}")
    
    if result.error:
        print(f"    Error: {result.error}")
    
    print("\n" + "="*60)
    print(f"Test {'PASSED ✓' if result.success else 'FAILED ✗'}")
    print("="*60)


if __name__ == "__main__":
    main()