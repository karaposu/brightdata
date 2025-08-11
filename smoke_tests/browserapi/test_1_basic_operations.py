#!/usr/bin/env python3
"""
Test 1: Browser API - Basic Operations
Tests basic fetching, strategies, result validation, and error handling
"""
# To run: python -m smoke_tests.browserapi.test_1_basic_operations

import os
import sys
import time
import asyncio
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from brightdata.browserapi import BrowserAPI
from brightdata.models import ScrapeResult
from dotenv import load_dotenv

load_dotenv()


async def test_01_demo_style_noop():
    """Test 01: Test noop strategy as shown in browser_api.py main()"""
    print("\n[Test 01] Demo-style noop strategy test...")
    
    # Use same config as main() demo
    api = BrowserAPI(
        strategy="noop",
        enable_wait_for_selector=True,
        block_patterns=["**/*.png", "**/*.css"]
    )
    
    urls = ["https://example.com", "https://openai.com"]
    
    try:
        all_good = True
        for url in urls:
            print(f"  Fetching {url}...")
            result = await api.fetch_async(url)
            
            if result.success:
                print(f"  ✓ noop: {url:>25} → {result.html_char_size} chars, "
                      f"${result.cost:.5f}, status={result.status}")
            else:
                print(f"  ✗ Failed: {url} - {result.error}")
                all_good = False
        
        await api.close()
        return all_good
        
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        try:
            await api.close()
        except:
            pass
        return False


