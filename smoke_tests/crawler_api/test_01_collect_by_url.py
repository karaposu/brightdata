#!/usr/bin/env python3
"""
Test 01: Crawler API - collect_by_url with different parameters

This test file validates the collect_by_url functionality with various parameter combinations.
Tests progress from basic single URL collection to advanced multi-URL scenarios.

python -m smoke_tests.crawler_api.test_01_collect_by_url

# https://docs.pydantic.dev/latest/
"""

import json
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI, crawl_url
from brightdata.models import CrawlResult

load_dotenv()


def print_test_header(test_num: int, description: str):
    """Print a formatted test header."""
    print(f"\n{'='*60}")
    print(f"TEST {test_num:02d}: {description}")
    print('='*60)


def print_result_summary(result: CrawlResult):
    """Print a summary of the CrawlResult."""
    print(f"  Success: {result.success}")
    print(f"  Status: {result.status}")
    print(f"  Pages collected: {result.page_count}")
    
    if result.success and result.pages:
        # Analyze content
        result.analyze_content()
        print(f"  Formats available: {result.formats_available}")
        print(f"  Total markdown chars: {result.total_markdown_chars:,}")
        print(f"  Total HTML chars: {result.total_html_chars:,}")
        
        # Show URLs collected
        urls = result.get_urls()
        print(f"  URLs collected: {len(urls)}")
        for url in urls[:3]:  # Show first 3
            print(f"    - {url}")
    
    if result.error:
        print(f"  Error: {result.error}")


def test_01_single_url_basic():
    """Test basic single URL collection."""
    print_test_header(1, "Basic Single URL Collection")
    
    api = CrawlerAPI()
    url = "https://httpbin.org/html"
    
    print(f"  Collecting: {url}")
    result = api.collect_by_url([url])
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=5, timeout=60)
    
    print_result_summary(result)
    return result.success


def test_02_single_url_with_errors():
    """Test single URL collection with include_errors parameter."""
    print_test_header(2, "Single URL with Error Details")
    
    api = CrawlerAPI()
    url = "https://httpbin.org/status/404"  # This will return 404
    
    print(f"  Collecting (with errors): {url}")
    result = api.collect_by_url([url], include_errors=True)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=5, timeout=60)
    
    print_result_summary(result)
    
    # Check for error information
    if result.pages:
        for page in result.pages:
            if page.get('error'):
                print(f"  Error details: {page.get('error')}")
    
    return True  # We expect this to handle errors gracefully


def test_03_multiple_urls():
    """Test collection of multiple URLs in one request."""
    print_test_header(3, "Multiple URLs Collection")
    
    api = CrawlerAPI()
    urls = [

       
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/xml"
    ]
    
    print(f"  Collecting {len(urls)} URLs...")
    for url in urls:
        print(f"    - {url}")
    
    result = api.collect_by_url(urls)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=5, timeout=90)
    
    print_result_summary(result)
    return result.success and result.page_count == len(urls)


def test_04_convenience_function():
    """Test the crawl_url convenience function."""
    print_test_header(4, "Convenience Function (crawl_url)")
    
    url = "https://httpbin.org/anything"
    
    print(f"  Using crawl_url for: {url}")
    result = crawl_url(url, poll_interval=5, timeout=60)
    
    print_result_summary(result)
    return result.success


def test_05_mixed_content_types():
    """Test collection of URLs with different content types."""
    print_test_header(5, "Mixed Content Types")
    
    api = CrawlerAPI()
    urls = [
        "https://httpbin.org/html",       # HTML content
        "https://httpbin.org/json",       # JSON response
        "https://httpbin.org/image/png",  # Binary image
    ]
    
    print(f"  Collecting mixed content types...")
    result = api.collect_by_url(urls, include_errors=True)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=5, timeout=90)
    
    print_result_summary(result)
    
    # Show content type details
    if result.pages:
        print("  Content analysis:")
        for page in result.pages:
            url = page.get('url', 'Unknown')
            has_markdown = bool(page.get('markdown'))
            has_html = bool(page.get('page_html'))
            has_text = bool(page.get('html2text'))
            print(f"    {url}:")
            print(f"      Markdown: {has_markdown}, HTML: {has_html}, Text: {has_text}")
    
    return result.success


def test_06_javascript_rendered_page():
    """Test collection of a page that requires JavaScript rendering."""
    print_test_header(6, "JavaScript-Rendered Page")
    
    api = CrawlerAPI()
    url = "https://docs.pydantic.dev/latest/"  # Simulates delayed response
    
    print(f"  Collecting JS-rendered page: {url}")
    result = api.collect_by_url([url])
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=5, timeout=90)
    
    print_result_summary(result)
    return result.success


