#!/usr/bin/env python3
"""
Test 0: Web Unlocker - Imports and Initialization
Tests basic imports, class initialization, and configuration
"""
# To run: python -m smoke_tests.web_unlocker.test_0_imports_and_init

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_01_import_web_unlocker():
    """Test 01: Can import BrightdataWebUnlocker class"""
    print("\n[Test 01] Importing BrightdataWebUnlocker...")
    try:
        from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
        print("✓ Successfully imported BrightdataWebUnlocker")
        return True
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        return False


def test_02_import_dependencies():
    """Test 02: Check all required dependencies are available"""
    print("\n[Test 02] Checking dependencies...")
    dependencies = [
        ("requests", "HTTP requests"),
        ("aiohttp", "Async HTTP"),
        ("tldextract", "Domain extraction"),
        ("dotenv", "Environment loading"),
    ]
    
    all_good = True
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"✓ {module} ({description}) is available")
        except ImportError:
            print(f"✗ {module} ({description}) is missing")
            all_good = False
    
    return all_good


def test_03_import_models():
    """Test 03: Can import ScrapeResult model"""
    print("\n[Test 03] Importing data models...")
    try:
        from brightdata.models import ScrapeResult
        print("✓ Successfully imported ScrapeResult")
        
        # Check if it's a dataclass
        import dataclasses
        if dataclasses.is_dataclass(ScrapeResult):
            print("✓ ScrapeResult is a proper dataclass")
            return True
        else:
            print("✗ ScrapeResult is not a dataclass")
            return False
    except ImportError as e:
        print(f"✗ Failed to import models: {e}")
        return False


def test_04_environment_variables():
    """Test 04: Check environment variable configuration"""
    print("\n[Test 04] Checking environment variables...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "BRIGHTDATA_WEBUNLOCKER_BEARER",
        "BRIGHTDATA_WEBUNLOCKER_APP_ZONE_STRING"
    ]
    
    found = 0
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var} is set (length: {len(value)})")
            found += 1
        else:
            print(f"✗ {var} is not set")
    
    if found == len(required_vars):
        print("✓ All required environment variables are set")
        return True
    else:
        print(f"⚠ Only {found}/{len(required_vars)} environment variables are set")
        return False


def test_05_init_with_env_vars():
    """Test 05: Initialize Web Unlocker with environment variables"""
    print("\n[Test 05] Initializing with environment variables...")
    
    from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
    
    try:
        unlocker = BrightdataWebUnlocker()
        print("✓ Successfully initialized with environment variables")
        print(f"  - Bearer token length: {len(unlocker.bearer) if unlocker.bearer else 0}")
        print(f"  - Zone configured: {'Yes' if unlocker.zone else 'No'}")
        print(f"  - Format: {unlocker.format}")
        print(f"  - Endpoint: {unlocker._endpoint}")
        return True
    except ValueError as e:
        print(f"✗ Failed to initialize: {e}")
        print("  Make sure BRIGHTDATA_WEBUNLOCKER_BEARER and BRIGHTDATA_WEBUNLOCKER_APP_ZONE_STRING are set")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_06_init_with_parameters():
    """Test 06: Initialize Web Unlocker with direct parameters"""
    print("\n[Test 06] Initializing with direct parameters...")
    
    from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
    
    try:
        # Test with dummy values
        unlocker = BrightdataWebUnlocker(
            BRIGHTDATA_WEBUNLOCKER_BEARER="test_bearer_token",
            ZONE_STRING="test_zone"
        )
        print("✓ Successfully initialized with parameters")
        print(f"  - Bearer: {unlocker.bearer[:10]}...")
        print(f"  - Zone: {unlocker.zone}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize with parameters: {e}")
        return False


