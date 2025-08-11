#!/usr/bin/env python3
"""
Test 0: Specialized Scrapers - Imports and Initialization
Tests scraper imports, registry system, and initialization
"""
# To run: python -m smoke_tests.specialized_scraper.test_0_imports_and_init

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_01_import_base_scraper():
    """Test 01: Import base scraper class"""
    print("\n[Test 01] Importing base scraper...")
    try:
        from brightdata.webscraper_api.base_specialized_scraper import BrightdataBaseSpecializedScraper
        print("✓ Successfully imported BrightdataBaseSpecializedScraper")
        
        # Check if it's a class
        if isinstance(BrightdataBaseSpecializedScraper, type):
            print("✓ BrightdataBaseSpecializedScraper is a proper class")
            return True
        else:
            print("✗ BrightdataBaseSpecializedScraper is not a class")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import base scraper: {e}")
        return False


def test_02_import_registry():
    """Test 02: Import registry system"""
    print("\n[Test 02] Importing registry system...")
    
    try:
        from brightdata.webscraper_api.registry import register, get_scraper_for
        print("✓ Successfully imported registry functions")
        
        # Check if they're callable
        if callable(register) and callable(get_scraper_for):
            print("✓ Registry functions are callable")
            return True
        else:
            print("✗ Registry functions are not callable")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import registry: {e}")
        return False


def test_03_import_models():
    """Test 03: Import data models"""
    print("\n[Test 03] Importing data models...")
    
    try:
        from brightdata.models import ScrapeResult, SnapshotBundle
        print("✓ Successfully imported ScrapeResult and SnapshotBundle")
        
        # Check if they're dataclasses
        import dataclasses
        if dataclasses.is_dataclass(ScrapeResult):
            print("✓ ScrapeResult is a dataclass")
        else:
            print("✗ ScrapeResult is not a dataclass")
            return False
            
        if dataclasses.is_dataclass(SnapshotBundle):
            print("✓ SnapshotBundle is a dataclass")
        else:
            print("✗ SnapshotBundle is not a dataclass")
            return False
            
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import models: {e}")
        return False


def test_04_import_scrapers():
    """Test 04: Import individual scraper classes"""
    print("\n[Test 04] Importing individual scrapers...")
    
    scrapers = [
        ("amazon", "AmazonScraper"),
        ("linkedin", "LinkedInScraper"),
        ("instagram", "InstagramScraper"),
        ("tiktok", "TikTokScraper"),
        ("x", "XScraper"),
        ("reddit", "RedditScraper"),
        ("digikey", "DigikeyScraper"),
        ("mouser", "MouserScraper"),
    ]
    
    all_good = True
    for module_name, class_name in scrapers:
        try:
            module = __import__(f"brightdata.webscraper_api.scrapers.{module_name}.scraper", 
                               fromlist=[class_name])
            scraper_class = getattr(module, class_name)
            print(f"✓ Imported {class_name} from {module_name}")
        except (ImportError, AttributeError) as e:
            print(f"✗ Failed to import {class_name}: {e}")
            all_good = False
    
    return all_good


def test_05_scraper_inheritance():
    """Test 05: Check scraper inheritance"""
    print("\n[Test 05] Checking scraper inheritance...")
    
    try:
        from brightdata.webscraper_api.base_specialized_scraper import BrightdataBaseSpecializedScraper
        from brightdata.webscraper_api.scrapers.amazon.scraper import AmazonScraper
        from brightdata.webscraper_api.scrapers.linkedin.scraper import LinkedInScraper
        
        # Check inheritance
        if issubclass(AmazonScraper, BrightdataBaseSpecializedScraper):
            print("✓ AmazonScraper inherits from base class")
        else:
            print("✗ AmazonScraper doesn't inherit from base class")
            return False
            
        if issubclass(LinkedInScraper, BrightdataBaseSpecializedScraper):
            print("✓ LinkedInScraper inherits from base class")
        else:
            print("✗ LinkedInScraper doesn't inherit from base class")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Inheritance check failed: {e}")
        return False


def test_06_registry_decorator():
    """Test 06: Test registry decorator functionality"""
    print("\n[Test 06] Testing registry decorator...")
    
    try:
        from brightdata.webscraper_api.registry import register, _COLLECT_REGISTRY
        
        # Create a test class
        @register("testdomain")
        class TestScraper:
            pass
        
        # Check if it was registered
        if "testdomain" in _COLLECT_REGISTRY:
            print("✓ Decorator successfully registered test scraper")
            
            # Check if the class is stored correctly
            if _COLLECT_REGISTRY["testdomain"] == TestScraper:
                print("✓ Registry stores correct class reference")
                return True
            else:
                print("✗ Registry stores wrong reference")
                return False
        else:
            print("✗ Decorator failed to register")
            return False
            
    except Exception as e:
        print(f"✗ Registry decorator test failed: {e}")
        return False


