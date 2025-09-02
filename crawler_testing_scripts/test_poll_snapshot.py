#!/usr/bin/env python3
"""
test_poll_snapshot.py - Poll a specific snapshot ID
"""

import sys
from pure_crawler_api import PureCrawlerAPI

def main():
    # Get snapshot_id from command line or use a default
    if len(sys.argv) > 1:
        snapshot_id = sys.argv[1]
    else:
        # Use the one from our test
        snapshot_id = "s_meskyp8a29yzyyv8ob"
    
    print(f"Polling snapshot: {snapshot_id}")
    print("-" * 40)
    
    crawler = PureCrawlerAPI()
    
    # First check status
    status = crawler.get_snapshot_status(snapshot_id)
    print(f"Current status: {status}")
    
    # Poll until ready
    data = crawler.poll_until_ready(snapshot_id, poll_interval=3, timeout=60)
    
    if isinstance(data, list):
        print(f"\n✅ Got {len(data)} pages")
        for i, page in enumerate(data[:3], 1):  # Show first 3
            print(f"\nPage {i}:")
            print(f"  URL: {page.get('url', 'N/A')}")
            print(f"  Title: {page.get('page_title', 'N/A')}")
            
            # Show available data formats
            formats = []
            if page.get('markdown'):
                formats.append('markdown')
            if page.get('html2text'):
                formats.append('html2text')
            if page.get('page_html'):
                formats.append('page_html')
            if page.get('ld_json'):
                formats.append('ld_json')
            
            print(f"  Available formats: {', '.join(formats) if formats else 'None'}")
            
            # Show sample of markdown if available
            if page.get('markdown'):
                sample = page['markdown'][:200].replace('\n', ' ')
                print(f"  Markdown sample: {sample}...")
    elif "error" in data:
        print(f"\n❌ Error: {data.get('error')}")
    else:
        print(f"\nUnexpected response: {data}")

if __name__ == "__main__":
    main()