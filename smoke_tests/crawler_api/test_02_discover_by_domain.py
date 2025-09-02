#!/usr/bin/env python3
"""
Test 02: Crawler API - discover_by_domain with incremental parameter testing

This test file validates the discover_by_domain functionality for crawling entire domains.
Tests are incremental and isolated, starting from the simplest case and gradually adding parameters.

NOTE: Discovery operations can take 5-10+ minutes to complete as they crawl entire domains.
      Consider running with longer timeouts or using smaller test domains.

python -m smoke_tests.crawler_api.test_02_discover_by_domain
"""

import time
from dotenv import load_dotenv
from brightdata.crawlerapi import CrawlerAPI, crawl_domain
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
    print(f"  Operation: {result.operation}")
    print(f"  Pages discovered: {result.page_count}")
    
    if result.crawl_params:
        print(f"  Crawl parameters used:")
        for key, value in result.crawl_params.items():
            if value not in [None, "", []]:
                print(f"    - {key}: {value}")
    
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        print(f"  Total URLs discovered: {len(urls)}")
        
        # Show sample URLs
        if urls:
            print(f"  Sample URLs (first 5):")
            for url in urls[:5]:
                print(f"    - {url}")
    
    if result.error:
        print(f"  Error: {result.error}")


def test_01_basic_domain_discovery():
    """Test basic domain discovery with default parameters."""
    print_test_header(1, "Basic Domain Discovery (defaults)")
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters: All defaults (no depth, filter, or exclude)")
    
    result = api.discover_by_domain(domain)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        print(f"  Polling for results (may take 5+ minutes)...")
        result = api.poll_until_ready(result, poll_interval=20, timeout=600)
    
    print_result_summary(result)
    return result.success


def test_02_domain_with_depth_limit_0():
    """Test domain discovery with depth=0 (single page only)."""
    print_test_header(2, "Domain with depth=0")
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters: depth=0 (single page only)")
    
    result = api.discover_by_domain(domain, depth=0)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=15, timeout=300)
    
    print_result_summary(result)
    
    # Verify depth=0 behavior
    if result.success and result.pages:
        print(f"  Verification: Should have exactly 1 page")
        print(f"  Actual page count: {result.page_count}")
    
    return result.success and result.page_count == 1


def test_03_domain_with_depth_limit_1():
    """Test domain discovery with depth=1 (page + direct links)."""
    print_test_header(3, "Domain with depth=1")
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters: depth=1 (main page + direct links)")
    
    result = api.discover_by_domain(domain, depth=1)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=15, timeout=400)
    
    print_result_summary(result)
    
    # Verify depth=1 found more than depth=0
    if result.success and result.pages:
        print(f"  Verification: Should have multiple pages")
        print(f"  Found {result.page_count} pages at depth=1")
    
    return result.success and result.page_count > 1


def test_04_domain_with_depth_limit_2():
    """Test domain discovery with depth=2 (two levels deep)."""
    print_test_header(4, "Domain with depth=2")
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters: depth=2 (follow links two levels deep)")
    
    result = api.discover_by_domain(domain, depth=2)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        print(f"  Polling (deeper crawls take longer, may take 5+ minutes)...")
        result = api.poll_until_ready(result, poll_interval=20, timeout=600)
    
    print_result_summary(result)
    
    # Analyze depth distribution
    if result.success and result.pages:
        print(f"  Verification: Should have more pages than depth=1")
        print(f"  Found {result.page_count} pages at depth=2")
    
    return result.success


def test_05_domain_with_filter_pattern():
    """Test domain discovery with filter pattern only."""
    print_test_header(5, "Domain with Filter Pattern")
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    filter_pattern = "/status/*"
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters: filter_pattern='{filter_pattern}'")
    print(f"  Note: No depth specified (using default)")
    
    result = api.discover_by_domain(domain, filter_pattern=filter_pattern)
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=15, timeout=400)
    
    print_result_summary(result)
    
    # Verify filter worked
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        matching_urls = [u for u in urls if "/status" in u]
        print(f"  Verification: All URLs should match '/status/*'")
        print(f"  Matching URLs: {len(matching_urls)}/{len(urls)}")
    
    return result.success


def test_06_domain_with_filter_pattern_and_depth():
    """Test domain discovery with both filter pattern and depth."""
    print_test_header(6, "Domain with Filter Pattern and Depth")
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    filter_pattern = "/forms/*"
    depth = 1
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters:")
    print(f"    - filter_pattern: '{filter_pattern}'")
    print(f"    - depth: {depth}")
    
    result = api.discover_by_domain(
        domain,
        filter_pattern=filter_pattern,
        depth=depth
    )
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=15, timeout=400)
    
    print_result_summary(result)
    
    # Verify both parameters worked
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        forms_urls = [u for u in urls if "/forms" in u]
        print(f"  Verification:")
        print(f"    - URLs with '/forms': {len(forms_urls)}/{len(urls)}")
        print(f"    - Depth limited crawl: {result.page_count} pages")
    
    return result.success