async def test_02_async_fetch_noop():
    """Test 02: Basic async fetch with noop strategy"""
    print("\n[Test 02] Async fetch with noop strategy...")
    
    api = BrowserAPI(strategy="noop")
    test_url = "https://httpbin.org/html"
    
    print(f"  Async fetching {test_url}...")
    
    try:
        result = await api.fetch_async(test_url)
        
        if result.success:
            print("✓ Async fetch successful")
            print(f"  - HTML size: {len(result.data) if result.data else 0} chars")
            print(f"  - Root domain: {result.root_domain}")
            return True
        else:
            print(f"✗ Async fetch failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        return False


def test_03_wait_options():
    """Test 03: Test different wait_until options"""
    print("\n[Test 03] Testing wait_until options...")
    
    api = BrowserAPI()
    test_url = "https://example.com"
    
    wait_options = ["load", "domcontentloaded", "networkidle"]
    
    all_good = True
    for wait_opt in wait_options:
        print(f"\n  Testing wait_until='{wait_opt}'...")
        
        try:
            start = time.time()
            result = api.fetch(test_url, wait_until=wait_opt)
            elapsed = time.time() - start
            
            if result.success:
                print(f"✓ {wait_opt}: Success in {elapsed:.2f}s")
            else:
                print(f"✗ {wait_opt}: Failed - {result.error}")
                all_good = False
                
        except Exception as e:
            print(f"✗ {wait_opt}: Exception - {e}")
            all_good = False
    
    return all_good


def test_04_timeout_handling():
    """Test 04: Test timeout parameter"""
    print("\n[Test 04] Testing timeout handling...")
    
    api = BrowserAPI()
    
    # Test with a slow-loading page
    test_url = "https://httpbin.org/delay/5"
    
    # Test short timeout (should fail)
    print("  Testing with 2s timeout (should fail)...")
    try:
        result = api.fetch(test_url, timeout=2000)  # 2 seconds
        
        if not result.success:
            print("✓ Correctly timed out")
        else:
            print("✗ Should have timed out but succeeded")
            return False
            
    except Exception as e:
        print(f"✓ Timeout raised exception as expected: {type(e).__name__}")
    
    # Test longer timeout (should succeed)
    print("\n  Testing with 10s timeout (should succeed)...")
    try:
        result = api.fetch(test_url, timeout=10000)  # 10 seconds
        
        if result.success:
            print("✓ Succeeded with longer timeout")
            return True
        else:
            print(f"✗ Failed even with longer timeout: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Unexpected exception: {e}")
        return False


def test_05_window_size():
    """Test 05: Test different window sizes"""
    print("\n[Test 05] Testing window sizes...")
    
    api = BrowserAPI()
    test_url = "https://httpbin.org/html"
    
    window_sizes = [
        ((1920, 1080), "Desktop"),
        ((768, 1024), "Tablet"),
        ((375, 667), "Mobile"),
    ]
    
    all_good = True
    for size, description in window_sizes:
        print(f"\n  Testing {description} size {size}...")
        
        try:
            result = api.fetch(test_url, window_size=size)
            
            if result.success:
                print(f"✓ {description} fetch successful")
            else:
                print(f"✗ {description} fetch failed: {result.error}")
                all_good = False
                
        except Exception as e:
            print(f"✗ {description} test failed: {e}")
            all_good = False
    
    return all_good


def test_06_headless_mode():
    """Test 06: Test headless vs headed mode"""
    print("\n[Test 06] Testing headless mode...")
    
    api = BrowserAPI()
    test_url = "https://example.com"
    
    # Test headless (default)
    print("  Testing headless=True...")
    try:
        result = api.fetch(test_url, headless=True)
        if result.success:
            print("✓ Headless mode works")
        else:
            print(f"✗ Headless mode failed: {result.error}")
            return False
    except Exception as e:
        print(f"✗ Headless test failed: {e}")
        return False
    
    # Test headed (if supported)
    print("\n  Testing headless=False...")
    try:
        result = api.fetch(test_url, headless=False)
        if result.success:
            print("✓ Headed mode works")
            return True
        else:
            print(f"⚠ Headed mode not supported: {result.error}")
            return True  # Not a failure, just not supported
    except Exception as e:
        print(f"⚠ Headed mode not supported: {e}")
        return True  # Not a failure


def test_07_cost_tracking():
    """Test 07: Test cost calculation and tracking"""
    print("\n[Test 07] Testing cost tracking...")
    
    api = BrowserAPI()
    
    # Reset tracking
    api.total_bytes = 0
    api.total_cost = 0.0
    
    test_url = "https://httpbin.org/html"
    
    try:
        # First request
        result1 = api.fetch(test_url)
        
        if result1.success:
            cost1 = result1.cost or 0
            print(f"✓ First request cost: ${cost1:.6f}")
            
            # Check tracking
            if api.total_bytes > 0:
                print(f"✓ Total bytes tracked: {api.total_bytes}")
            if api.total_cost > 0:
                print(f"✓ Total cost tracked: ${api.total_cost:.6f}")
            
            # Second request
            result2 = api.fetch(test_url)
            
            if result2.success:
                cost2 = result2.cost or 0
                print(f"✓ Second request cost: ${cost2:.6f}")
                
                # Verify accumulation
                expected_total = cost1 + cost2
                if abs(api.total_cost - expected_total) < 0.0001:
                    print(f"✓ Cost accumulation correct: ${api.total_cost:.6f}")
                    return True
                else:
                    print(f"✗ Cost mismatch: expected ${expected_total:.6f}, got ${api.total_cost:.6f}")
                    return False
        
        print("✗ Requests failed")
        return False
        
    except Exception as e:
        print(f"✗ Cost tracking test failed: {e}")
        return False


def test_08_domain_extraction():
    """Test 08: Test domain extraction functionality"""
    print("\n[Test 08] Testing domain extraction...")
    
    api = BrowserAPI()
    
    test_cases = [
        ("https://www.example.com/page", "example"),
        ("https://blog.example.co.uk/", "example"),
        ("https://subdomain.test.org", "test"),
        ("https://example.com:8080/", "example"),
    ]
    
    all_good = True
    for url, expected in test_cases:
        extracted = api._extract_root(url)
        
        if extracted == expected:
            print(f"✓ {url} → {extracted}")
        else:
            print(f"✗ {url} → {extracted} (expected {expected})")
            all_good = False
    
    return all_good


async def test_09_semaphore_strategy():
    """Test 09: Test semaphore strategy limiting"""
    print("\n[Test 09] Testing semaphore strategy...")
    
    api = BrowserAPI(strategy="semaphore", max_concurrent=2)
    test_url = "https://httpbin.org/delay/1"
    
    print("  Testing concurrent limit of 2...")
    
    try:
        start = time.time()
        
        # Launch 4 requests (should process 2 at a time)
        tasks = [api.fetch_async(test_url) for _ in range(4)]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        
        success_count = sum(1 for r in results if r.success)
        print(f"✓ Completed {len(results)} requests in {elapsed:.2f}s")
        print(f"  - Successes: {success_count}/{len(results)}")
        
        # With 2 concurrent and 1s delay, should take ~2s
        if elapsed > 1.5:  # Allow some overhead
            print("✓ Semaphore correctly limited concurrency")
            return True
        else:
            print("✗ Requests completed too fast - semaphore not working")
            return False
            
    except Exception as e:
        print(f"✗ Semaphore test failed: {e}")
        return False


def test_10_error_recovery():
    """Test 10: Test error recovery and resilience"""
    print("\n[Test 10] Testing error recovery...")
    
    api = BrowserAPI()
    
    # Test various problematic URLs
    error_urls = [
        ("https://invalid-domain-12345.com", "Invalid domain"),
        ("not-a-url", "Invalid URL format"),
        ("https://httpbin.org/status/404", "404 page"),
        ("https://httpbin.org/status/500", "500 error"),
    ]
    
    all_good = True
    for test_url, description in error_urls:
        print(f"\n  Testing {description}...")
        
        try:
            result = api.fetch(test_url)
            
            # Should return ScrapeResult with success=False
            if isinstance(result, ScrapeResult):
                if not result.success:
                    print(f"✓ Correctly handled {description}")
                else:
                    # Some error pages might still return content
                    print(f"⚠ Got success for {description} (may be valid)")
            else:
                print(f"✗ Invalid result type for {description}")
                all_good = False
                
        except Exception as e:
            print(f"⚠ Exception for {description}: {type(e).__name__}")
            # Some errors might raise exceptions, which is acceptable
    
    return all_good


def main():
    """Run all basic operation tests"""
    print("=" * 60)
    print("Browser API - Test Suite 1: Basic Operations")
    print("=" * 60)
    
    sync_tests = [
        test_03_wait_options,
        test_04_timeout_handling,
        test_05_window_size,
        test_06_headless_mode,
        test_07_cost_tracking,
        test_08_domain_extraction,
        test_10_error_recovery,
    ]
    
    async_tests = [
        test_01_demo_style_noop,
        test_02_async_fetch_noop,
        test_09_semaphore_strategy,
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
    success = main()
    sys.exit(0 if success else 1)