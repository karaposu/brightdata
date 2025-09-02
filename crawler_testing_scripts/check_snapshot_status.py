#!/usr/bin/env python3
"""
check_snapshot_status.py - Just check status without polling
"""

import sys
from pure_crawler_api import PureCrawlerAPI

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_snapshot_status.py <snapshot_id>")
        return
    
    snapshot_id = sys.argv[1]
    
    crawler = PureCrawlerAPI()
    status = crawler.get_snapshot_status(snapshot_id)
    
    print(f"Snapshot: {snapshot_id}")
    print(f"Status: {status}")
    
    if status.get('status') == 'ready':
        records = status.get('records', 0)
        errors = status.get('errors', 0)
        duration = status.get('collection_duration', 0)
        
        print(f"\n✅ Snapshot is ready!")
        print(f"   Records: {records}")
        print(f"   Errors: {errors}")
        print(f"   Duration: {duration}ms ({duration/1000:.1f}s)")
        print(f"\nRetrieve with: python save_crawler_result.py {snapshot_id}")

if __name__ == "__main__":
    main()