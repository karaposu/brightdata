#!/usr/bin/env python3
"""
Test 1: Web Unlocker - Basic Operations
Tests basic fetching, error handling, and result validation
"""
# To run: python -m smoke_tests.web_unlocker.test_1_basic_operations

import os
import sys
import time
from pathlib import Path

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


def test_01_basic_fetch():
    """Test 01: Basic synchronous fetch of a simple website"""
    print("\n[Test 01] Basic synchronous fetch...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    test_url = "https://example.com"
    print(f"  Fetching {test_url}...")
    
    try:
        result = unlocker.get_source(test_url)
        
        # Check result type
        if not isinstance(result, ScrapeResult):
            print("✗ Result is not a ScrapeResult object")
            return False
        
        print(f"✓ Got ScrapeResult: success={result.success}, status={result.status}")
        
        # Validate content
        if result.success and result.data:
            if "Example Domain" in result.data:
                print("✓ Content validation passed")
                print(f"  - HTML size: {len(result.data)} chars")
                print(f"  - Cost: ${result.cost:.6f}")
                return True
            else:
                print("✗ Content validation failed - unexpected HTML")
                return False
        else:
            print(f"✗ Fetch failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        return False


def test_02_safe_fetch():
    """Test 02: Safe fetch that never raises exceptions"""
    print("\n[Test 02] Safe fetch (exception handling)...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    test_url = "https://httpbin.org/html"
    print(f"  Safe fetching {test_url}...")
    
    try:
        result = unlocker.get_source_safe(test_url)
        
        # Safe fetch should NEVER raise
        print("✓ Safe fetch didn't raise any exceptions")
        
        # Check result
        print(f"  - Success: {result.success}")
        print(f"  - Status: {result.status}")
        print(f"  - HTML size: {result.html_char_size} chars")
        
        return True
        
    except Exception as e:
        print(f"✗ Safe fetch raised exception (should never happen): {e}")
        return False


def test_03_result_fields():
    """Test 03: Validate all ScrapeResult fields are populated correctly"""
    print("\n[Test 03] Validating ScrapeResult fields...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    test_url = "https://example.com"
    result = unlocker.get_source_safe(test_url)
    
    # Check required fields
    required_fields = [
        ("success", bool),
        ("url", str),
        ("status", str),
        ("data", (str, type(None))),
        ("error", (str, type(None))),
        ("cost", (float, type(None))),
        ("fallback_used", bool),
        ("root_domain", (str, type(None))),
    ]
    
    all_good = True
    for field_name, expected_type in required_fields:
        if hasattr(result, field_name):
            value = getattr(result, field_name)
            if isinstance(value, expected_type):
                print(f"✓ {field_name}: {type(value).__name__} = {repr(value)[:50]}...")
            else:
                print(f"✗ {field_name}: expected {expected_type}, got {type(value)}")
                all_good = False
        else:
            print(f"✗ Missing field: {field_name}")
            all_good = False
    
    # Check timestamps
    if result.success:
        if result.request_sent_at:
            print(f"✓ request_sent_at: {result.request_sent_at}")
        if result.data_received_at:
            print(f"✓ data_received_at: {result.data_received_at}")
        if result.html_char_size:
            print(f"✓ html_char_size: {result.html_char_size}")
    
    return all_good


def test_04_error_handling():
    """Test 04: Test Web Unlocker handles various URLs gracefully"""
    print("\n[Test 04] Testing Web Unlocker response handling...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    # Web Unlocker returns success even for non-existent domains (it proxies whatever response it gets)
    test_cases = [
        ("https://this-domain-definitely-does-not-exist-12345.com", "Non-existent domain"),
        ("https://httpbin.org/status/404", "404 page"),
        ("https://httpbin.org/status/500", "500 error page"),
    ]
    
    all_good = True
    for test_url, description in test_cases:
        print(f"\n  Testing {description}: {test_url}")
        
        try:
            result = unlocker.get_source_safe(test_url)
            
            # Web Unlocker should return success (it successfully proxied the request)
            if result.success:
                print(f"✓ Successfully proxied {description}")
                if result.data:
                    print(f"  - Got {len(result.data)} chars of content")
            else:
                # Only fail if Web Unlocker itself had an error
                print(f"✗ Web Unlocker API error: {result.error}")
                all_good = False
                
        except Exception as e:
            print(f"✗ Unexpected exception for {description}: {e}")
            all_good = False
    
    return all_good


def test_05_download_to_file():
    """Test 05: Test downloading content to file"""
    print("\n[Test 05] Testing download to file...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    test_url = "https://example.com"
    test_file = "test_download.html"
    
    try:
        # Clean up any existing file
        if os.path.exists(test_file):
            os.remove(test_file)
        
        print(f"  Downloading {test_url} to {test_file}...")
        result = unlocker.download_source(test_url, test_file)
        
        if result.success:
            print("✓ Download reported success")
            
            # Check if file exists
            if os.path.exists(test_file):
                print(f"✓ File created: {test_file}")
                
                # Check file content
                with open(test_file, 'r') as f:
                    content = f.read()
                    if "Example Domain" in content:
                        print(f"✓ File contains expected content ({len(content)} chars)")
                        os.remove(test_file)  # Clean up
                        return True
                    else:
                        print("✗ File content validation failed")
                        os.remove(test_file)
                        return False
            else:
                print("✗ File was not created")
                return False
        else:
            print(f"✗ Download failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return False


def test_06_safe_download():
    """Test 06: Test safe download with error handling"""
    print("\n[Test 06] Testing safe download...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    test_url = "https://httpbin.org/html"
    test_file = "test_safe_download.html"
    
    try:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
        
        print(f"  Safe downloading {test_url} to {test_file}...")
        result = unlocker.download_source_safe(test_url, test_file)
        
        # Should never raise
        print("✓ Safe download didn't raise exceptions")
        
        if result.success and os.path.exists(test_file):
            print(f"✓ File successfully created")
            os.remove(test_file)  # Clean up
            return True
        elif not result.success:
            print(f"✓ Handled error gracefully: {result.error}")
            return True
        else:
            print("✗ Unexpected state")
            return False
            
    except Exception as e:
        print(f"✗ Safe download raised exception: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return False


def test_07_test_method():
    """Test 07: Test the built-in test_unlocker method"""
    print("\n[Test 07] Testing built-in test method...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    try:
        print("  Running test_unlocker()...")
        result = unlocker.test_unlocker()
        
        if not isinstance(result, ScrapeResult):
            print("✗ test_unlocker didn't return ScrapeResult")
            return False
        
        print(f"  - Success: {result.success}")
        print(f"  - Status: {result.status}")
        print(f"  - Data: {result.data}")
        
        if result.success and result.data == "Test succeeded":
            print("✓ Built-in test passed")
            return True
        else:
            print("✗ Built-in test failed")
            return False
            
    except Exception as e:
        print(f"✗ Test method failed: {e}")
        return False


def test_08_cost_calculation():
    """Test 08: Verify cost calculation is correct"""
    print("\n[Test 08] Testing cost calculation...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    # Test successful request
    test_url = "https://example.com"
    result = unlocker.get_source_safe(test_url)
    
    if result.success:
        expected_cost = WebUnlocker.COST_PER_REQUEST
        if result.cost == expected_cost:
            print(f"✓ Success cost correct: ${result.cost:.6f}")
        else:
            print(f"✗ Success cost mismatch: got ${result.cost}, expected ${expected_cost}")
            return False
    
    # Test failed request
    bad_url = "https://this-will-fail-12345.com"
    fail_result = unlocker.get_source_safe(bad_url)
    
    if not fail_result.success:
        if fail_result.cost == 0.0:
            print(f"✓ Failed request cost correct: ${fail_result.cost}")
        else:
            print(f"✗ Failed request should have zero cost, got ${fail_result.cost}")
            return False
    
    return True


def test_09_domain_extraction():
    """Test 09: Test root domain extraction"""
    print("\n[Test 09] Testing domain extraction...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    test_cases = [
        ("https://www.example.com/path/page.html", "example"),
        ("https://subdomain.example.co.uk/", "example"),
        ("https://example.com", "example"),
        ("https://blog.example.org/post", "example"),
    ]
    
    all_good = True
    for test_url, expected_domain in test_cases:
        result = unlocker._make_result(
            url=test_url,
            success=True,
            status="ready",
            data="test"
        )
        
        if result.root_domain == expected_domain:
            print(f"✓ {test_url} → {result.root_domain}")
        else:
            print(f"✗ {test_url} → {result.root_domain} (expected {expected_domain})")
            all_good = False
    
    return all_good


def test_10_timing_validation():
    """Test 10: Validate timing of operations"""
    print("\n[Test 10] Testing operation timing...")
    
    unlocker = get_unlocker()
    if not unlocker:
        return False
    
    test_url = "https://example.com"
    
    start_time = time.time()
    result = unlocker.get_source(test_url)
    elapsed = time.time() - start_time
    
    print(f"  Operation took {elapsed:.2f} seconds")
    
    if result.success:
        # Check timestamps are set
        if result.request_sent_at and result.data_received_at:
            delta = (result.data_received_at - result.request_sent_at).total_seconds()
            print(f"✓ Timestamps recorded: {delta:.2f}s between request and response")
            
            # Sanity check - should be positive and reasonable
            if 0 < delta < 30:  # Assuming max 30s for a request
                print("✓ Timing looks reasonable")
                return True
            else:
                print(f"✗ Timing seems off: {delta}s")
                return False
        else:
            print("✗ Timestamps not properly set")
            return False
    else:
        print(f"✗ Request failed: {result.error}")
        return False


def main():
    """Run all basic operation tests"""
    print("=" * 60)
    print("Web Unlocker - Test Suite 1: Basic Operations")
    print("=" * 60)
    
    tests = [
        test_01_basic_fetch,
        test_02_safe_fetch,
        test_03_result_fields,
        test_04_error_handling,
        test_05_download_to_file,
        test_06_safe_download,
        test_07_test_method,
        test_08_cost_calculation,
        test_09_domain_extraction,
        test_10_timing_validation,
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
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Summary: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)