#!/usr/bin/env python3
"""
Test 02-09: Domain Discovery with ignore_sitemap parameter

python -m smoke_tests.crawler_api.test_02_09_discover_ignore_sitemap
"""

from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def main():
    """Test ignore_sitemap parameter."""
    print("\n" + "="*60)
    print("TEST 02-09: Domain with ignore_sitemap")
    print("="*60)
    
    api = CrawlerAPI()
    domain = "https://example.com"  # Using simpler domain
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters:")
    print(f"    - ignore_sitemap: True")
    print(f"    - depth: 1")
    print(f"\n  Note: ignore_sitemap tells crawler to discover links organically")
    print(f"        rather than using sitemap.xml if available")
    
    result = api.discover_by_domain(
        domain,
        ignore_sitemap=True,
        depth=1
    )
    
    if result.success and result.snapshot_id:
        print(f"\n  Snapshot ID: {result.snapshot_id}")
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
    
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        print(f"    Total URLs discovered: {len(urls)}")
        
        if urls:
            print(f"\n    URLs found (organically, without sitemap):")
            for url in urls[:10]:
                print(f"      - {url}")
            if len(urls) > 10:
                print(f"      ... and {len(urls) - 10} more")
        
        print(f"\n  Verification:")
        print(f"    Pages discovered organically: {result.page_count}")
        print(f"    ✓ Discovery completed with ignore_sitemap=True")
    
    if result.error:
        print(f"    Error: {result.error}")
    
    print("\n" + "="*60)
    print(f"Test {'PASSED ✓' if result.success else 'FAILED ✗'}")
    print("="*60)


if __name__ == "__main__":
    main()