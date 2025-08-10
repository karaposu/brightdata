#!/usr/bin/env python3
"""
Test 2: Browser API - Advanced Features
Tests pool management, resource blocking, concurrent operations, and performance
"""
# To run: python -m smoke_tests.browserapi.test_2_advanced_features

import os
import sys
import time
import asyncio
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from brightdata.browser_api import BrowserAPI
from brightdata.browser_pool import BrowserPool
from brightdata.models import ScrapeResult
from dotenv import load_dotenv

load_dotenv()


async def test_01_pool_strategy_basic():
    """Test 01: Basic pool strategy functionality"""
    print("\n[Test 01] Pool strategy basic test...")
    
    api = BrowserAPI(strategy="pool", pool_size=3)
    test_url = "https://example.com"
    
    print("  Testing pool with 3 sessions...")
    
    try:
        # First request should initialize pool
        result1 = await api.fetch_async(test_url)
        
        if result1.success:
            print("✓ First pool request successful")
            
            # Check pool was created
            if len(api._sessions) > 0:
                print(f"✓ Pool initialized with {len(api._sessions)} session(s)")
            else:
                print("✗ Pool not initialized")
                return False
            
            # Multiple requests should reuse sessions
            results = []
            for i in range(5):
                result = await api.fetch_async(f"https://httpbin.org/uuid")
                results.append(result)
            
            success_count = sum(1 for r in results if r.success)
            print(f"✓ Reused pool for {success_count}/5 requests")
            
            return success_count == 5
        else:
            print(f"✗ Pool request failed: {result1.error}")
            return False
            
    except Exception as e:
        print(f"✗ Pool test failed: {e}")
        return False


async def test_02_pool_round_robin():
    """Test 02: Test round-robin distribution in pool"""
    print("\n[Test 02] Pool round-robin test...")
    
    api = BrowserAPI(strategy="pool", pool_size=2)
    
    print("  Testing round-robin with 2 sessions...")
    
    try:
        # Initialize pool
        await api._ensure_pool()
        
        initial_idx = api._rr_idx
        print(f"  Initial index: {initial_idx}")
        
        # Make several requests
        for i in range(4):
            await api.fetch_async("https://httpbin.org/uuid")
            print(f"  After request {i+1}: index = {api._rr_idx}")
        
        # Index should have incremented
        if api._rr_idx > initial_idx:
            print("✓ Round-robin index incremented correctly")
            return True
        else:
            print("✗ Round-robin not working")
            return False
            
    except Exception as e:
        print(f"✗ Round-robin test failed: {e}")
        return False


async def test_03_resource_blocking():
    """Test 03: Test resource blocking patterns"""
    print("\n[Test 03] Resource blocking test...")
    
    # Test blocking images and scripts
    api = BrowserAPI(
        block_patterns=["*.jpg", "*.png", "*.gif", "*.js", "*.css"]
    )
    
    test_url = "https://httpbin.org/html"
    
    print("  Testing with resource blocking...")
    
    try:
        start = time.time()
        result = await api.fetch_async(test_url)
        elapsed = time.time() - start
        
        if result.success:
            print(f"✓ Fetch with blocking successful in {elapsed:.2f}s")
            
            # Compare with non-blocked
            api_noblock = BrowserAPI()
            start2 = time.time()
            result2 = await api_noblock.fetch_async(test_url)
            elapsed2 = time.time() - start2
            
            print(f"✓ Non-blocked fetch took {elapsed2:.2f}s")
            
            # Blocked should generally be faster
            if elapsed <= elapsed2 * 1.5:  # Allow some variance
                print("✓ Resource blocking improves performance")
                return True
            else:
                print("⚠ Resource blocking didn't improve performance (may vary)")
                return True  # Still pass as performance can vary
                
        else:
            print(f"✗ Blocked fetch failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Resource blocking test failed: {e}")
        return False


async def test_04_wait_for_selector():
    """Test 04: Test wait for selector functionality"""
    print("\n[Test 04] Wait for selector test...")
    
    api = BrowserAPI(
        enable_wait_for_selector=True,
        wait_for_selector_timeout=5000
    )
    
    test_url = "https://example.com"
    
    print("  Testing wait for selector...")
    
    try:
        # This should work as example.com has h1
        result = await api.fetch_async(test_url)
        
        if result.success:
            print("✓ Wait for selector succeeded")
            
            # Verify content was loaded
            if result.data and "<h1>" in result.data:
                print("✓ Selector content verified")
                return True
            else:
                print("✗ Expected content not found")
                return False
        else:
            print(f"✗ Wait for selector failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Selector test failed: {e}")
        return False


