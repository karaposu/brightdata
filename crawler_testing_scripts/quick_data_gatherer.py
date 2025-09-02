#!/usr/bin/env python3
"""
quick_data_gatherer.py - Quick version that triggers operations without long waits
"""

import json
from datetime import datetime
from pathlib import Path
from pure_crawler_api import PureCrawlerAPI

def main():
    """Trigger various crawler operations and save snapshot IDs"""
    
    crawler = PureCrawlerAPI()
    
    # Create output directory
    output_dir = Path("crawler_data") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("QUICK CRAWLER DATA GATHERING")
    print(f"Output: {output_dir}")
    print("="*60)
    
    # Test configurations
    tests = [
        # Simple single page
        {
            "name": "example_com",
            "type": "collect",
            "urls": ["https://example.com"],
            "description": "Simple HTML page"
        },
        # Documentation page with markdown
        {
            "name": "httpbin_docs",
            "type": "collect",
            "urls": ["https://httpbin.org"],
            "description": "API documentation page"
        },
        # Multiple pages batch
        {
            "name": "httpbin_batch",
            "type": "collect",
            "urls": [
                "https://httpbin.org/",
                "https://httpbin.org/html",
                "https://httpbin.org/forms/post"
            ],
            "description": "Multiple HTTPBin pages"
        },
        # Discover with filter
        {
            "name": "example_discover",
            "type": "discover",
            "domain": "https://example.com",
            "filter": "",
            "exclude": "",
            "description": "Discover example.com domain"
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n{test['name']}: {test['description']}")
        print("-"*40)
        
        if test["type"] == "collect":
            result = crawler.collect_by_url(test["urls"])
        else:  # discover
            result = crawler.discover_by_domain(
                test["domain"],
                test.get("filter", ""),
                test.get("exclude", "")
            )
        
        if "snapshot_id" in result:
            snapshot_id = result["snapshot_id"]
            print(f"✅ Snapshot ID: {snapshot_id}")
            
            # Save snapshot info
            snapshot_info = {
                "test_name": test["name"],
                "type": test["type"],
                "snapshot_id": snapshot_id,
                "timestamp": datetime.now().isoformat(),
                "description": test["description"],
                "input": test.get("urls") or test.get("domain"),
                "filter": test.get("filter"),
                "exclude": test.get("exclude")
            }
            
            results.append(snapshot_info)
            
            # Save individual snapshot info
            with open(output_dir / f"{test['name']}_snapshot.json", 'w') as f:
                json.dump(snapshot_info, f, indent=2)
            
            filename = f"{test['name']}_snapshot.json"
            print(f"   Saved to: {output_dir / filename}")
            
            # Try quick poll (don't wait long)
            print("   Quick poll attempt...")
            status = crawler.get_snapshot_status(snapshot_id)
            
            if status.get("status") == "ready":
                print(f"   ✅ Already ready! Fetching data...")
                data = crawler.get_snapshot_data(snapshot_id)
                
                # Save the data
                data_file = output_dir / f"{test['name']}_data.json"
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"   📁 Data saved to: {data_file}")
                
                if isinstance(data, list):
                    print(f"   📊 Contains {len(data)} pages")
            else:
                print(f"   ⏳ Status: {status.get('status', 'unknown')}")
                print(f"   Poll later with: python test_poll_snapshot.py {snapshot_id}")
        else:
            print(f"❌ Failed: {result}")
    
    # Save all results
    summary_file = output_dir / "snapshots_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print(f"SUMMARY: {len(results)} operations triggered")
    print(f"Results saved to: {output_dir}")
    print(f"Summary file: {summary_file}")
    
    # Print poll commands
    print("\nTo poll these snapshots later:")
    for r in results:
        print(f"  python save_crawler_result.py {r['snapshot_id']}  # {r['test_name']}")

if __name__ == "__main__":
    main()