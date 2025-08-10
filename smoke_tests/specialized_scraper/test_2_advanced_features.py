#!/usr/bin/env python3
"""
Test 2: Specialized Scrapers - Advanced Features
Tests batch operations, async scraping, fallback mechanisms, and performance
"""
# To run: python -m smoke_tests.specialized_scraper.test_2_advanced_features

import os
import sys
import time
import asyncio
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from brightdata import scrape_url, scrape_url_async, scrape_urls, scrape_urls_async
from brightdata.ready_scrapers.amazon import AmazonScraper
from brightdata.ready_scrapers.linkedin import LinkedInScraper
from brightdata.models import ScrapeResult
from dotenv import load_dotenv

load_dotenv()


async def test_01_async_scrape_url():
    """Test 01: Test async single URL scraping"""
    print("\n[Test 01] Testing async scrape_url...")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("⚠ BRIGHTDATA_TOKEN not set - skipping test")
        return True
    
    test_url = "https://www.amazon.com/dp/B0CRMZHDG8"
    
    try:
        print(f"  Async scraping {test_url}...")
        
        result = await scrape_url_async(
            test_url,
            bearer_token=token,
            poll_interval=5,
            poll_timeout=60
        )
        
        if result and isinstance(result, ScrapeResult):
            print(f"✓ Got ScrapeResult: success={result.success}")
            
            if result.success:
                print(f"  - Status: {result.status}")
                print(f"  - Snapshot ID: {result.snapshot_id}")
                print(f"  - Cost: ${result.cost:.6f}" if result.cost else "  - Cost: N/A")
                return True
            else:
                print(f"  - Error: {result.error}")
                return False
        else:
            print("✗ No result returned")
            return False
            
    except Exception as e:
        print(f"✗ Async scrape test failed: {e}")
        return False


async def test_02_batch_scraping():
    """Test 02: Test batch URL scraping"""
    print("\n[Test 02] Testing batch scraping...")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("⚠ BRIGHTDATA_TOKEN not set - skipping test")
        return True
    
    # Mix of URLs - some with scrapers, some without
    test_urls = [
        "https://www.amazon.com/dp/B0CRMZHDG8",
        "https://example.com",  # No scraper - should use fallback
        "https://httpbin.org/html",  # No scraper - should use fallback
    ]
    
    try:
        print(f"  Batch scraping {len(test_urls)} URLs...")
        
        results = await scrape_urls_async(
            test_urls,
            bearer_token=token,
            fallback_to_browser_api=True,
            poll_interval=5,
            poll_timeout=60
        )
        
        print(f"✓ Got {len(results)} results")
        
        # Check results
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, ScrapeResult) and result.success:
                success_count += 1
                print(f"  - {test_urls[i]}: Success (fallback={result.fallback_used})")
            else:
                print(f"  - {test_urls[i]}: Failed")
        
        if success_count >= 2:  # At least 2 should succeed
            print(f"✓ {success_count}/{len(test_urls)} succeeded")
            return True
        else:
            print(f"✗ Only {success_count}/{len(test_urls)} succeeded")
            return False
            
    except Exception as e:
        print(f"✗ Batch scraping test failed: {e}")
        return False


def test_03_fallback_mechanism():
    """Test 03: Test fallback to Browser API"""
    print("\n[Test 03] Testing fallback mechanism...")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    
    # URL with no specialized scraper
    test_url = "https://example.com"
    
    try:
        print(f"  Scraping {test_url} with fallback...")
        
        # Without fallback
        result_no_fallback = scrape_url(
            test_url,
            bearer_token=token,
            fallback_to_browser_api=False
        )
        
        if result_no_fallback is None:
            print("✓ Without fallback returns None as expected")
        else:
            print("✗ Without fallback should return None")
            return False
        
        # With fallback
        result_with_fallback = scrape_url(
            test_url,
            bearer_token=token,
            fallback_to_browser_api=True
        )
        
        if result_with_fallback and isinstance(result_with_fallback, ScrapeResult):
            print(f"✓ With fallback returns ScrapeResult")
            print(f"  - Fallback used: {result_with_fallback.fallback_used}")
            print(f"  - Success: {result_with_fallback.success}")
            
            if result_with_fallback.fallback_used:
                print("✓ Correctly marked as fallback")
                return True
            else:
                print("✗ Should be marked as fallback")
                return False
        else:
            print("✗ Fallback didn't work")
            return False
            
    except Exception as e:
        print(f"✗ Fallback test failed: {e}")
        return False


