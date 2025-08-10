#!/usr/bin/env python3
"""
Smoke tests for BrightData Web Unlocker
"""
import os
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
from dotenv import load_dotenv

load_dotenv()


def test_web_unlocker_basic():
    """Test basic Web Unlocker functionality"""
    print("\n=== Web Unlocker Basic Test ===")
    
    try:
        unlocker = BrightdataWebUnlocker()
        print("✓ Web Unlocker initialized successfully")
    except ValueError as e:
        print(f"✗ Failed to initialize: {e}")
        print("  Make sure BRIGHTDATA_WEBUNLOCKER_BEARER and BRIGHTDATA_WEBUNLOCKER_APP_ZONE_STRING are set")
        return False
    
    # Test with a simple website
    test_url = "https://example.com"
    print(f"\nTesting with {test_url}...")
    
    result = unlocker.get_source_safe(test_url)
    
    print(f"Success: {result.success}")
    print(f"Status: {result.status}")
    print(f"Cost: ${result.cost:.6f}")
    print(f"HTML size: {result.html_char_size} chars")
    print(f"Root domain: {result.root_domain}")
    
    if result.success and result.data:
        print(f"✓ Successfully fetched {len(result.data)} characters")
        # Check if we got real content
        if "<title>Example Domain</title>" in result.data:
            print("✓ Content verification passed")
            return True
        else:
            print("✗ Content verification failed - unexpected HTML")
            return False
    else:
        print(f"✗ Failed to fetch: {result.error}")
        return False


def test_web_unlocker_async():
    """Test async Web Unlocker functionality"""
    import asyncio
    
    print("\n=== Web Unlocker Async Test ===")
    
    async def run_test():
        try:
            unlocker = BrightdataWebUnlocker()
            print("✓ Web Unlocker initialized successfully")
        except ValueError as e:
            print(f"✗ Failed to initialize: {e}")
            return False
        
        test_url = "https://httpbin.org/html"
        print(f"\nTesting async with {test_url}...")
        
        result = await unlocker.get_source_async(test_url)
        
        print(f"Success: {result.success}")
        print(f"Status: {result.status}")
        print(f"HTML size: {result.html_char_size} chars")
        
        if result.success:
            print("✓ Async fetch successful")
            return True
        else:
            print(f"✗ Async fetch failed: {result.error}")
            return False
    
    return asyncio.run(run_test())


def test_web_unlocker_error_handling():
    """Test Web Unlocker error handling"""
    print("\n=== Web Unlocker Error Handling Test ===")
    
    try:
        unlocker = BrightdataWebUnlocker()
    except ValueError:
        print("✗ Cannot test - Web Unlocker not configured")
        return False
    
    # Test with invalid URL
    test_url = "https://this-domain-definitely-does-not-exist-12345.com"
    print(f"\nTesting error handling with invalid URL: {test_url}")
    
    result = unlocker.get_source_safe(test_url)
    
    print(f"Success: {result.success}")
    print(f"Status: {result.status}")
    print(f"Error: {result.error}")
    
    if not result.success and result.status == "error":
        print("✓ Error handling works correctly")
        return True
    else:
        print("✗ Error handling failed - expected error status")
        return False


def main():
    """Run all Web Unlocker smoke tests"""
    print("BrightData Web Unlocker Smoke Tests")
    print("=" * 50)
    
    tests = [
        test_web_unlocker_basic,
        test_web_unlocker_async,
        test_web_unlocker_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)