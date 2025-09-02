#!/usr/bin/env python3
"""
Test script for Crawler API integration
"""

import asyncio
import json
from dotenv import load_dotenv
from brightdata import crawl_single_url, crawl_website, CrawlerAPI
from brightdata.crawlerapi import crawl_url, crawl_domain

load_dotenv()


def test_direct_crawl_url():
    """Test direct crawl_url function"""
    print("\n=== Testing direct crawl_url ===")
    try:
        result = crawl_url("https://httpbin.org/html")
        print(f"Success: {result.success}")
        print(f"Status: {result.status}")
        print(f"Page count: {result.page_count}")
        if result.pages:
            page = result.pages[0]
            print(f"URL: {page.get('url')}")
            print(f"Markdown length: {len(page.get('markdown', ''))}")
            print(f"HTML length: {len(page.get('page_html', ''))}")
    except Exception as e:
        print(f"Error: {e}")


def test_auto_crawl_single():
    """Test auto.py's crawl_single_url"""
    print("\n=== Testing auto.crawl_single_url ===")
    try:
        result = crawl_single_url("https://httpbin.org/json")
        print(f"Success: {result.success}")
        print(f"Status: {result.status}")
        print(f"Page count: {result.page_count}")
    except Exception as e:
        print(f"Error: {e}")


def test_crawler_api_class():
    """Test CrawlerAPI class directly"""
    print("\n=== Testing CrawlerAPI class ===")
    try:
        api = CrawlerAPI()
        
        # Test collect_by_url
        print("\nCollecting single URL...")
        result = api.collect_by_url(["https://httpbin.org/forms/post"])
        print(f"Snapshot ID: {result.snapshot_id}")
        
        # Poll for results
        print("Polling for results...")
        result = api.poll_until_ready(result, poll_interval=5, timeout=60)
        print(f"Success: {result.success}")
        print(f"Status: {result.status}")
        print(f"Page count: {result.page_count}")
        
        if result.pages:
            # Analyze content
            result.analyze_content()
            print(f"URLs collected: {len(result.urls_collected)}")
            print(f"Formats available: {result.formats_available}")
            print(f"Total markdown chars: {result.total_markdown_chars}")
    except Exception as e:
        print(f"Error: {e}")


def test_discover_domain():
    """Test domain discovery"""
    print("\n=== Testing domain discovery ===")
    try:
        api = CrawlerAPI()
        
        # Discover with filter
        print("Discovering domain with filter...")
        result = api.discover_by_domain(
            "https://httpbin.org",
            filter_pattern="/forms/*",
            depth=1
        )
        print(f"Snapshot ID: {result.snapshot_id}")
        
        # Poll for results
        print("Polling for results...")
        result = api.poll_until_ready(result, poll_interval=5, timeout=120)
        print(f"Success: {result.success}")
        print(f"Status: {result.status}")
        print(f"Page count: {result.page_count}")
        
        if result.pages:
            print("URLs discovered:")
            for url in result.get_urls()[:5]:  # Show first 5
                print(f"  - {url}")
    except Exception as e:
        print(f"Error: {e}")


async def test_async_crawl():
    """Test async crawling"""
    print("\n=== Testing async crawling ===")
    try:
        from brightdata.crawlerapi import acrawl_url
        result = await acrawl_url("https://httpbin.org/anything")
        print(f"Success: {result.success}")
        print(f"Status: {result.status}")
        print(f"Page count: {result.page_count}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all tests"""
    print("Testing Crawler API Integration")
    print("=" * 50)
    
    # Test different access methods
    test_direct_crawl_url()
    test_auto_crawl_single()
    test_crawler_api_class()
    test_discover_domain()
    
    # Test async
    print("\nRunning async test...")
    asyncio.run(test_async_crawl())
    
    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    main()