def test_07_large_batch_collection():
    """Test collection of a larger batch of URLs."""
    print_test_header(7, "Large Batch Collection")
    
    api = CrawlerAPI()
    # Create a batch of URLs
    urls = [
        f"https://httpbin.org/anything?page={i}"
        for i in range(1, 6)  # 5 URLs
    ]
    
    print(f"  Collecting batch of {len(urls)} URLs...")
    result = api.collect_by_url(urls)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        start_time = time.time()
        result = api.poll_until_ready(result, poll_interval=5, timeout=120)
        elapsed = time.time() - start_time
        print(f"  Processing time: {elapsed:.2f} seconds")
    
    print_result_summary(result)
    return result.success and result.page_count == len(urls)


def test_08_markdown_extraction():
    """Test markdown extraction quality."""
    print_test_header(8, "Markdown Extraction Quality")
    
    api = CrawlerAPI()
    url = "https://httpbin.org/html"  # Has structured HTML
    
    print(f"  Collecting for markdown extraction: {url}")
    result = api.collect_by_url([url])
    
    if result.success and result.snapshot_id:
        result = api.poll_until_ready(result, poll_interval=5, timeout=60)
    
    print_result_summary(result)
    
    # Analyze markdown quality
    if result.success and result.pages:
        page = result.pages[0]
        markdown = page.get('markdown', '')
        
        print("  Markdown analysis:")
        print(f"    Has headers (#): {markdown.count('#') > 0}")
        print(f"    Has links: {'[' in markdown and ']' in markdown}")
        has_paragraphs = markdown.count('\n\n') > 0
        print(f"    Has paragraphs: {has_paragraphs}")
        print(f"    Clean formatting: {not markdown.startswith('<')}")
        
        # Show preview
        preview = markdown[:200].replace('\n', ' ')
        print(f"    Preview: {preview}...")
    
    return result.success


def test_09_error_handling():
    """Test error handling for invalid URLs."""
    print_test_header(9, "Error Handling")
    
    api = CrawlerAPI()
    urls = [
        "https://this-domain-definitely-does-not-exist-12345.com",
        "not-even-a-url",
        "https://httpbin.org/html",  # One valid URL
    ]
    
    print(f"  Collecting with invalid URLs...")
    result = api.collect_by_url(urls, include_errors=True)
    
    if result.success and result.snapshot_id:
        result = api.poll_until_ready(result, poll_interval=5, timeout=90)
    
    print_result_summary(result)
    
    # Show error handling
    if result.pages:
        print("  Error handling results:")
        for page in result.pages:
            url = page.get('url', 'Unknown')
            if page.get('error'):
                print(f"    {url}: ERROR - {page.get('error')}")
            else:
                print(f"    {url}: SUCCESS")
    
    return result.success  # Should still succeed even with errors


def test_10_performance_metrics():
    """Test with performance metrics tracking."""
    print_test_header(10, "Performance Metrics")
    
    api = CrawlerAPI()
    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/uuid",
    ]
    
    print(f"  Collecting with timing metrics...")
    
    # Track timing
    start_trigger = time.time()
    result = api.collect_by_url(urls)
    trigger_time = time.time() - start_trigger
    
    if result.success and result.snapshot_id:
        print(f"  Trigger time: {trigger_time:.3f}s")
        
        start_poll = time.time()
        result = api.poll_until_ready(result, poll_interval=5, timeout=90)
        poll_time = time.time() - start_poll
        print(f"  Poll time: {poll_time:.3f}s")
        print(f"  Total time: {trigger_time + poll_time:.3f}s")
    
    print_result_summary(result)
    
    # Calculate metrics
    if result.success and result.pages:
        total_chars = sum(len(p.get('markdown', '')) for p in result.pages)
        avg_chars = total_chars / len(result.pages) if result.pages else 0
        print(f"  Average chars per page: {avg_chars:,.0f}")
        print(f"  Processing speed: {total_chars/(poll_time+trigger_time):,.0f} chars/sec")
    
    return result.success


def main():
    """Run all tests and provide summary."""
    print("\n" + "="*60)
    print("CRAWLER API SMOKE TESTS - COLLECT BY URL")
    print("="*60)
    
    tests = [
        test_01_single_url_basic,
        test_02_single_url_with_errors,
        test_03_multiple_urls,
        test_04_convenience_function,
        test_05_mixed_content_types,
        test_06_javascript_rendered_page,
        test_07_large_batch_collection,
        test_08_markdown_extraction,
        test_09_error_handling,
        test_10_performance_metrics,
    ]
    
    results = []
    for test_func in tests:
        try:
            success = test_func()
            results.append((test_func.__name__, success))
            time.sleep(2)  # Small delay between tests
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            results.append((test_func.__name__, False))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    print("="*60)


if __name__ == "__main__":
    main()