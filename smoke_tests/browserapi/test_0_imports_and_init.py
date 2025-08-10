#!/usr/bin/env python3
"""
Test 0: Browser API - Imports and Initialization
Tests basic imports, class initialization, strategies, and configuration
"""
# To run: python -m smoke_tests.browserapi.test_0_imports_and_init

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_01_import_browser_api():
    """Test 01: Can import BrowserAPI class"""
    print("\n[Test 01] Importing BrowserAPI...")
    try:
        from brightdata.browser_api import BrowserAPI
        print("✓ Successfully imported BrowserAPI")
        return True
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        return False


def test_02_import_dependencies():
    """Test 02: Check all required dependencies"""
    print("\n[Test 02] Checking Browser API dependencies...")
    dependencies = [
        ("asyncio", "Async support"),
        ("logging", "Logging"),
        ("tldextract", "Domain extraction"),
        ("brightdata.browserapi_engine", "Browser engine"),
        ("brightdata.models", "Data models"),
    ]
    
    all_good = True
    for module, description in dependencies:
        try:
            if '.' in module:
                parts = module.split('.')
                __import__(parts[0])
                exec(f"from {module} import *")
            else:
                __import__(module)
            print(f"✓ {module} ({description}) is available")
        except ImportError:
            print(f"✗ {module} ({description}) is missing")
            all_good = False
    
    return all_good


def test_03_strategy_options():
    """Test 03: Test available strategy options"""
    print("\n[Test 03] Testing strategy options...")
    
    from brightdata.browser_api import BrowserAPI
    
    strategies = ["noop", "semaphore", "pool"]
    
    all_good = True
    for strategy in strategies:
        try:
            api = BrowserAPI(strategy=strategy)
            print(f"✓ Strategy '{strategy}' initialized successfully")
        except Exception as e:
            print(f"✗ Strategy '{strategy}' failed: {e}")
            all_good = False
    
    # Test invalid strategy
    try:
        api = BrowserAPI(strategy="invalid_strategy")
        print("✗ Should have rejected invalid strategy")
        all_good = False
    except:
        print("✓ Correctly rejected invalid strategy")
    
    return all_good


def test_04_init_parameters():
    """Test 04: Test initialization parameters"""
    print("\n[Test 04] Testing initialization parameters...")
    
    from brightdata.browser_api import BrowserAPI
    
    test_cases = [
        ({"pool_size": 10}, "pool_size=10"),
        ({"max_concurrent": 5}, "max_concurrent=5"),
        ({"enable_wait_for_selector": True}, "wait_for_selector enabled"),
        ({"wait_for_selector_timeout": 10000}, "selector timeout=10s"),
        ({"block_patterns": ["*.jpg", "*.png"]}, "block patterns"),
    ]
    
    all_good = True
    for params, description in test_cases:
        try:
            api = BrowserAPI(**params)
            print(f"✓ Initialized with {description}")
            
            # Verify parameters were set
            if "pool_size" in params:
                assert api.pool_size == params["pool_size"]
            if "max_concurrent" in params:
                assert api._max_concurrent == params["max_concurrent"]
                
        except Exception as e:
            print(f"✗ Failed with {description}: {e}")
            all_good = False
    
    return all_good


def test_05_class_attributes():
    """Test 05: Check class attributes and constants"""
    print("\n[Test 05] Checking class attributes...")
    
    from brightdata.browser_api import BrowserAPI
    
    # Check cost constants
    if hasattr(BrowserAPI, 'COST_PER_GIB'):
        print(f"✓ COST_PER_GIB: ${BrowserAPI.COST_PER_GIB}")
    else:
        print("✗ Missing COST_PER_GIB constant")
        return False
    
    if hasattr(BrowserAPI, 'GIB'):
        print(f"✓ GIB constant: {BrowserAPI.GIB} bytes")
        expected_gib = 1024**3
        if BrowserAPI.GIB == expected_gib:
            print("✓ GIB calculation correct")
        else:
            print(f"✗ GIB should be {expected_gib}, got {BrowserAPI.GIB}")
            return False
    else:
        print("✗ Missing GIB constant")
        return False
    
    return True


def test_06_method_availability():
    """Test 06: Check all expected methods are available"""
    print("\n[Test 06] Checking method availability...")
    
    from brightdata.browser_api import BrowserAPI
    
    expected_methods = [
        ("fetch", "Sync fetch method"),
        ("fetch_async", "Async fetch method"),
        ("calculate_cost", "Cost calculation"),
        ("_extract_root", "Root domain extraction"),
        ("_fetch_isolated", "Isolated fetch (private)"),
        ("_ensure_pool", "Pool initialization (private)"),
        ("_fetch_from_pool", "Pool fetch (private)"),
        ("_do_strategy_fetch", "Strategy dispatcher (private)"),
    ]
    
    all_good = True
    for method_name, description in expected_methods:
        if hasattr(BrowserAPI, method_name):
            print(f"✓ {method_name}: {description}")
        else:
            print(f"✗ Missing method: {method_name} ({description})")
            all_good = False
    
    return all_good


