#!/usr/bin/env python3
"""
test_crawl_real_site.py - Test crawler on a site with actual links
"""

import json
from pure_crawler_api import PureCrawlerAPI

def main():
    crawler = PureCrawlerAPI()
    
    # Let's try with a documentation site or blog that has multiple pages
    # Some options that should have multiple linked pages:
    sites_to_try = [
        "https://docs.python.org/3/tutorial/",  # Python tutorial - has many linked pages
        "https://httpbin.org",  # HTTP testing service - has multiple endpoints
        "https://www.scrapethissite.com",  # A site designed for scraping practice
    ]
    
    # Let's use httpbin.org as it's designed for testing
    test_url = "https://httpbin.org"
    
    print(f"Testing Crawler on: {test_url}")
    print("="*50)
    
    # Test 1: Collect a specific page with links
    print("\n1. Testing Collect by URL")
    print("-"*30)
    
    result = crawler.collect_by_url([test_url])
    
    if "snapshot_id" in result:
        snapshot_id = result["snapshot_id"]
        print(f"Snapshot ID: {snapshot_id}")
        print("Polling...")
        
        data = crawler.poll_until_ready(snapshot_id, poll_interval=5, timeout=120)
        
        if isinstance(data, list):
            with open("sample_httpbin_collect.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {len(data)} pages to sample_httpbin_collect.json")
            
            # Analyze content
            for page in data:
                url = page.get('url', 'N/A')
                title = page.get('page_title', 'N/A')
                markdown = page.get('markdown', '')
                
                # Count links in markdown
                link_count = markdown.count('](')  # Simple count of markdown links
                
                print(f"\nPage: {url}")
                print(f"  Title: {title}")
                print(f"  Markdown length: {len(markdown)} chars")
                print(f"  Approximate link count: {link_count}")
    
    # Test 2: Discover the domain (crawl all pages)
    print("\n\n2. Testing Discover by Domain")
    print("-"*30)
    
    result = crawler.discover_by_domain(
        domain_url=test_url,
        filter="",  # Get everything
        exclude_filter=""  # Don't exclude anything
    )
    
    if "snapshot_id" in result:
        snapshot_id = result["snapshot_id"]
        print(f"Snapshot ID: {snapshot_id}")
        print("Polling (this may take longer)...")
        
        data = crawler.poll_until_ready(snapshot_id, poll_interval=10, timeout=300)
        
        if isinstance(data, list):
            with open("sample_httpbin_discover.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {len(data)} pages to sample_httpbin_discover.json")
            
            # Analyze discovered URLs
            urls = [page.get('url', '') for page in data]
            
            # Categorize URLs
            base_domain = test_url.replace('https://', '').replace('http://', '')
            internal_urls = [u for u in urls if base_domain in u]
            external_urls = [u for u in urls if base_domain not in u]
            
            print(f"\nDiscovery Results:")
            print(f"  Total pages: {len(urls)}")
            print(f"  Internal URLs: {len(internal_urls)}")
            print(f"  External URLs: {len(external_urls)}")
            
            print(f"\n  Sample Internal URLs:")
            for url in internal_urls[:10]:
                print(f"    - {url}")
            
            if external_urls:
                print(f"\n  Sample External URLs:")
                for url in external_urls[:5]:
                    print(f"    - {url}")

if __name__ == "__main__":
    main()