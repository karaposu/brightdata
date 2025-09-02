#!/usr/bin/env python3
"""
Test 02-10: crawl_domain convenience function

python -m smoke_tests.crawler_api.test_02_10_discover_convenience
"""

from dotenv import load_dotenv
from brightdata.crawlerapi import crawl_domain

load_dotenv()


def main():
    """Test the crawl_domain convenience function."""
    print("\n" + "="*60)
    print("TEST 02-10: Convenience Function crawl_domain()")
    print("="*60)
    
    domain = "https://httpbin.org"
    
    print(f"  Using crawl_domain() for: {domain}")
    print(f"  Parameters:")
    print(f"    - filter_pattern: '/status/*'")
    print(f"    - depth: 1")
    print(f"    - poll_interval: 15")
    print(f"    - timeout: 400")
    
    # Use convenience function
    result = crawl_domain(
        domain,
        filter_pattern="/status/*",
        depth=1,
        poll_interval=15,
        timeout=400
    )
    
    # Print results
    print(f"\n  Results:")
    print(f"    Success: {result.success}")
    print(f"    Status: {result.status}")
    print(f"    Operation: {result.operation}")
    print(f"    Pages discovered: {result.page_count}")
    
    if result.crawl_params:
        print(f"    Crawl parameters used:")
        for key, value in result.crawl_params.items():
            if value not in [None, "", []]:
                print(f"      - {key}: {value}")
    
    # Verify it worked
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        status_urls = [u for u in urls if "/status" in u]
        
        print(f"    Total URLs discovered: {len(urls)}")
        print(f"    URLs with '/status': {len(status_urls)}")
        
        if urls:
            print(f"\n    Sample URLs:")
            for url in urls[:5]:
                match = "✓" if "/status" in url else "✗"
                print(f"      {match} {url}")
        
        print(f"\n  Verification:")
        print(f"    Convenience function: crawl_domain()")
        print(f"    Expected: URLs matching '/status/*'")
        print(f"    Result: {len(status_urls)}/{len(urls)} match")
        
        if len(status_urls) > 0:
            print(f"    ✓ Convenience function working")
    
    if result.error:
        print(f"    Error: {result.error}")
    
    print("\n" + "="*60)
    print(f"Test {'PASSED ✓' if result.success else 'FAILED ✗'}")
    print("="*60)


if __name__ == "__main__":
    main()