def test_07_semaphore_strategy():
    """Test 07: Test semaphore strategy initialization"""
    print("\n[Test 07] Testing semaphore strategy...")
    
    from brightdata.browser_api import BrowserAPI
    import asyncio
    
    try:
        api = BrowserAPI(strategy="semaphore", max_concurrent=3)
        
        # Check if semaphore was created
        if hasattr(api, '_sem'):
            print("✓ Semaphore created")
            
            # Check semaphore value
            if isinstance(api._sem, asyncio.Semaphore):
                print(f"✓ Semaphore is correct type")
                return True
            else:
                print("✗ Semaphore is wrong type")
                return False
        else:
            print("✗ Semaphore not created")
            return False
            
    except Exception as e:
        print(f"✗ Semaphore test failed: {e}")
        return False


def test_08_pool_strategy():
    """Test 08: Test pool strategy initialization"""
    print("\n[Test 08] Testing pool strategy...")
    
    from brightdata.browser_api import BrowserAPI
    
    try:
        api = BrowserAPI(strategy="pool", pool_size=5)
        
        # Check pool attributes
        if hasattr(api, '_sessions'):
            print("✓ Session list created")
        else:
            print("✗ Missing _sessions list")
            return False
            
        if hasattr(api, '_rr_idx'):
            print(f"✓ Round-robin index initialized: {api._rr_idx}")
        else:
            print("✗ Missing round-robin index")
            return False
            
        # Check pool size
        if api.pool_size == 5:
            print("✓ Pool size correctly set")
        else:
            print(f"✗ Pool size mismatch: expected 5, got {api.pool_size}")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Pool test failed: {e}")
        return False


def test_09_default_values():
    """Test 09: Test default configuration values"""
    print("\n[Test 09] Testing default values...")
    
    from brightdata.browser_api import BrowserAPI
    
    try:
        api = BrowserAPI()
        
        # Check defaults
        checks = [
            (api.strategy == "noop", f"Default strategy should be 'noop', got '{api.strategy}'"),
            (api.pool_size == 5, f"Default pool_size should be 5, got {api.pool_size}"),
            (api._enable_wait_for_selector == False, "Default wait_for_selector should be False"),
            (api._wait_for_selector_timeout == 15000, f"Default timeout should be 15000ms"),
            (api._block_patterns is None, "Default block_patterns should be None"),
        ]
        
        all_good = True
        for condition, message in checks:
            if condition:
                print(f"✓ {message.split('should')[0]} correct")
            else:
                print(f"✗ {message}")
                all_good = False
                
        return all_good
        
    except Exception as e:
        print(f"✗ Default values test failed: {e}")
        return False


def test_10_usage_tracking():
    """Test 10: Test usage tracking initialization"""
    print("\n[Test 10] Testing usage tracking...")
    
    from brightdata.browser_api import BrowserAPI
    
    try:
        api = BrowserAPI()
        
        # Check tracking attributes
        if hasattr(api, 'total_bytes'):
            print(f"✓ total_bytes initialized: {api.total_bytes}")
            if api.total_bytes != 0:
                print("✗ total_bytes should start at 0")
                return False
        else:
            print("✗ Missing total_bytes attribute")
            return False
            
        if hasattr(api, 'total_cost'):
            print(f"✓ total_cost initialized: {api.total_cost}")
            if api.total_cost != 0.0:
                print("✗ total_cost should start at 0.0")
                return False
        else:
            print("✗ Missing total_cost attribute")
            return False
            
        # Test cost calculation method
        test_html = "Hello World" * 1000  # ~11KB
        cost = api.calculate_cost(test_html)
        
        if isinstance(cost, float) and cost > 0:
            print(f"✓ Cost calculation works: ${cost:.6f}")
            return True
        else:
            print(f"✗ Invalid cost calculation: {cost}")
            return False
            
    except Exception as e:
        print(f"✗ Usage tracking test failed: {e}")
        return False


def main():
    """Run all import and initialization tests"""
    print("=" * 60)
    print("Browser API - Test Suite 0: Imports and Initialization")
    print("=" * 60)
    
    tests = [
        test_01_import_browser_api,
        test_02_import_dependencies,
        test_03_strategy_options,
        test_04_init_parameters,
        test_05_class_attributes,
        test_06_method_availability,
        test_07_semaphore_strategy,
        test_08_pool_strategy,
        test_09_default_values,
        test_10_usage_tracking,
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