def test_07_partial_credentials():
    """Test 07: Test initialization with partial credentials"""
    print("\n[Test 07] Testing partial credentials...")
    
    from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
    
    try:
        # Test with only bearer token
        unlocker = BrightdataWebUnlocker(BRIGHTDATA_WEBUNLOCKER_BEARER="test_bearer")
        print("✗ Should have raised ValueError with only bearer token")
        return False
    except ValueError as e:
        print("✓ Correctly raised ValueError with only bearer token")
    
    try:
        # Test with only zone
        unlocker = BrightdataWebUnlocker(ZONE_STRING="test_zone")
        print("✗ Should have raised ValueError with only zone")
        return False
    except ValueError as e:
        print("✓ Correctly raised ValueError with only zone")
    
    return True


def test_08_class_attributes():
    """Test 08: Check class attributes and constants"""
    print("\n[Test 08] Checking class attributes...")
    
    from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
    
    # Check class constants
    if hasattr(BrightdataWebUnlocker, 'COST_PER_THOUSAND'):
        print(f"✓ COST_PER_THOUSAND: ${BrightdataWebUnlocker.COST_PER_THOUSAND}")
    else:
        print("✗ Missing COST_PER_THOUSAND constant")
        return False
    
    if hasattr(BrightdataWebUnlocker, 'COST_PER_REQUEST'):
        print(f"✓ COST_PER_REQUEST: ${BrightdataWebUnlocker.COST_PER_REQUEST:.6f}")
    else:
        print("✗ Missing COST_PER_REQUEST constant")
        return False
    
    # Check if cost calculation is correct
    expected_cost = BrightdataWebUnlocker.COST_PER_THOUSAND / 1000.0
    if abs(BrightdataWebUnlocker.COST_PER_REQUEST - expected_cost) < 0.000001:
        print("✓ Cost calculation is correct")
    else:
        print("✗ Cost calculation mismatch")
        return False
    
    return True


def test_09_method_availability():
    """Test 09: Check all expected methods are available"""
    print("\n[Test 09] Checking method availability...")
    
    from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
    
    expected_methods = [
        ("get_source", "Sync fetch method"),
        ("get_source_safe", "Safe sync fetch"),
        ("download_source", "Download to file"),
        ("download_source_safe", "Safe download"),
        ("get_source_async", "Async fetch"),
        ("get_source_safe_async", "Safe async fetch"),
        ("test_unlocker", "Test method"),
        ("_make_result", "Result factory (private)"),
    ]
    
    all_good = True
    for method_name, description in expected_methods:
        if hasattr(BrightdataWebUnlocker, method_name):
            print(f"✓ {method_name}: {description}")
        else:
            print(f"✗ Missing method: {method_name} ({description})")
            all_good = False
    
    return all_good


def test_10_endpoint_configuration():
    """Test 10: Test endpoint URL configuration"""
    print("\n[Test 10] Testing endpoint configuration...")
    
    from brightdata.brightdata_web_unlocker import BrightdataWebUnlocker
    
    try:
        unlocker = BrightdataWebUnlocker(
            BRIGHTDATA_WEBUNLOCKER_BEARER="test",
            ZONE_STRING="test"
        )
        
        # Check endpoint
        expected_endpoint = "https://api.brightdata.com/request"
        if unlocker._endpoint == expected_endpoint:
            print(f"✓ Endpoint correctly set to: {unlocker._endpoint}")
        else:
            print(f"✗ Unexpected endpoint: {unlocker._endpoint}")
            print(f"  Expected: {expected_endpoint}")
            return False
        
        # Check format
        if unlocker.format == "raw":
            print(f"✓ Format correctly set to: {unlocker.format}")
        else:
            print(f"✗ Unexpected format: {unlocker.format}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to test endpoint: {e}")
        return False


def main():
    """Run all import and initialization tests"""
    print("=" * 60)
    print("Web Unlocker - Test Suite 0: Imports and Initialization")
    print("=" * 60)
    
    tests = [
        test_01_import_web_unlocker,
        test_02_import_dependencies,
        test_03_import_models,
        test_04_environment_variables,
        test_05_init_with_env_vars,
        test_06_init_with_parameters,
        test_07_partial_credentials,
        test_08_class_attributes,
        test_09_method_availability,
        test_10_endpoint_configuration,
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