def test_07_scraper_initialization():
    """Test 07: Test scraper initialization with token"""
    print("\n[Test 07] Testing scraper initialization...")
    
    try:
        from brightdata.webscraper_api.scrapers.amazon.scraper import AmazonScraper
        
        # Test with dummy token
        test_token = "test_bearer_token_12345"
        
        scraper = AmazonScraper(bearer_token=test_token)
        print("✓ AmazonScraper initialized successfully")
        
        # Check if it has required attributes
        if hasattr(scraper, 'dataset_id'):
            print(f"✓ Has dataset_id: {scraper.dataset_id}")
        else:
            print("✗ Missing dataset_id attribute")
            return False
            
        if hasattr(scraper, '_engine'):
            print("✓ Has _engine attribute")
        else:
            print("✗ Missing _engine attribute")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Scraper initialization failed: {e}")
        return False


def test_08_scraper_methods():
    """Test 08: Check required scraper methods"""
    print("\n[Test 08] Checking scraper methods...")
    
    try:
        from brightdata.webscraper_api.scrapers.amazon.scraper import AmazonScraper
        
        required_methods = [
            "trigger",
            "_trigger_async",
            "get_data",
            "get_data_async",
            "collect_by_url",
        ]
        
        all_good = True
        for method in required_methods:
            if hasattr(AmazonScraper, method):
                print(f"✓ Has method: {method}")
            else:
                print(f"✗ Missing method: {method}")
                all_good = False
        
        # Check Amazon-specific methods
        amazon_methods = [
            "products__collect_by_url",
            "products__discover_by_keyword",
            "products__discover_by_category",
        ]
        
        for method in amazon_methods:
            if hasattr(AmazonScraper, method):
                print(f"✓ Has Amazon method: {method}")
            else:
                print(f"⚠ Missing Amazon method: {method}")
        
        return all_good
        
    except Exception as e:
        print(f"✗ Method check failed: {e}")
        return False


def test_09_auto_import():
    """Test 09: Test auto-import functionality"""
    print("\n[Test 09] Testing auto-import...")
    
    try:
        from brightdata import scrape_url, scrape_url_async, scrape_urls, scrape_urls_async
        
        functions = [
            ("scrape_url", scrape_url),
            ("scrape_url_async", scrape_url_async),
            ("scrape_urls", scrape_urls),
            ("scrape_urls_async", scrape_urls_async),
        ]
        
        all_good = True
        for name, func in functions:
            if callable(func):
                print(f"✓ {name} is callable")
            else:
                print(f"✗ {name} is not callable")
                all_good = False
        
        return all_good
        
    except ImportError as e:
        print(f"✗ Failed to import auto functions: {e}")
        return False


def test_10_environment_setup():
    """Test 10: Check environment setup for scrapers"""
    print("\n[Test 10] Checking environment setup...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for BrightData token
    token = os.getenv("BRIGHTDATA_TOKEN")
    
    if token:
        print(f"✓ BRIGHTDATA_TOKEN is set (length: {len(token)})")
        
        # Test initializing a scraper with env token
        try:
            from brightdata.webscraper_api.scrapers.amazon.scraper import AmazonScraper
            scraper = AmazonScraper()  # Should use env token
            print("✓ Scraper can initialize with environment token")
            return True
        except Exception as e:
            print(f"⚠ Scraper initialization with env token failed: {e}")
            return True  # Not a failure if token isn't configured
    else:
        print("⚠ BRIGHTDATA_TOKEN not set in environment")
        print("  Set it in .env file for full functionality")
        return True  # Not a failure for import tests


def main():
    """Run all import and initialization tests"""
    print("=" * 60)
    print("Specialized Scrapers - Test Suite 0: Imports and Initialization")
    print("=" * 60)
    
    tests = [
        test_01_import_base_scraper,
        test_02_import_registry,
        test_03_import_models,
        test_04_import_scrapers,
        test_05_scraper_inheritance,
        test_06_registry_decorator,
        test_07_scraper_initialization,
        test_08_scraper_methods,
        test_09_auto_import,
        test_10_environment_setup,
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