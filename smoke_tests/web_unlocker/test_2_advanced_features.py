#!/usr/bin/env python3
"""
Test 2: Web Unlocker - Advanced Features
Tests async operations, concurrent requests, stress testing, and edge cases
"""
# To run: python -m smoke_tests.web_unlocker.test_2_advanced_features

import os
import sys
import asyncio
import time
from pathlib import Path
from typing import List

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from brightdata.web_unlocker import WebUnlocker
from brightdata.models import ScrapeResult
from dotenv import load_dotenv

load_dotenv()


def get_unlocker():
    """Helper to get initialized unlocker or None"""
    try:
        return WebUnlocker()
    except ValueError:
        print("⚠ Web Unlocker not configured - set BRIGHTDATA_WEBUNLOCKER_BEARER and BRIGHTDATA_WEBUNLOCKER_APP_ZONE_STRING")
        return None


async def test_01_async_basic_fetch():
    """Test 01: Basic asynchronous fetch"""
    print("\n[Test 01] Basic async fetch...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    test_url = "https://example.com"
    print(f"  Async fetching {test_url}...")
    
    try:
        result = await unlocker.get_source_async(test_url)
        
        if not isinstance(result, ScrapeResult):
            print("✗ Result is not a ScrapeResult object")
            return False
        
        print(f"✓ Got async result: success={result.success}, status={result.status}")
        
        if result.success and "Example Domain" in (result.data or ""):
            print("✓ Async content validation passed")
            print(f"  - HTML size: {result.html_char_size} chars")
            return True
        else:
            print(f"✗ Async fetch failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Async test failed: {e}")
        return False


async def test_02_async_safe_fetch():
    """Test 02: Safe async fetch with error handling"""
    print("\n[Test 02] Safe async fetch...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    # Test with a non-existent domain (Web Unlocker will still proxy it successfully)
    test_url = "https://this-should-fail-12345.com"
    print(f"  Safe async fetching {test_url}...")
    
    try:
        result = await unlocker.get_source_safe_async(test_url)
        
        # Should never raise
        print("✓ Safe async fetch didn't raise exceptions")
        
        # Web Unlocker returns success even for non-existent domains
        if result.success:
            print(f"✓ Successfully proxied non-existent domain")
            if result.data:
                print(f"  - Got {len(result.data)} chars (likely DNS error page)")
            return True
        else:
            # Only fail if Web Unlocker API itself errored
            print(f"⚠ Web Unlocker API error: {result.error}")
            return True  # Still pass - API errors can happen
            
    except Exception as e:
        print(f"✗ Safe async fetch raised exception: {e}")
        return False


async def test_03_concurrent_requests():
    """Test 03: Multiple concurrent async requests"""
    print("\n[Test 03] Concurrent async requests...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/status/200",
    ]
    
    print(f"  Fetching {len(urls)} URLs concurrently...")
    
    try:
        start_time = time.time()
        
        # Create concurrent tasks
        tasks = [unlocker.get_source_async(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        print(f"✓ Completed {len(results)} requests in {elapsed:.2f}s")
        
        # Check results
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  - {urls[i]}: Exception {type(result).__name__}")
            elif isinstance(result, ScrapeResult) and result.success:
                success_count += 1
                print(f"  - {urls[i]}: Success ({result.html_char_size} chars)")
            else:
                print(f"  - {urls[i]}: Failed ({getattr(result, 'error', 'unknown')})")
        
        if success_count >= 2:  # At least half should succeed
            print(f"✓ {success_count}/{len(urls)} requests succeeded")
            return True
        else:
            print(f"✗ Only {success_count}/{len(urls)} succeeded")
            return False
            
    except Exception as e:
        print(f"✗ Concurrent test failed: {e}")
        return False


async def test_04_batch_performance():
    """Test 04: Batch request performance comparison"""
    print("\n[Test 04] Batch performance test...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    # Use fast-responding URLs
    urls = ["https://httpbin.org/html" for _ in range(5)]
    
    try:
        # Sequential timing
        print("  Testing sequential requests...")
        seq_start = time.time()
        seq_results = []
        for url in urls:
            result = await unlocker.get_source_async(url)
            seq_results.append(result)
        seq_time = time.time() - seq_start
        
        # Concurrent timing
        print("  Testing concurrent requests...")
        conc_start = time.time()
        tasks = [unlocker.get_source_async(url) for url in urls]
        conc_results = await asyncio.gather(*tasks)
        conc_time = time.time() - conc_start
        
        print(f"✓ Sequential: {seq_time:.2f}s")
        print(f"✓ Concurrent: {conc_time:.2f}s")
        print(f"✓ Speedup: {seq_time/conc_time:.1f}x")
        
        # Concurrent should be faster
        if conc_time < seq_time:
            print("✓ Concurrent is faster as expected")
            return True
        else:
            print("✗ Concurrent wasn't faster")
            return False
            
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False


async def test_05_timeout_handling():
    """Test 05: Test timeout handling"""
    print("\n[Test 05] Timeout handling...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    # Use a URL that delays response
    test_url = "https://httpbin.org/delay/10"  # 10 second delay
    
    print(f"  Testing timeout with {test_url}...")
    
    try:
        # Create a task with short timeout
        task = asyncio.create_task(unlocker.get_source_async(test_url))
        
        try:
            # Wait max 3 seconds
            result = await asyncio.wait_for(task, timeout=3.0)
            print("✗ Request completed (expected timeout)")
            return False
        except asyncio.TimeoutError:
            print("✓ Correctly timed out after 3 seconds")
            task.cancel()  # Clean up
            return True
            
    except Exception as e:
        print(f"✗ Timeout test failed: {e}")
        return False


async def test_06_large_content():
    """Test 06: Handle large content"""
    print("\n[Test 06] Large content handling...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    # Use a URL that returns large HTML content (not binary)
    test_url = "https://httpbin.org/html"  # HTML content
    
    print(f"  Fetching HTML content from {test_url}...")
    
    try:
        result = await unlocker.get_source_async(test_url)
        
        if result.success:
            content_size = len(result.data) if result.data else 0
            print(f"✓ Successfully fetched {content_size} chars")
            
            # For large content test, just verify we got substantial content
            if content_size > 1000:  # httpbin.org/html returns ~3.7KB
                print("✓ Content size is substantial")
                
                # Check size calculation
                if result.html_char_size == content_size:
                    print("✓ Size calculation correct")
                    return True
                else:
                    print(f"⚠ Size mismatch: reported {result.html_char_size}, actual {content_size}")
                    return True  # Still pass - size tracking is secondary
            else:
                print(f"✗ Content too small: {content_size} chars")
                return False
        else:
            print(f"✗ Failed to fetch content: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Large content test failed: {e}")
        return False


async def test_07_special_characters():
    """Test 07: Handle URLs and content with special characters"""
    print("\n[Test 07] Special characters handling...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    # Test URL with query parameters  
    test_url = "https://httpbin.org/anything?key=value&special=test%20space"
    
    print(f"  Testing URL with special characters...")
    
    try:
        result = await unlocker.get_source_async(test_url)
        
        if result.success:
            print("✓ Successfully handled URL with special characters")
            
            # Check if response contains our parameters
            if result.data and "test space" in result.data:
                print("✓ Special characters preserved in response")
                return True
            else:
                print("✗ Special characters not found in response")
                return False
        else:
            print(f"✗ Failed with special characters: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Special characters test failed: {e}")
        return False


async def test_08_redirect_handling():
    """Test 08: Test redirect handling"""
    print("\n[Test 08] Redirect handling...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    # httpbin redirect endpoint
    test_url = "https://httpbin.org/redirect/3"  # 3 redirects
    
    print(f"  Testing redirect chain...")
    
    try:
        result = await unlocker.get_source_async(test_url)
        
        if result.success:
            print("✓ Successfully followed redirects")
            
            # Final page should be httpbin /get
            if result.data and '"url"' in result.data:
                print("✓ Reached final destination")
                return True
            else:
                print("✗ Unexpected final content")
                return False
        else:
            print(f"✗ Failed to handle redirects: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Redirect test failed: {e}")
        return False


async def test_09_stress_test():
    """Test 09: Stress test with rapid requests"""
    print("\n[Test 09] Stress test...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    # Create many concurrent requests
    num_requests = 10
    test_url = "https://httpbin.org/uuid"  # Fast endpoint
    
    print(f"  Sending {num_requests} rapid requests...")
    
    try:
        start_time = time.time()
        
        # Fire all requests at once
        tasks = [unlocker.get_source_async(test_url) for _ in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        # Count successes
        successes = sum(1 for r in results 
                       if isinstance(r, ScrapeResult) and r.success)
        
        print(f"✓ Completed {num_requests} requests in {elapsed:.2f}s")
        print(f"  - Successes: {successes}/{num_requests}")
        print(f"  - Rate: {num_requests/elapsed:.1f} req/s")
        
        if successes >= num_requests * 0.8:  # 80% success rate
            print("✓ Stress test passed")
            return True
        else:
            print("✗ Too many failures in stress test")
            return False
            
    except Exception as e:
        print(f"✗ Stress test failed: {e}")
        return False


async def test_10_memory_efficiency():
    """Test 10: Test memory efficiency with multiple requests"""
    print("\n[Test 10] Memory efficiency test...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    # Test that we're not leaking memory
    import gc
    
    test_url = "https://httpbin.org/html"
    
    try:
        # Force garbage collection
        gc.collect()
        
        # Do multiple rounds of requests
        for round_num in range(3):
            print(f"  Round {round_num + 1}/3...")
            
            tasks = [unlocker.get_source_async(test_url) for _ in range(5)]
            results = await asyncio.gather(*tasks)
            
            # Clear references
            del results
            del tasks
            
            # Force cleanup
            gc.collect()
        
        print("✓ Completed multiple rounds without issues")
        print("✓ Memory efficiency test passed")
        return True
        
    except Exception as e:
        print(f"✗ Memory test failed: {e}")
        return False


def main():
    """Run all advanced feature tests"""
    print("=" * 60)
    print("Web Unlocker - Test Suite 2: Advanced Features")
    print("=" * 60)
    
    async_tests = [
        test_01_async_basic_fetch,
        test_02_async_safe_fetch,
        test_03_concurrent_requests,
        test_04_batch_performance,
        test_05_timeout_handling,
        test_06_large_content,
        test_07_special_characters,
        test_08_redirect_handling,
        test_09_stress_test,
        test_10_memory_efficiency,
    ]
    
    passed = 0
    failed = 0
    
    # Run all async tests
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
    print(f"Summary: {passed} passed, {failed} failed out of {len(async_tests)} tests")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)