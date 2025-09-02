#!/usr/bin/env python3
"""
trigger_httpbin_crawl.py - Just trigger crawl operations without polling
"""

from pure_crawler_api import PureCrawlerAPI

def main():
    crawler = PureCrawlerAPI()
    
    test_url = "https://httpbin.org"
    
    print(f"Triggering crawl operations for: {test_url}")
    print("="*50)
    
    # Trigger collect
    print("\n1. Triggering Collect")
    result1 = crawler.collect_by_url([test_url])
    if "snapshot_id" in result1:
        print(f"✅ Collect Snapshot ID: {result1['snapshot_id']}")
        print(f"   Poll with: python test_poll_snapshot.py {result1['snapshot_id']}")
    
    # Trigger discover
    print("\n2. Triggering Discover")
    result2 = crawler.discover_by_domain(test_url)
    if "snapshot_id" in result2:
        print(f"✅ Discover Snapshot ID: {result2['snapshot_id']}")
        print(f"   Poll with: python test_poll_snapshot.py {result2['snapshot_id']}")
    
    print("\n" + "="*50)
    print("Snapshots triggered! Use the commands above to poll them.")

if __name__ == "__main__":
    main()