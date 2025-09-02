#!/usr/bin/env python3
"""
test_crawler_simple.py - Just trigger and get snapshot ID, no polling
"""

from pure_crawler_api import PureCrawlerAPI

def main():
    # Initialize API
    crawler = PureCrawlerAPI()
    
    print("\nTest 1: Collect by URL (no polling)")
    print("-" * 40)
    
    urls = ["https://example.com"]
    result = crawler.collect_by_url(urls)
    
    print(f"Response: {result}")
    
    if "snapshot_id" in result:
        print(f"\n✅ Success! Snapshot ID: {result['snapshot_id']}")
        print("\nYou can poll this snapshot_id later to get results")
    elif "error" in result:
        print(f"\n❌ Error: {result.get('error')}")
        print(f"Status Code: {result.get('status_code')}")
    
    print("\n" + "="*50)
    print("\nTest 2: Discover by Domain (no polling)")
    print("-" * 40)
    
    domain = "https://example.com"
    result2 = crawler.discover_by_domain(domain)
    
    print(f"Response: {result2}")
    
    if "snapshot_id" in result2:
        print(f"\n✅ Success! Snapshot ID: {result2['snapshot_id']}")
        print("\nYou can poll this snapshot_id later to get results")
    elif "error" in result2:
        print(f"\n❌ Error: {result2.get('error')}")
        print(f"Status Code: {result2.get('status_code')}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")