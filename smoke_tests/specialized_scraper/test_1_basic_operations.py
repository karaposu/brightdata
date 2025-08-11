#!/usr/bin/env python3
"""
Test 1: Specialized Scrapers - Basic Operations
Tests URL detection, scraper routing, basic scraping operations
"""
# To run: python -m smoke_tests.specialized_scraper.test_1_basic_operations

import os
import sys
import time
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from brightdata import scrape_url, trigger_scrape_url
from brightdata.webscraper_api.registry import get_scraper_for
from brightdata.models import ScrapeResult
from dotenv import load_dotenv

load_dotenv()


def test_01_url_detection():
    """Test 01: Test URL to scraper detection"""
    print("\n[Test 01] Testing URL detection...")
    
    test_cases = [
        ("https://www.amazon.com/dp/B0123456789", "amazon"),
        ("https://www.linkedin.com/in/john-doe/", "linkedin"),
        ("https://www.instagram.com/p/ABC123/", "instagram"),
        ("https://www.tiktok.com/@user/video/123", "tiktok"),
        ("https://twitter.com/user/status/123", "x"),
        ("https://x.com/user/status/123", "x"),
        ("https://www.reddit.com/r/python/comments/123", "reddit"),
        ("https://www.digikey.com/en/products/detail/123", "digikey"),
        ("https://www.mouser.com/ProductDetail/123", "mouser"),
    ]
    
    all_good = True
    for url, expected_domain in test_cases:
        scraper = get_scraper_for(url)
        
        if scraper:
            scraper_name = scraper.__name__.lower()
            # Extract domain from scraper name (e.g., "AmazonScraper" -> "amazon")
            detected_domain = scraper_name.replace("scraper", "")
            
            if detected_domain == expected_domain:
                print(f"✓ {url} → {scraper.__name__}")
            else:
                print(f"✗ {url} → {scraper.__name__} (expected {expected_domain})")
                all_good = False
        else:
            print(f"✗ {url} → No scraper found")
            all_good = False
    
    return all_good


def test_02_trigger_scrape_url():
    """Test 02: Test trigger_scrape_url function"""
    print("\n[Test 02] Testing trigger_scrape_url...")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("⚠ BRIGHTDATA_TOKEN not set - skipping test")
        return True
    
    # Test with a known URL
    test_url = "https://www.amazon.com/dp/B0CRMZHDG8"
    
    try:
        print(f"  Triggering scrape for {test_url}...")
        snapshot_id = trigger_scrape_url(test_url, bearer_token=token)
        
        if snapshot_id:
            print(f"✓ Got snapshot ID: {snapshot_id}")
            return True
        else:
            print("✗ No snapshot ID returned")
            return False
            
    except Exception as e:
        print(f"✗ Trigger failed: {e}")
        return False


def test_03_scraper_url_classification():
    """Test 03: Test URL classification within scrapers"""
    print("\n[Test 03] Testing URL classification...")
    
    try:
        from brightdata.webscraper_api.scrapers.amazon.scraper import AmazonScraper
        
        scraper = AmazonScraper(bearer_token="dummy_token")
        
        test_cases = [
            ("https://www.amazon.com/dp/B123", "product"),
            ("https://www.amazon.com/gp/product/B123", "product"),
            ("https://www.amazon.com/product-reviews/B123", "review"),
            ("https://www.amazon.com/s?k=laptop", "search"),
            ("https://www.amazon.com/sp?seller=A123", "seller"),
        ]
        
        all_good = True
        for url, expected_type in test_cases:
            try:
                url_type = scraper.classify_url(url)
                if url_type == expected_type:
                    print(f"✓ {url} → {url_type}")
                else:
                    print(f"✗ {url} → {url_type} (expected {expected_type})")
                    all_good = False
            except ValueError:
                print(f"✗ {url} → ValueError (couldn't classify)")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"✗ Classification test failed: {e}")
        return False


