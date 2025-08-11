#!/usr/bin/env python3
"""
Smoke tests for BrightData Browser API
"""
# To run: python -m smoke_tests.browserapi.test_basic

import sys
import asyncio
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from brightdata.browserapi import BrowserAPI
from dotenv import load_dotenv

load_dotenv()


def test_browserapi_sync():
    """Test synchronous Browser API functionality"""
    print("\n=== Browser API Sync Test ===")
    
    api = BrowserAPI(strategy="noop")
    test_url = "https://example.com"
    
    print(f"Testing with {test_url}...")
    
    try:
        result = api.fetch(test_url)
        
        print(f"Success: {result.success}")
        print(f"Status: {result.status}")
        print(f"HTML size: {len(result.data) if result.data else 0} chars")
        print(f"Cost: ${result.cost:.6f}")
        print(f"Root domain: {result.root_domain}")
        
        if result.success and result.data:
            if "Example Domain" in result.data:
                print("✓ Content verification passed")
                return True
            else:
                print("✗ Content verification failed")
                return False
        else:
            print(f"✗ Failed to fetch: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        return False


async def test_browserapi_async():
    """Test asynchronous Browser API functionality"""
    print("\n=== Browser API Async Test ===")
    
    api = BrowserAPI(strategy="noop")
    test_url = "https://httpbin.org/html"
    
    print(f"Testing async with {test_url}...")
    
    try:
        result = await api.fetch_async(test_url)
        
        print(f"Success: {result.success}")
        print(f"Status: {result.status}")
        print(f"HTML size: {len(result.data) if result.data else 0} chars")
        
        if result.success:
            print("✓ Async fetch successful")
            return True
        else:
            print(f"✗ Async fetch failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        return False


async def test_browserapi_strategies():
    """Test different Browser API strategies"""
    print("\n=== Browser API Strategies Test ===")
    
    strategies = ["noop", "semaphore", "pool"]
    test_url = "https://example.com"
    
    for strategy in strategies:
        print(f"\nTesting {strategy} strategy...")
        
        try:
            api = BrowserAPI(
                strategy=strategy,
                pool_size=2,
                max_concurrent=2
            )
            
            result = await api.fetch_async(test_url)
            
            if result.success:
                print(f"✓ {strategy} strategy works")
            else:
                print(f"✗ {strategy} strategy failed: {result.error}")
                return False
                
        except Exception as e:
            print(f"✗ {strategy} strategy crashed: {e}")
            return False
    
    return True


async def test_browserapi_concurrent():
    """Test concurrent Browser API requests"""
    print("\n=== Browser API Concurrent Test ===")
    
    api = BrowserAPI(strategy="semaphore", max_concurrent=3)
    
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://httpbin.org/delay/1"
    ]
    
    print(f"Testing {len(urls)} concurrent requests...")
    
    try:
        tasks = [api.fetch_async(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r.success)
        print(f"Successful: {success_count}/{len(results)}")
        
        if success_count == len(results):
            print("✓ All concurrent requests succeeded")
            return True
        else:
            failed = [r for r in results if not r.success]
            for f in failed:
                print(f"✗ Failed: {f.url} - {f.error}")
            return False
            
    except Exception as e:
        print(f"✗ Concurrent test failed: {e}")
        return False


def test_browserapi_wait_options():
    """Test Browser API wait options"""
    print("\n=== Browser API Wait Options Test ===")
    
    api = BrowserAPI(
        enable_wait_for_selector=True,
        wait_for_selector_timeout=5000
    )
    
    test_url = "https://example.com"
    
    print(f"Testing with wait options on {test_url}...")
    
    try:
        result = api.fetch(test_url, wait_until="networkidle")
        
        if result.success:
            print("✓ Wait options test passed")
            return True
        else:
            print(f"✗ Wait options test failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        return False


def main():
    """Run all Browser API smoke tests"""
    print("BrightData Browser API Smoke Tests")
    print("=" * 50)
    
    sync_tests = [
        test_browserapi_sync,
        test_browserapi_wait_options
    ]
    
    async_tests = [
        test_browserapi_async,
        test_browserapi_strategies,
        test_browserapi_concurrent
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
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    # Run async tests
    for test in async_tests:
        try:
            if asyncio.run(test()):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {len(sync_tests) + len(async_tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)