def test_07_domain_with_exclude_pattern():
    """Test domain discovery with exclude pattern."""
    print_test_header(7, "Domain with Exclude Pattern")
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    exclude_pattern = "*/image/*,*/bytes/*"
    depth = 1
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters:")
    print(f"    - exclude_pattern: '{exclude_pattern}'")
    print(f"    - depth: {depth}")
    
    result = api.discover_by_domain(
        domain,
        exclude_pattern=exclude_pattern,
        depth=depth
    )
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=15, timeout=400)
    
    print_result_summary(result)
    
    # Verify exclusion worked
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        excluded_count = len([u for u in urls if "/image" in u or "/bytes" in u])
        print(f"  Verification: No URLs should contain '/image' or '/bytes'")
        print(f"  Excluded URLs found: {excluded_count} (should be 0)")
    
    return result.success and excluded_count == 0


def test_08_domain_with_all_parameters():
    """Test with filter, exclude, and depth all specified."""
    print_test_header(8, "Domain with All Parameters")
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    filter_pattern = "/*"  # Include all
    exclude_pattern = "*/delay/*,*/stream/*"  # Exclude slow endpoints
    depth = 1
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters:")
    print(f"    - filter_pattern: '{filter_pattern}'")
    print(f"    - exclude_pattern: '{exclude_pattern}'")
    print(f"    - depth: {depth}")
    
    result = api.discover_by_domain(
        domain,
        filter_pattern=filter_pattern,
        exclude_pattern=exclude_pattern,
        depth=depth
    )
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=15, timeout=400)
    
    print_result_summary(result)
    
    # Verify all parameters worked
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        delay_urls = len([u for u in urls if "/delay" in u])
        stream_urls = len([u for u in urls if "/stream" in u])
        print(f"  Verification:")
        print(f"    - Total pages at depth=1: {result.page_count}")
        print(f"    - URLs with '/delay': {delay_urls} (should be 0)")
        print(f"    - URLs with '/stream': {stream_urls} (should be 0)")
    
    return result.success


def test_09_ignore_sitemap_parameter():
    """Test ignore_sitemap parameter."""
    print_test_header(9, "Domain with ignore_sitemap")
    
    api = CrawlerAPI()
    domain = "https://httpbin.org"
    
    print(f"  Discovering domain: {domain}")
    print(f"  Parameters:")
    print(f"    - ignore_sitemap: True")
    print(f"    - depth: 1")
    
    result = api.discover_by_domain(
        domain,
        ignore_sitemap=True,
        depth=1
    )
    
    if result.success and result.snapshot_id:
        print(f"  Snapshot ID: {result.snapshot_id}")
        result = api.poll_until_ready(result, poll_interval=15, timeout=400)
    
    print_result_summary(result)
    
    print(f"  Note: ignore_sitemap tells crawler to discover links organically")
    print(f"        rather than using sitemap.xml if available")
    
    return result.success


def test_10_convenience_crawl_domain():
    """Test the crawl_domain convenience function."""
    print_test_header(10, "Convenience Function crawl_domain()")
    
    domain = "https://httpbin.org"
    
    print(f"  Using crawl_domain() for: {domain}")
    print(f"  Parameters:")
    print(f"    - filter_pattern: '/status/*'")
    print(f"    - depth: 1")
    
    # Use convenience function
    result = crawl_domain(
        domain,
        filter_pattern="/status/*",
        depth=1,
        poll_interval=15,
        timeout=400
    )
    
    print_result_summary(result)
    
    # Verify it worked
    if result.success and result.pages:
        urls = [p.get('url') for p in result.pages]
        status_urls = [u for u in urls if "/status" in u]
        print(f"  Verification: Using convenience function")
        print(f"    - URLs with '/status': {len(status_urls)}/{len(urls)}")
    
    return result.success


def main():
    """Run all tests and provide summary."""
    print("\n" + "="*60)
    print("CRAWLER API SMOKE TESTS - DISCOVER BY DOMAIN")
    print("Incremental and Isolated Parameter Testing")
    print("="*60)
    
    tests = [
        test_01_basic_domain_discovery,
        test_02_domain_with_depth_limit_0,
        test_03_domain_with_depth_limit_1,
        test_04_domain_with_depth_limit_2,
        test_05_domain_with_filter_pattern,
        test_06_domain_with_filter_pattern_and_depth,
        test_07_domain_with_exclude_pattern,
        test_08_domain_with_all_parameters,
        test_09_ignore_sitemap_parameter,
        test_10_convenience_crawl_domain,
    ]
    
    results = []
    for test_func in tests:
        try:
            success = test_func()
            results.append((test_func.__name__, success))
            time.sleep(3)  # Delay between tests
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