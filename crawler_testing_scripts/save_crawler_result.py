#!/usr/bin/env python3
"""
save_crawler_result.py - Poll a snapshot and save result to sample_result.json
"""

import sys
import json
from pure_crawler_api import PureCrawlerAPI

def main():
    # Get snapshot_id from command line or use a default
    if len(sys.argv) > 1:
        snapshot_id = sys.argv[1]
    else:
        # Use the collect snapshot from our test
        snapshot_id = "s_meskyp8a29yzyyv8ob"
    
    print(f"Polling snapshot: {snapshot_id}")
    print("-" * 40)
    
    crawler = PureCrawlerAPI()
    
    # First check status
    status = crawler.get_snapshot_status(snapshot_id)
    print(f"Current status: {status}")
    
    # Poll until ready
    data = crawler.poll_until_ready(snapshot_id, poll_interval=3, timeout=60)
    
    # Save to JSON file
    output_file = "sample_result.json"
    
    if isinstance(data, list) or isinstance(data, dict):
        # Save the raw data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Data saved to {output_file}")
        
        # Show summary
        if isinstance(data, list):
            print(f"   Contains {len(data)} pages")
            
            # Show what fields are available
            if data:
                first_page = data[0]
                available_fields = list(first_page.keys())
                print(f"   Available fields: {', '.join(available_fields)}")
                
                # Show which fields have data
                fields_with_data = [k for k, v in first_page.items() if v]
                print(f"   Fields with data: {', '.join(fields_with_data)}")
        else:
            print(f"   Data type: {type(data).__name__}")
            
    elif "error" in data:
        # Save error response too
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"\n❌ Error response saved to {output_file}")
        print(f"   Error: {data.get('error')}")
    else:
        # Save whatever we got
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"\n⚠️ Unexpected response saved to {output_file}")

if __name__ == "__main__":
    main()