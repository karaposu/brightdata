#!/usr/bin/env python3
"""
simple_crawler_tester.py - Simple tester that saves params and response for each test

One JSON file per test with structure:
{
    "params": { ... exact API parameters ... },
    "response": { ... actual response data ... }
}
"""

import json
import time
from datetime import datetime
from pathlib import Path
from pure_crawler_api import PureCrawlerAPI

def test_and_save(name: str, test_type: str, params: dict, output_dir: Path):
    """Run a test and save params + response"""
    
    crawler = PureCrawlerAPI()
    
    print(f"\nTesting: {name}")
    print(f"Type: {test_type}")
    
    # Make the API call based on type
    if test_type == "collect":
        urls = params.get("urls", [])
        result = crawler.collect_by_url(urls)
        
    elif test_type == "discover":
        domain = params.get("domain")
        filter_pattern = params.get("filter", "")
        exclude = params.get("exclude", "")
        result = crawler.discover_by_domain(domain, filter_pattern, exclude)
    
    # Get the snapshot and poll for actual data
    response_data = None
    if "snapshot_id" in result:
        snapshot_id = result["snapshot_id"]
        print(f"  Snapshot: {snapshot_id}")
        print(f"  Polling...")
        
        # Poll for the actual data
        try:
            response_data = crawler.poll_until_ready(snapshot_id, poll_interval=3, timeout=60)
        except Exception as e:
            response_data = {"error": str(e), "snapshot_id": snapshot_id}
    else:
        response_data = result
    
    # Create the record
    record = {
        "test_name": name,
        "test_type": test_type,
        "timestamp": datetime.now().isoformat(),
        "params": params,
        "response": response_data
    }
    
    # Save to file
    filename = f"{name.lower().replace(' ', '_')}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Saved: {filename}")
    
    # Show summary
    if isinstance(response_data, list):
        print(f"  Got {len(response_data)} pages")
    elif isinstance(response_data, dict) and "error" in response_data:
        print(f"  ❌ Error: {response_data.get('error')}")
    
    return record


def main():
    # Create output directory with timestamp
    output_dir = Path("crawler_tests") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("SIMPLE CRAWLER API TESTER")
    print(f"Output: {output_dir}")
    print("="*60)
    
    # Define all tests with their params
    tests = [
        # Single URL collection
        {
            "name": "single_page_example",
            "type": "collect",
            "params": {
                "urls": ["https://example.com"]
            }
        },
        
        # Multiple URLs collection (batch)
        {
            "name": "batch_three_pages",
            "type": "collect",
            "params": {
                "urls": [
                    "https://httpbin.org/",
                    "https://httpbin.org/html",
                    "https://httpbin.org/forms/post"
                ]
            }
        },
        
        # Discover without filters
        {
            "name": "discover_example_all",
            "type": "discover",
            "params": {
                "domain": "https://example.com",
                "filter": "",
                "exclude": ""
            }
        },
        
        # Discover with filter
        {
            "name": "discover_httpbin_forms",
            "type": "discover",
            "params": {
                "domain": "https://httpbin.org",
                "filter": "/forms/*",
                "exclude": ""
            }
        },
        
        # Discover with exclude
        {
            "name": "discover_with_exclude",
            "type": "discover",
            "params": {
                "domain": "https://httpbin.org",
                "filter": "",
                "exclude": "/static/*"
            }
        }
    ]
    
    # Run all tests
    all_results = []
    
    for test in tests:
        try:
            result = test_and_save(
                test["name"],
                test["type"],
                test["params"],
                output_dir
            )
            all_results.append(result)
            
            # Small delay between tests
            time.sleep(2)
            
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            error_record = {
                "test_name": test["name"],
                "test_type": test["type"],
                "params": test["params"],
                "response": {"error": str(e)}
            }
            all_results.append(error_record)
    
    # Save a combined file with all tests
    combined_file = output_dir / "_all_tests.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*60)
    print(f"COMPLETE! {len(all_results)} tests run")
    print(f"Individual files in: {output_dir}")
    print(f"Combined file: {combined_file}")
    print("="*60)
    
    # List all files created
    print("\nFiles created:")
    for file in sorted(output_dir.glob("*.json")):
        size = file.stat().st_size
        print(f"  - {file.name} ({size:,} bytes)")


if __name__ == "__main__":
    main()