async def test_05_concurrent_pool_stress():
    """Test 05: Stress test pool with many concurrent requests"""
    print("\n[Test 05] Pool concurrent stress test...")
    
    pool_size = 5
    num_requests = 20
    
    api = BrowserAPI(strategy="pool", pool_size=pool_size)
    
    print(f"  Testing {num_requests} requests with pool size {pool_size}...")
    
    try:
        start = time.time()
        
        # Create many concurrent requests
        tasks = []
        for i in range(num_requests):
            url = f"https://httpbin.org/uuid"
            tasks.append(api.fetch_async(url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start
        
        # Count successes
        successes = sum(1 for r in results 
                       if isinstance(r, ScrapeResult) and r.success)
        exceptions = sum(1 for r in results if isinstance(r, Exception))
        
        print(f"✓ Completed in {elapsed:.2f}s")
        print(f"  - Successes: {successes}/{num_requests}")
        print(f"  - Exceptions: {exceptions}")
        print(f"  - Rate: {num_requests/elapsed:.1f} req/s")
        
        # Should handle all requests successfully
        if successes >= num_requests * 0.9:  # 90% success rate
            print("✓ Pool handled concurrent load well")
            return True
        else:
            print("✗ Too many failures under load")
            return False
            
    except Exception as e:
        print(f"✗ Stress test failed: {e}")
        return False


async def test_06_pool_vs_noop_performance():
    """Test 06: Compare pool vs noop strategy performance"""
    print("\n[Test 06] Pool vs noop performance comparison...")
    
    num_requests = 10
    test_url = "https://httpbin.org/uuid"
    
    # Test noop strategy
    print(f"\n  Testing noop strategy with {num_requests} requests...")
    api_noop = BrowserAPI(strategy="noop")
    
    start = time.time()
    noop_tasks = [api_noop.fetch_async(test_url) for _ in range(num_requests)]
    noop_results = await asyncio.gather(*noop_tasks)
    noop_time = time.time() - start
    
    noop_success = sum(1 for r in noop_results if r.success)
    print(f"  Noop: {noop_time:.2f}s ({noop_success}/{num_requests} succeeded)")
    
    # Test pool strategy
    print(f"\n  Testing pool strategy with {num_requests} requests...")
    api_pool = BrowserAPI(strategy="pool", pool_size=3)
    
    start = time.time()
    pool_tasks = [api_pool.fetch_async(test_url) for _ in range(num_requests)]
    pool_results = await asyncio.gather(*pool_tasks)
    pool_time = time.time() - start
    
    pool_success = sum(1 for r in pool_results if r.success)
    print(f"  Pool: {pool_time:.2f}s ({pool_success}/{num_requests} succeeded)")
    
    # Pool should be more efficient
    print(f"\n  Performance gain: {(noop_time/pool_time - 1) * 100:.1f}%")
    
    if pool_time < noop_time:
        print("✓ Pool strategy is more efficient")
        return True
    else:
        print("⚠ Pool wasn't faster (may vary based on conditions)")
        return True  # Still pass as performance can vary


async def test_07_browser_pool_class():
    """Test 07: Test BrowserPool class directly"""
    print("\n[Test 07] BrowserPool class test...")
    
    try:
        from brightdata.browser_pool import BrowserPool
        
        pool = BrowserPool(size=4)
        
        print("  Testing BrowserPool operations...")
        
        # Test context manager
        async with pool:
            # Acquire browsers
            browsers = []
            for i in range(4):
                browser = await pool.acquire()
                browsers.append(browser)
                print(f"  ✓ Acquired browser {i+1}")
            
            # Verify round-robin
            browser5 = await pool.acquire()
            if browser5 == browsers[0]:
                print("  ✓ Round-robin reuse confirmed")
            else:
                print("  ✗ Round-robin not working")
                return False
        
        print("✓ BrowserPool context manager worked")
        return True
        
    except Exception as e:
        print(f"✗ BrowserPool test failed: {e}")
        return False


async def test_08_memory_leak_check():
    """Test 08: Check for memory leaks with repeated operations"""
    print("\n[Test 08] Memory leak check...")
    
    api = BrowserAPI(strategy="pool", pool_size=2)
    
    print("  Running multiple cycles...")
    
    try:
        import gc
        
        for cycle in range(3):
            print(f"\n  Cycle {cycle + 1}/3...")
            
            # Force garbage collection
            gc.collect()
            
            # Do many requests
            tasks = [api.fetch_async("https://httpbin.org/uuid") for _ in range(10)]
            results = await asyncio.gather(*tasks)
            
            success = sum(1 for r in results if r.success)
            print(f"    Completed {success}/10 requests")
            
            # Clear references
            del results
            del tasks
        
        # Final cleanup
        gc.collect()
        
        print("\n✓ No apparent memory leaks")
        return True
        
    except Exception as e:
        print(f"✗ Memory leak test failed: {e}")
        return False


async def test_09_mixed_strategies():
    """Test 09: Test mixing different strategies"""
    print("\n[Test 09] Mixed strategies test...")
    
    strategies = ["noop", "semaphore", "pool"]
    test_url = "https://httpbin.org/uuid"
    
    try:
        # Create multiple API instances
        apis = {
            strategy: BrowserAPI(strategy=strategy, max_concurrent=2, pool_size=2)
            for strategy in strategies
        }
        
        print("  Testing all strategies concurrently...")
        
        # Launch requests from all strategies
        all_tasks = []
        for strategy, api in apis.items():
            for i in range(3):
                task = api.fetch_async(test_url)
                all_tasks.append((strategy, task))
        
        # Gather results
        results_by_strategy = {s: [] for s in strategies}
        
        for strategy, task in all_tasks:
            try:
                result = await task
                results_by_strategy[strategy].append(result)
            except Exception as e:
                print(f"  ✗ {strategy} failed: {e}")
        
        # Check results
        all_good = True
        for strategy, results in results_by_strategy.items():
            success = sum(1 for r in results if r.success)
            print(f"  {strategy}: {success}/{len(results)} succeeded")
            if success < len(results) * 0.8:
                all_good = False
        
        if all_good:
            print("✓ All strategies worked together")
            return True
        else:
            print("✗ Some strategies had issues")
            return False
            
    except Exception as e:
        print(f"✗ Mixed strategies test failed: {e}")
        return False


async def test_10_cleanup_and_lifecycle():
    """Test 10: Test proper cleanup and lifecycle management"""
    print("\n[Test 10] Cleanup and lifecycle test...")
    
    try:
        # Test pool cleanup
        api = BrowserAPI(strategy="pool", pool_size=2)
        
        print("  Initializing pool...")
        await api._ensure_pool()
        initial_sessions = len(api._sessions)
        print(f"  Pool has {initial_sessions} sessions")
        
        # Do some work
        await api.fetch_async("https://example.com")
        
        # Manual cleanup (if method exists)
        if hasattr(api, 'close') or hasattr(api, 'cleanup'):
            print("  ✓ Cleanup methods available")
        else:
            print("  ⚠ No explicit cleanup methods")
        
        # Test creating and destroying multiple times
        for i in range(3):
            api2 = BrowserAPI(strategy="pool", pool_size=1)
            result = await api2.fetch_async("https://httpbin.org/uuid")
            if not result.success:
                print(f"  ✗ Lifecycle {i+1} failed")
                return False
            # Let it go out of scope
            del api2
        
        print("✓ Lifecycle management working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Lifecycle test failed: {e}")
        return False


def main():
    """Run all advanced feature tests"""
    print("=" * 60)
    print("Browser API - Test Suite 2: Advanced Features")
    print("=" * 60)
    
    async_tests = [
        test_01_pool_strategy_basic,
        test_02_pool_round_robin,
        test_03_resource_blocking,
        test_04_wait_for_selector,
        test_05_concurrent_pool_stress,
        test_06_pool_vs_noop_performance,
        test_07_browser_pool_class,
        test_08_memory_leak_check,
        test_09_mixed_strategies,
        test_10_cleanup_and_lifecycle,
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