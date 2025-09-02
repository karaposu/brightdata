#!/usr/bin/env python3
"""
trigger_quotes_discover.py - Trigger discover on a site with multiple pages
"""

from pure_crawler_api import PureCrawlerAPI

def main():
    crawler = PureCrawlerAPI()
    
    # Let's try a few different sites
    sites = [
        {
            "url": "http://quotes.toscrape.com",
            "name": "Quotes site",
            "filter": "",  # Get all pages
            "exclude": ""
        },
        {
            "url": "https://books.toscrape.com",  
            "name": "Books site",
            "filter": "/catalogue/page-*.html",  # Get paginated pages
            "exclude": ""
        }
    ]
    
    print("Triggering discover operations on sites with multiple pages")
    print("="*60)
    
    for site in sites:
        print(f"\n{site['name']}: {site['url']}")
        
        result = crawler.discover_by_domain(
            domain_url=site['url'],
            filter=site['filter'],
            exclude_filter=site['exclude']
        )
        
        if "snapshot_id" in result:
            print(f"  ✅ Snapshot ID: {result['snapshot_id']}")
            print(f"     Poll with: python save_crawler_result.py {result['snapshot_id']}")
        else:
            print(f"  ❌ Error: {result}")
    
    print("\n" + "="*60)
    print("Use the commands above to poll the snapshots")

if __name__ == "__main__":
    main()