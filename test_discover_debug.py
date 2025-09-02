#!/usr/bin/env python3
"""
Debug discover_by_domain to see what's happening
"""

import time
from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI

load_dotenv()

def debug_discover():
    api = CrawlerAPI()
    
    # Try a simple domain with depth=0
    domain = "https://example.com"
    print(f"Testing discover with {domain}, depth=0")
    
    result = api.discover_by_domain(domain, depth=0)
    print(f"Initial response:")
    print(f"  Success: {result.success}")
    print(f"  Snapshot ID: {result.snapshot_id}")
    print(f"  Status: {result.status}")
    
    if not result.success:
        print(f"  Failed to trigger discovery")
        return
    
    # Poll manually with debug output
    print("\nPolling status...")
    max_attempts = 20
    
    for i in range(max_attempts):
        time.sleep(10)
        
        # Check status
        status = api.get_snapshot_status(result.snapshot_id)
        print(f"  Poll {i+1}: {status}")
        
        if status.get("status") == "ready":
            print("\n✓ Snapshot is ready!")
            
            # Get the data
            data = api.get_snapshot_data(result.snapshot_id)
            if isinstance(data, dict) and data.get("status") == "building":
                print("  Still building even though status says ready...")
                continue
                
            print(f"  Data received: {type(data)}")
            if isinstance(data, list):
                print(f"  Pages: {len(data)}")
                if data:
                    print(f"  First URL: {data[0].get('url')}")
            break
            
        elif status.get("status") in ["error", "failed"]:
            print(f"\n✗ Discovery failed: {status}")
            break

if __name__ == "__main__":
    debug_discover()