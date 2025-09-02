#!/usr/bin/env python3
"""
test_discover_and_save.py - Test discover and save to sample_discover_result.json
"""

import json
from pure_crawler_api import PureCrawlerAPI

def main():
    crawler = PureCrawlerAPI()
    
    print("Testing Discover by Domain")
    print("-" * 40)
    
    # Trigger discover
    domain = "https://example.com"
    result = crawler.discover_by_domain(domain)
    
    if "snapshot_id" in result:
        snapshot_id = result["snapshot_id"]
        print(f"Got Snapshot ID: {snapshot_id}")
        
        # Poll for results
        data = crawler.poll_until_ready(snapshot_id, poll_interval=3, timeout=60)
        
        # Save to JSON
        output_file = "sample_discover_result.json"
        
        if isinstance(data, list) or isinstance(data, dict):
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Data saved to {output_file}")
            
            if isinstance(data, list):
                print(f"   Discovered {len(data)} pages")
                
                # Analyze URLs
                urls = [page.get('url', '') for page in data]
                internal = [u for u in urls if domain.replace('https://', '') in u]
                external = [u for u in urls if domain.replace('https://', '') not in u]
                
                print(f"   Internal URLs: {len(internal)}")
                print(f"   External URLs: {len(external)}")
                
                print("\n   All URLs found:")
                for url in urls[:10]:  # First 10
                    print(f"     - {url}")
    else:
        print(f"Error: {result}")

if __name__ == "__main__":
    main()