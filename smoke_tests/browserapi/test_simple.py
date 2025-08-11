#!/usr/bin/env python3
"""
Simple Browser API test to check basic functionality
"""
# To run: python -m smoke_tests.browserapi.test_simple

import sys
import asyncio
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from brightdata.browserapi import BrowserAPI
from dotenv import load_dotenv

load_dotenv()


async def test_simple():
    """Simple test that matches browser_api.py main() demo"""
    print("Simple Browser API Test")
    print("=" * 50)
    
    try:
        # Test 1: Create API instance
        print("\n1. Creating BrowserAPI instance...")
        api = BrowserAPI(strategy="noop")
        print("✓ BrowserAPI created")
        
        # Test 2: Simple fetch
        print("\n2. Fetching example.com...")
        try:
            result = await api.fetch_async("https://example.com")
            if result.success:
                print(f"✓ Fetch successful: {result.html_char_size} chars")
            else:
                print(f"✗ Fetch failed: {result.error}")
        except Exception as e:
            print(f"✗ Exception during fetch: {e}")
            
        # Test 3: Close
        print("\n3. Closing API...")
        try:
            await api.close()
            print("✓ API closed")
        except:
            print("⚠ Close may not be implemented")
            
        print("\n" + "=" * 50)
        print("Test completed")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_simple())