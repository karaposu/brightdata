#!/usr/bin/env python3
"""
Quick test to verify crawler API imports work
"""

print("Testing imports...")

try:
    from brightdata.crawlerapi import CrawlerAPI, crawl_url, crawl_domain, acrawl_url, acrawl_domain
    print("✓ Direct imports from crawlerapi work")
except ImportError as e:
    print(f"✗ Direct import failed: {e}")

try:
    from brightdata import CrawlerAPI, crawl_url, crawl_domain
    print("✓ Imports from brightdata package work")
except ImportError as e:
    print(f"✗ Package import failed: {e}")

try:
    from brightdata import crawl_single_url, crawl_website
    print("✓ Auto.py convenience functions import")
except ImportError as e:
    print(f"✗ Auto.py import failed: {e}")

print("\nTesting CrawlerAPI instantiation...")
try:
    api = CrawlerAPI()
    print(f"✓ CrawlerAPI created successfully")
    print(f"  Dataset ID: {api.dataset_id}")
    print(f"  Base URL: {api.base_url}")
except Exception as e:
    print(f"✗ CrawlerAPI creation failed: {e}")

print("\nAll import tests completed!")