def test_04_linkedin_url_routing():
    """Test 04: Test LinkedIn URL routing"""
    print("\n[Test 04] Testing LinkedIn URL routing...")
    
    try:
        from brightdata.webscraper_api.scrapers.linkedin.scraper import LinkedInScraper
        
        scraper = LinkedInScraper(bearer_token="dummy_token")
        
        # Check method existence
        methods = [
            ("collect_people_by_url", "People profiles"),
            ("collect_company_by_url", "Company pages"),
            ("collect_jobs_by_url", "Job postings"),
        ]
        
        all_good = True
        for method_name, description in methods:
            if hasattr(scraper, method_name):
                print(f"✓ Has method for {description}: {method_name}")
            else:
                print(f"✗ Missing method for {description}: {method_name}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"✗ LinkedIn routing test failed: {e}")
        return False


def test_05_scraper_constants():
    """Test 05: Test scraper dataset constants"""
    print("\n[Test 05] Testing scraper constants...")
    
    try:
        from brightdata.webscraper_api.scrapers.amazon.scraper import AmazonScraper
        from brightdata.webscraper_api.scrapers.linkedin.scraper import LinkedInScraper
        
        # Check Amazon datasets
        if hasattr(AmazonScraper, '_DATASET'):
            datasets = AmazonScraper._DATASET
            print(f"✓ Amazon has {len(datasets)} dataset IDs")
            
            for key, value in datasets.items():
                if value and value.startswith("gd_"):
                    print(f"  ✓ {key}: {value}")
                else:
                    print(f"  ✗ {key}: Invalid dataset ID")
                    return False
        else:
            print("✗ Amazon missing _DATASET constant")
            return False
        
        # Check patterns
        if hasattr(AmazonScraper, 'PATTERNS'):
            print(f"✓ Amazon has {len(AmazonScraper.PATTERNS)} URL patterns")
        else:
            print("✗ Amazon missing PATTERNS constant")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Constants test failed: {e}")
        return False


def test_06_scraper_cost_tracking():
    """Test 06: Test scraper cost tracking"""
    print("\n[Test 06] Testing cost tracking...")
    
    try:
        from brightdata.webscraper_api.base_specialized_scraper import BrightdataBaseSpecializedScraper
        
        # Check cost constant
        if hasattr(BrightdataBaseSpecializedScraper, 'COST_PER_RECORD'):
            cost = BrightdataBaseSpecializedScraper.COST_PER_RECORD
            print(f"✓ Base cost per record: ${cost}")
            
            if isinstance(cost, (int, float)) and cost > 0:
                print("✓ Cost is valid numeric value")
                return True
            else:
                print("✗ Invalid cost value")
                return False
        else:
            print("✗ Missing COST_PER_RECORD constant")
            return False
            
    except Exception as e:
        print(f"✗ Cost tracking test failed: {e}")
        return False


def test_07_discovery_methods():
    """Test 07: Test discovery methods exist"""
    print("\n[Test 07] Testing discovery methods...")
    
    try:
        from brightdata.webscraper_api.scrapers.amazon.scraper import AmazonScraper
        
        scraper = AmazonScraper(bearer_token="dummy_token")
        
        discovery_methods = [
            "products__discover_by_keyword",
            "products__discover_by_category",
            "products_search__search",
        ]
        
        found = 0
        for method in discovery_methods:
            if hasattr(scraper, method):
                print(f"✓ Has discovery method: {method}")
                found += 1
            else:
                print(f"⚠ Missing discovery method: {method}")
        
        if found > 0:
            print(f"✓ Found {found} discovery methods")
            return True
        else:
            print("✗ No discovery methods found")
            return False
            
    except Exception as e:
        print(f"✗ Discovery methods test failed: {e}")
        return False


def test_08_base_scraper_endpoints():
    """Test 08: Test base scraper API endpoints"""
    print("\n[Test 08] Testing base scraper endpoints...")
    
    try:
        from brightdata.webscraper_api.base_specialized_scraper import BrightdataBaseSpecializedScraper
        
        # Check endpoint URLs
        endpoints = [
            ("trigger_url", "https://api.brightdata.com/datasets/v3/trigger"),
            ("status_base_url", "https://api.brightdata.com/datasets/v3/progress"),
            ("result_base_url", "https://api.brightdata.com/datasets/v3/snapshot"),
        ]
        
        all_good = True
        for attr, expected_url in endpoints:
            if hasattr(BrightdataBaseSpecializedScraper, attr):
                actual_url = getattr(BrightdataBaseSpecializedScraper, attr)
                if actual_url == expected_url:
                    print(f"✓ {attr}: {actual_url}")
                else:
                    print(f"✗ {attr}: {actual_url} (expected {expected_url})")
                    all_good = False
            else:
                print(f"✗ Missing endpoint: {attr}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"✗ Endpoints test failed: {e}")
        return False


def test_09_fallback_behavior():
    """Test 09: Test fallback behavior for unknown URLs"""
    print("\n[Test 09] Testing fallback behavior...")
    
    # Test with URL that has no scraper
    test_url = "https://unknown-website-12345.com/page"
    
    try:
        # Check if scraper is found
        scraper = get_scraper_for(test_url)
        
        if scraper is None:
            print("✓ Correctly returns None for unknown URL")
            
            # Test trigger_scrape_url behavior
            snapshot = trigger_scrape_url(test_url, raise_if_unknown=False)
            if snapshot is None:
                print("✓ trigger_scrape_url returns None when raise_if_unknown=False")
            else:
                print("✗ trigger_scrape_url should return None")
                return False
            
            # Test with raise_if_unknown=True
            try:
                trigger_scrape_url(test_url, raise_if_unknown=True)
                print("✗ Should have raised ValueError")
                return False
            except ValueError as e:
                print(f"✓ Correctly raised ValueError: {e}")
                return True
                
        else:
            print(f"✗ Unexpectedly found scraper: {scraper}")
            return False
            
    except Exception as e:
        print(f"✗ Fallback test failed: {e}")
        return False


def test_10_result_data_structure():
    """Test 10: Test ScrapeResult data structure"""
    print("\n[Test 10] Testing ScrapeResult structure...")
    
    try:
        from brightdata.models import ScrapeResult
        from datetime import datetime
        
        # Create a test result
        result = ScrapeResult(
            success=True,
            url="https://example.com",
            status="ready",
            data={"test": "data"},
            error=None,
            snapshot_id="test_123",
            cost=0.001,
            fallback_used=False,
            root_domain="example",
            request_sent_at=datetime.utcnow(),
            data_received_at=datetime.utcnow(),
            html_char_size=100,
            row_count=1,
            field_count=5
        )
        
        # Check attributes
        checks = [
            (result.success == True, "success flag"),
            (result.url == "https://example.com", "URL"),
            (result.status == "ready", "status"),
            (result.data == {"test": "data"}, "data"),
            (result.snapshot_id == "test_123", "snapshot_id"),
            (result.cost == 0.001, "cost"),
            (result.root_domain == "example", "root_domain"),
            (isinstance(result.request_sent_at, datetime), "request timestamp"),
            (result.html_char_size == 100, "html_char_size"),
        ]
        
        all_good = True
        for condition, description in checks:
            if condition:
                print(f"✓ {description} is correct")
            else:
                print(f"✗ {description} is incorrect")
                all_good = False
        
        # Test save_data_to_file method
        if hasattr(result, 'save_data_to_file'):
            print("✓ Has save_data_to_file method")
        else:
            print("✗ Missing save_data_to_file method")
            all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"✗ Result structure test failed: {e}")
        return False


def main():
    """Run all basic operation tests"""
    print("=" * 60)
    print("Specialized Scrapers - Test Suite 1: Basic Operations")
    print("=" * 60)
    
    tests = [
        test_01_url_detection,
        test_02_trigger_scrape_url,
        test_03_scraper_url_classification,
        test_04_linkedin_url_routing,
        test_05_scraper_constants,
        test_06_scraper_cost_tracking,
        test_07_discovery_methods,
        test_08_base_scraper_endpoints,
        test_09_fallback_behavior,
        test_10_result_data_structure,
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