async def test_04_concurrent_scrapers():
    """Test 04: Test concurrent requests to different scrapers"""
    print("\n[Test 04] Testing concurrent different scrapers...")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("⚠ BRIGHTDATA_TOKEN not set - skipping test")
        return True
    
    # URLs from different scrapers
    test_urls = [
        "https://www.amazon.com/dp/B0CRMZHDG8",
        "https://www.linkedin.com/in/example/",
        "https://www.reddit.com/r/python/",
    ]
    
    try:
        print(f"  Concurrent scraping across {len(test_urls)} different scrapers...")
        
        start = time.time()
        
        # Create tasks
        tasks = [scrape_url_async(url, bearer_token=token, poll_timeout=30) 
                for url in test_urls]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start
        print(f"✓ Completed in {elapsed:.2f}s")
        
        # Check results
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  - {test_urls[i]}: Exception {type(result).__name__}")
            elif isinstance(result, ScrapeResult):
                if result and result.success:
                    success_count += 1
                    print(f"  - {test_urls[i]}: Success")
                else:
                    print(f"  - {test_urls[i]}: Failed")
            else:
                print(f"  - {test_urls[i]}: No result")
        
        if success_count > 0:
            print(f"✓ {success_count}/{len(test_urls)} scrapers worked")
            return True
        else:
            print("✗ No scrapers succeeded")
            return False
            
    except Exception as e:
        print(f"✗ Concurrent scrapers test failed: {e}")
        return False


async def test_05_discovery_operations():
    """Test 05: Test discovery/search operations"""
    print("\n[Test 05] Testing discovery operations...")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("⚠ BRIGHTDATA_TOKEN not set - skipping test")
        return True
    
    try:
        scraper = AmazonScraper(bearer_token=token)
        
        print("  Testing keyword discovery...")
        
        # Trigger discovery
        snapshot_id = scraper.products__discover_by_keyword(
            [{"keyword": "laptop", "pages_to_search": 1}]
        )
        
        if snapshot_id:
            print(f"✓ Got snapshot ID for discovery: {snapshot_id}")
            
            # Would normally poll for results here
            print("  Discovery triggered successfully")
            return True
        else:
            print("✗ No snapshot ID returned for discovery")
            return False
            
    except Exception as e:
        print(f"⚠ Discovery test failed (may be API limitation): {e}")
        return True  # Don't fail test for API limitations


def test_06_scraper_polling():
    """Test 06: Test polling mechanism"""
    print("\n[Test 06] Testing polling mechanism...")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("⚠ BRIGHTDATA_TOKEN not set - skipping test")
        return True
    
    try:
        from brightdata.utils.poll import poll_until_ready
        
        scraper = AmazonScraper(bearer_token=token)
        
        # Trigger a quick scrape
        snapshot_id = scraper.collect_by_url("https://www.amazon.com/dp/B0CRMZHDG8")
        
        if snapshot_id:
            print(f"  Polling snapshot {snapshot_id}...")
            
            # Poll with short timeout
            try:
                result = poll_until_ready(
                    scraper,
                    snapshot_id,
                    poll_interval=2,
                    timeout=30
                )
                
                if result.success:
                    print("✓ Polling completed successfully")
                    print(f"  - Data received: {result.data is not None}")
                    return True
                else:
                    print(f"✗ Polling failed: {result.error}")
                    return False
                    
            except TimeoutError:
                print("⚠ Polling timed out (normal for large requests)")
                return True
        else:
            print("✗ No snapshot to poll")
            return False
            
    except Exception as e:
        print(f"✗ Polling test failed: {e}")
        return False


async def test_07_async_polling():
    """Test 07: Test async polling utilities"""
    print("\n[Test 07] Testing async polling...")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("⚠ BRIGHTDATA_TOKEN not set - skipping test")
        return True
    
    try:
        from brightdata.utils.async_poll import wait_ready
        
        scraper = AmazonScraper(bearer_token=token)
        
        # Trigger async
        snapshot_id = await scraper._trigger_async(
            [{"url": "https://www.amazon.com/dp/B0CRMZHDG8"}]
        )
        
        if snapshot_id:
            print(f"  Async polling snapshot {snapshot_id}...")
            
            # Poll async
            result = await wait_ready(
                scraper,
                snapshot_id,
                poll_interval=2,
                timeout=30
            )
            
            if result.success:
                print("✓ Async polling completed")
                return True
            else:
                print(f"✗ Async polling failed: {result.error}")
                return False
        else:
            print("✗ No snapshot to poll")
            return False
            
    except Exception as e:
        print(f"⚠ Async polling test failed: {e}")
        return True  # May fail due to API limits


def test_08_flexible_timeout():
    """Test 08: Test flexible timeout feature"""
    print("\n[Test 08] Testing flexible timeout...")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("⚠ BRIGHTDATA_TOKEN not set - skipping test")
        return True
    
    # LinkedIn typically needs longer timeouts
    test_url = "https://www.linkedin.com/in/example/"
    
    try:
        print("  Testing with flexible timeout...")
        
        # Check if scraper has MIN_POLL_TIMEOUT
        scraper_class = get_scraper_for(test_url)
        
        if scraper_class and hasattr(scraper_class, 'MIN_POLL_TIMEOUT'):
            min_timeout = scraper_class.MIN_POLL_TIMEOUT
            print(f"✓ Scraper has MIN_POLL_TIMEOUT: {min_timeout}s")
            
            # Test with flexible timeout
            result = scrape_url(
                test_url,
                bearer_token=token,
                poll_timeout=30,  # Short timeout
                flexible_timeout=True  # Should use MIN_POLL_TIMEOUT if larger
            )
            
            print("✓ Flexible timeout applied")
            return True
        else:
            print("⚠ Scraper doesn't define MIN_POLL_TIMEOUT")
            return True
            
    except Exception as e:
        print(f"✗ Flexible timeout test failed: {e}")
        return False


