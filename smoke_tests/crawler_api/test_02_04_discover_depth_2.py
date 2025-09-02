#!/usr/bin/env python3
"""
Test 02-04: Domain Discovery with depth=2 (two levels deep)

python -m smoke_tests.crawler_api.test_02_04_discover_depth_2
"""

from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()


def main():
    """Test domain discovery with depth=2 (two levels deep)."""
    print("\n" + "="*60)
    print("TEST 02-04: Domain with depth=2")
    print("="*60)
    
    api = CrawlerAPI()
    domain = "https://example.com"
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters: depth=2 (follow links two levels deep)")
    print(f"  Note: This may take 5-10 minutes")
    
    result = api.discover_by_domain(domain, depth=2)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        print(f"  Polling (deeper crawls take longer)...")
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
    
    # Analyze depth distribution
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        print(f"    Total URLs discovered: {len(urls)}")
        
        # Analyze URL depth
        base_domain = "example.com"
        depth_stats = {}
        for url in urls:
            # Count path segments to estimate depth
            path = url.replace("https://", "").replace("http://", "")
            segments = len([s for s in path.split("/")[1:] if s])  # Skip domain
            depth_stats[segments] = depth_stats.get(segments, 0) + 1
        
        print(f"\n    URL depth distribution:")
        for depth, count in sorted(depth_stats.items()):
            print(f"      Depth {depth}: {count} URLs")
        
        print(f"\n  Verification:")
        print(f"    Expected: More pages than depth=1")
        print(f"    Actual: {result.page_count} pages")
        
        if result.page_count >= 1:  # At least some pages
            print(f"    ✓ Depth=2 crawl completed")
    
    if result.error:
        print(f"    Error: {result.error}")
    
    print("\n" + "="*60)
    print(f"Test {'PASSED ✓' if result.success else 'FAILED ✗'}")
    print("="*60)


if __name__ == "__main__":
    main()