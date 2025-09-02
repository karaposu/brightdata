#!/usr/bin/env python3
"""
quick_param_tester.py - Quick version that just gets snapshot IDs
"""

import json
from datetime import datetime
from pathlib import Path
from pure_crawler_api import PureCrawlerAPI

def main():
    crawler = PureCrawlerAPI()
    
    # Output directory
    output_dir = Path("crawler_tests") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output: {output_dir}\n")
    
    # Test cases
    tests = [
        {
            "name": "single_url",
            "params": {
                "type": "collect",
                "urls": ["https://example.com"]
            }
        },
        {
            "name": "batch_urls",
            "params": {
                "type": "collect",
                "urls": [
                    "https://httpbin.org/",
                    "https://httpbin.org/html",
                    "https://httpbin.org/forms/post"
                ]
            }
        },
        {
            "name": "discover_no_filter",
            "params": {
                "type": "discover",
                "domain": "https://example.com",
                "filter": "",
                "exclude": ""
            }
        },
        {
            "name": "discover_with_filter",
            "params": {
                "type": "discover",
                "domain": "https://httpbin.org",
                "filter": "/forms/*",
                "exclude": ""
            }
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"Test: {test['name']}")
        
        params = test['params']
        
        # Make API call
        if params['type'] == 'collect':
            api_response = crawler.collect_by_url(params['urls'])
        else:  # discover
            api_response = crawler.discover_by_domain(
                params['domain'],
                params.get('filter', ''),
                params.get('exclude', '')
            )
        
        # Create record
        record = {
            "test": test['name'],
            "params": params,
            "response": api_response  # Just the snapshot response, no polling
        }
        
        # Save individual file
        filepath = output_dir / f"{test['name']}.json"
        with open(filepath, 'w') as f:
            json.dump(record, f, indent=2)
        
        print(f"  ✅ Snapshot: {api_response.get('snapshot_id', 'ERROR')}")
        print(f"  📁 Saved: {filepath.name}\n")
        
        results.append(record)
    
    # Save combined
    with open(output_dir / "all_tests.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDone! Files in: {output_dir}")
    
    # Print commands to poll later
    print("\nTo get actual data, poll these snapshots:")
    for r in results:
        if 'snapshot_id' in r['response']:
            print(f"python save_crawler_result.py {r['response']['snapshot_id']}  # {r['test']}")


if __name__ == "__main__":
    main()