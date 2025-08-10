#!/usr/bin/env python3
"""
Smoke tests for BrightData Specialized Scrapers
"""
# To run: python -m smoke_tests.specialized_scraper.test_basic

import os
import sys
import asyncio
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from brightdata import scrape_url, scrape_url_async
from brightdata.ready_scrapers.amazon import AmazonScraper
from brightdata.ready_scrapers.linkedin import LinkedInScraper
from brightdata.registry import get_scraper_for
from dotenv import load_dotenv

load_dotenv()


def test_auto_scraper_detection():
    """Test automatic scraper detection"""
    print("\n=== Auto Scraper Detection Test ===")
    
    test_cases = [
        ("https://www.amazon.com/dp/B0CRMZHDG8", "amazon"),
        ("https://www.linkedin.com/in/example/", "linkedin"),
        ("https://www.instagram.com/p/example/", "instagram"),
        ("https://www.tiktok.com/@example/video/123", "tiktok"),
        ("https://twitter.com/example/status/123", "x"),
        ("https://www.reddit.com/r/example/comments/123", "reddit"),
    ]
    
    passed = 0
    for url, expected_domain in test_cases:
        scraper_class = get_scraper_for(url)
        if scraper_class:
            print(f"✓ {url} → {scraper_class.__name__}")
            passed += 1
        else:
            print(f"✗ {url} → No scraper found (expected {expected_domain})")
    
    print(f"\nDetection success: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_amazon_scraper():
    """Test Amazon scraper basic functionality"""
    print("\n=== Amazon Scraper Test ===")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("✗ BRIGHTDATA_TOKEN not set - skipping test")
        return False
    
    try:
        scraper = AmazonScraper(bearer_token=token)
        print("✓ Amazon scraper initialized")
        
        # Test URL classification
        test_urls = [
            ("https://www.amazon.com/dp/B0CRMZHDG8", "product"),
            ("https://www.amazon.com/product-reviews/B0CRMZHDG8", "review"),
            ("https://www.amazon.com/s?k=laptop", "search"),
        ]
        
        for url, expected_type in test_urls:
            try:
                url_type = scraper.classify_url(url)
                if url_type == expected_type:
                    print(f"✓ Correctly classified {url} as {url_type}")
                else:
                    print(f"✗ Misclassified {url} as {url_type} (expected {expected_type})")
                    return False
            except Exception as e:
                print(f"✗ Failed to classify {url}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Amazon scraper test failed: {e}")
        return False


async def test_scrape_url_async():
    """Test async scrape_url functionality"""
    print("\n=== Async scrape_url Test ===")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("✗ BRIGHTDATA_TOKEN not set - skipping test")
        return False
    
    # Test with a URL that should fall back to browser API
    test_url = "https://example.com"
    
    print(f"Testing async scrape with {test_url}...")
    
    try:
        result = await scrape_url_async(
            test_url,
            bearer_token=token,
            fallback_to_browser_api=True,
            poll_timeout=30
        )
        
        if result:
            print(f"✓ Got result: success={result.success}, status={result.status}")
            if result.data:
                print(f"✓ Data received: {len(str(result.data))} chars")
            return True
        else:
            print("✗ No result returned")
            return False
            
    except Exception as e:
        print(f"✗ Async scrape test failed: {e}")
        return False


def test_linkedin_scraper():
    """Test LinkedIn scraper URL routing"""
    print("\n=== LinkedIn Scraper Test ===")
    
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        print("✗ BRIGHTDATA_TOKEN not set - skipping test")
        return False
    
    try:
        scraper = LinkedInScraper(bearer_token=token)
        print("✓ LinkedIn scraper initialized")
        
        # Test URL classification
        test_urls = [
            ("https://www.linkedin.com/in/example/", "people"),
            ("https://www.linkedin.com/company/12345/", "company"),
            ("https://www.linkedin.com/jobs/view/12345/", "jobs"),
        ]
        
        for url, expected_type in test_urls:
            # LinkedIn scraper uses different method names
            if expected_type == "people" and hasattr(scraper, 'collect_people_by_url'):
                print(f"✓ LinkedIn scraper can handle {expected_type} URLs")
            elif expected_type == "company" and hasattr(scraper, 'collect_company_by_url'):
                print(f"✓ LinkedIn scraper can handle {expected_type} URLs")
            elif expected_type == "jobs" and hasattr(scraper, 'collect_jobs_by_url'):
                print(f"✓ LinkedIn scraper can handle {expected_type} URLs")
            else:
                print(f"✗ LinkedIn scraper missing handler for {expected_type}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ LinkedIn scraper test failed: {e}")
        return False


def test_scraper_registry():
    """Test scraper registry functionality"""
    print("\n=== Scraper Registry Test ===")
    
    # Import all scrapers to populate registry
    from brightdata.ready_scrapers import amazon, linkedin, instagram, tiktok, x, reddit
    
    domains = ["amazon", "linkedin", "instagram", "tiktok", "x", "reddit"]
    
    found = 0
    for domain in domains:
        test_urls = {
            "amazon": "https://www.amazon.com/dp/test",
            "linkedin": "https://www.linkedin.com/in/test",
            "instagram": "https://www.instagram.com/p/test",
            "tiktok": "https://www.tiktok.com/@test",
            "x": "https://x.com/test",
            "reddit": "https://www.reddit.com/r/test"
        }
        
        scraper = get_scraper_for(test_urls.get(domain, f"https://{domain}.com"))
        if scraper:
            print(f"✓ {domain} scraper registered")
            found += 1
        else:
            print(f"✗ {domain} scraper not found in registry")
    
    print(f"\nRegistry check: {found}/{len(domains)} scrapers found")
    return found == len(domains)


def main():
    """Run all specialized scraper smoke tests"""
    print("BrightData Specialized Scrapers Smoke Tests")
    print("=" * 50)
    
    sync_tests = [
        test_auto_scraper_detection,
        test_scraper_registry,
        test_amazon_scraper,
        test_linkedin_scraper,
    ]
    
    async_tests = [
        test_scrape_url_async,
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