#!/usr/bin/env python3
"""
test_quotes_site.py - Test on quotes.toscrape.com which has multiple linked pages
"""

import json
from pure_crawler_api import PureCrawlerAPI

def main():
    crawler = PureCrawlerAPI()
    
    # quotes.toscrape.com is a simple site designed for scraping with pagination
    test_url = "http://quotes.toscrape.com"
    
    print(f"Testing Crawler on: {test_url}")
    print("This site has multiple pages with quotes and pagination")
    print("="*50)
    
    # Test discover to get multiple pages
    print("\nTriggering Discover by Domain")
    print("-"*30)
    
    result = crawler.discover_by_domain(
        domain_url=test_url,
        filter="/page/*",  # Only get paginated pages
        exclude_filter=""
    )
    
    if "snapshot_id" in result:
        snapshot_id = result["snapshot_id"]
        print(f"✅ Discover Snapshot ID: {snapshot_id}")
        print("\nPolling (this will crawl multiple pages)...")
        
        data = crawler.poll_until_ready(snapshot_id, poll_interval=5, timeout=180)
        
        if isinstance(data, list):
            # Save the full result
            with open("sample_quotes_discover.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Saved {len(data)} pages to sample_quotes_discover.json")
            
            # Analyze discovered pages
            urls = [page.get('url', '') for page in data]
            
            print(f"\nDiscovered URLs:")
            for i, url in enumerate(urls, 1):
                title = data[i-1].get('page_title', 'N/A')
                markdown_len = len(data[i-1].get('markdown', ''))
                print(f"  {i}. {url}")
                print(f"     Title: {title}")
                print(f"     Markdown size: {markdown_len} chars")
            
            # Show a sample of content from the first page
            if data:
                first_page = data[0]
                markdown = first_page.get('markdown', '')
                if markdown:
                    print(f"\nSample content from first page:")
                    print("-"*30)
                    print(markdown[:500])
                    print("...")
        elif isinstance(data, dict) and "error" in data:
            print(f"Error: {data}")
            # Still save it for debugging
            with open("sample_quotes_error.json", 'w') as f:
                json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()