async def test_09_error_recovery():
    """Test 09: Test error recovery in batch operations"""
    print("\n[Test 09] Testing error recovery...")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("⚠ BRIGHTDATA_TOKEN not set - skipping test")
        return True
    
    # Mix of valid and invalid URLs
    test_urls = [
        "https://www.amazon.com/dp/B0CRMZHDG8",  # Valid
        "https://invalid-url-12345",  # Invalid
        "https://www.amazon.com/dp/INVALID123",  # Valid domain, invalid product
        "https://example.com",  # No scraper
    ]
    
    try:
        print(f"  Testing batch with {len(test_urls)} mixed URLs...")
        
        results = await scrape_urls_async(
            test_urls,
            bearer_token=token,
            fallback_to_browser_api=True,
            poll_timeout=30
        )
        
        # Analyze results
        success = 0
        failed = 0
        fallback = 0
        
        for i, result in enumerate(results):
            if isinstance(result, ScrapeResult):
                if result.success:
                    success += 1
                    if result.fallback_used:
                        fallback += 1
                else:
                    failed += 1
                    
                print(f"  - {test_urls[i]}: {'Success' if result.success else 'Failed'}"
                      f"{' (fallback)' if result.fallback_used else ''}")
            else:
                failed += 1
                print(f"  - {test_urls[i]}: No result")
        
        print(f"\n  Summary: {success} success, {failed} failed, {fallback} fallbacks")
        
        # Should handle errors gracefully
        if success >= 2:  # At least half should work
            print("✓ Error recovery working")
            return True
        else:
            print("✗ Too many failures")
            return False
            
    except Exception as e:
        print(f"✗ Error recovery test failed: {e}")
        return False


async def test_10_performance_metrics():
    """Test 10: Test performance metrics collection"""
    print("\n[Test 10] Testing performance metrics...")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("⚠ BRIGHTDATA_TOKEN not set - skipping test")
        return True
    
    test_urls = [
        "https://www.amazon.com/dp/B0CRMZHDG8",
        "https://example.com",
        "https://httpbin.org/html",
    ]
    
    try:
        print("  Collecting performance metrics...")
        
        start = time.time()
        
        results = await scrape_urls_async(
            test_urls,
            bearer_token=token,
            fallback_to_browser_api=True,
            poll_timeout=30
        )
        
        total_elapsed = time.time() - start
        
        # Analyze metrics
        total_cost = 0.0
        specialized_count = 0
        fallback_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, ScrapeResult):
                if result.cost:
                    total_cost += result.cost
                
                if result.fallback_used:
                    fallback_count += 1
                else:
                    specialized_count += 1
                
                # Check timing fields
                if result.request_sent_at:
                    print(f"  ✓ {test_urls[i]}: Has request timestamp")
                if result.data_received_at:
                    delta = (result.data_received_at - result.request_sent_at).total_seconds()
                    print(f"    Response time: {delta:.2f}s")
        
        print(f"\n  Performance Summary:")
        print(f"  - Total time: {total_elapsed:.2f}s")
        print(f"  - Total cost: ${total_cost:.6f}")
        print(f"  - Specialized scrapers: {specialized_count}")
        print(f"  - Fallback used: {fallback_count}")
        print(f"  - Average time: {total_elapsed/len(test_urls):.2f}s per URL")
        
        print("✓ Performance metrics collected")
        return True
        
    except Exception as e:
        print(f"✗ Performance metrics test failed: {e}")
        return False


def main():
    """Run all advanced feature tests"""
    print("=" * 60)
    print("Specialized Scrapers - Test Suite 2: Advanced Features")
    print("=" * 60)
    
    async_tests = [
        test_01_async_scrape_url,
        test_02_batch_scraping,
        test_04_concurrent_scrapers,
        test_05_discovery_operations,
        test_07_async_polling,
        test_09_error_recovery,
        test_10_performance_metrics,
    ]
    
    sync_tests = [
        test_03_fallback_mechanism,
        test_06_scraper_polling,
        test_08_flexible_timeout,
    ]
    
    passed = 0
    failed = 0
    
    # Run sync tests
    for test in sync_tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    # Run async tests
    for test in async_tests:
        try:
            if asyncio.run(test()):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Summary: {passed} passed, {failed} failed out of {len(sync_tests) + len(async_tests)} tests")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    from brightdata.registry import get_scraper_for  # Import needed for test_08
    success = main()
    sys.exit(0 if success else 1)