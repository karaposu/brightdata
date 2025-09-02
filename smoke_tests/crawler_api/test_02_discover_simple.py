#!/usr/bin/env python3
"""
Simple discover_by_domain test to show results
"""

from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def main():
    """Run a simple discovery test."""
    print("\nCRAWLER API - DISCOVER BY DOMAIN TEST")
    print("="*60)
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    
    # Test 1: Basic discovery with depth=1
    print(f"\nDiscovering: {domain}")
    print("Parameters: depth=1")
    
    result = api.discover_by_domain(domain, depth=1)
    print(f"Snapshot ID: {result.snapshot_id}")
    
    if result.success:
        print("Polling for results...")
        result = api.poll_until_ready(result, poll_interval=10, timeout=120)
        
        print(f"\nResults Summary:")
        print(f"  Success: {result.success}")
        print(f"  Status: {result.status}")
        print(f"  Pages discovered: {result.page_count}")
        
        if result.pages:
            result.analyze_content()
            urls = result.get_urls()
            print(f"  URLs found: {len(urls)}")
            print(f"\nFirst 10 URLs:")
            for url in urls[:10]:
                print(f"    - {url}")
    
    # Test 2: With filter
    print("\n" + "="*60)
    print("\nTest 2: Discovery with filter")
    print(f"Domain: {domain}")
    print("Filter: /status/*")
    print("Depth: 1")
    
    result = api.discover_by_domain(
        domain,
        filter_pattern="/status/*",
        depth=1
    )
    print(f"Snapshot ID: {result.snapshot_id}")
    
    if result.success:
        print("Polling...")
        result = api.poll_until_ready(result, poll_interval=10, timeout=120)
        
        print(f"\nFiltered Results:")
        print(f"  Pages discovered: {result.page_count}")
        
        if result.pages:
            urls = result.get_urls()
            print(f"  URLs matching filter:")
            for url in urls[:10]:
                print(f"    - {url}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    main()