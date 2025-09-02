#!/usr/bin/env python3
"""
pure_crawler_api.py - Minimal working implementation of BrightData Crawler API

This uses the official API code from crawler_api.md to test basic functionality.
Run with: python pure_crawler_api.py
"""

import os
import json
import time
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PureCrawlerAPI:
    """Minimal Crawler API implementation using official API examples"""
    
    DATASET_ID = "gd_m6gjtfmeh43we6cqc"
    BASE_URL = "https://api.brightdata.com/datasets/v3"
    
    def __init__(self, bearer_token: Optional[str] = None):
        """Initialize with bearer token from env or parameter"""
        self.bearer_token = bearer_token or os.getenv('BRIGHTDATA_TOKEN')
        if not self.bearer_token:
            raise ValueError("BRIGHTDATA_TOKEN not found. Set it in .env or pass as parameter")
        
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
    
    def collect_by_url(self, urls: List[str], include_errors: bool = True) -> Dict[str, Any]:
        """
        Collect data from specific URLs
        Returns snapshot_id for polling
        """
        # Convert single URL to list
        if isinstance(urls, str):
            urls = [urls]
        
        # Prepare request
        endpoint = f"{self.BASE_URL}/trigger"
        params = {
            "dataset_id": self.DATASET_ID,
            "include_errors": str(include_errors).lower(),
        }
        
        # Format data as required by API
        data = [{"url": url} for url in urls]
        
        # Make request
        print(f"Triggering collect for {len(urls)} URL(s)...")
        response = requests.post(
            endpoint, 
            headers=self.headers, 
            params=params, 
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Snapshot ID: {result.get('snapshot_id')}")
            return result
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return {"error": response.text, "status_code": response.status_code}
    
    def discover_by_domain(
        self, 
        domain_url: str, 
        filter: str = "", 
        exclude_filter: str = "",
        include_errors: bool = True
    ) -> Dict[str, Any]:
        """
        Discover and crawl all URLs from a domain
        Returns snapshot_id for polling
        """
        # Prepare request
        endpoint = f"{self.BASE_URL}/trigger"
        params = {
            "dataset_id": self.DATASET_ID,
            "include_errors": str(include_errors).lower(),
            "type": "discover_new",
            "discover_by": "domain_url",
        }
        
        # Format data as required by API
        data = [{
            "url": domain_url,
            "filter": filter,
            "exclude_filter": exclude_filter
        }]
        
        # Make request
        print(f"Triggering discover for domain: {domain_url}")
        if filter:
            print(f"  Filter: {filter}")
        if exclude_filter:
            print(f"  Exclude: {exclude_filter}")
            
        response = requests.post(
            endpoint, 
            headers=self.headers, 
            params=params, 
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Snapshot ID: {result.get('snapshot_id')}")
            return result
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return {"error": response.text, "status_code": response.status_code}
    
    def get_snapshot_status(self, snapshot_id: str) -> Dict[str, Any]:
        """Check the status of a snapshot"""
        endpoint = f"{self.BASE_URL}/progress/{snapshot_id}"
        
        response = requests.get(endpoint, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text, "status_code": response.status_code}
    
    def get_snapshot_data(self, snapshot_id: str, format: str = "json") -> Any:
        """
        Retrieve the actual data from a completed snapshot
        format: json, csv, jsonl, etc.
        """
        endpoint = f"{self.BASE_URL}/snapshot/{snapshot_id}"
        params = {"format": format}
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        
        if response.status_code == 200:
            if format == "json":
                return response.json()
            else:
                return response.text
        else:
            return {"error": response.text, "status_code": response.status_code}
    
    def poll_until_ready(
        self, 
        snapshot_id: str, 
        poll_interval: int = 10, 
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Poll until snapshot is ready or timeout
        Returns the final data or error
        """
        start_time = time.time()
        
        print(f"Polling snapshot {snapshot_id}...")
        
        while time.time() - start_time < timeout:
            status = self.get_snapshot_status(snapshot_id)
            
            if "error" in status:
                print(f"Error checking status: {status['error']}")
                return status
            
            current_status = status.get("status", "unknown")
            print(f"  Status: {current_status}")
            
            if current_status == "ready":
                print("Snapshot ready! Retrieving data...")
                return self.get_snapshot_data(snapshot_id)
            elif current_status in ["failed", "error"]:
                print(f"Snapshot failed: {status}")
                return status
            
            time.sleep(poll_interval)
        
        print(f"Timeout after {timeout} seconds")
        return {"error": "Timeout", "status": "timeout"}


def main():
    """Example usage of the pure crawler API"""
    
    # Initialize API
    crawler = PureCrawlerAPI()
    
    # Example 1: Collect specific URLs
    print("\n" + "="*50)
    print("Example 1: Collect by URL")
    print("="*50)
    
    urls = [
        "https://example.com",
        "https://example.com/about"
    ]
    
    result = crawler.collect_by_url(urls)
    
    if "snapshot_id" in result:
        snapshot_id = result["snapshot_id"]
        print(f"\n📸 Got Snapshot ID: {snapshot_id}")
        print("Now polling for results...")
        
        data = crawler.poll_until_ready(snapshot_id, poll_interval=5, timeout=120)
        
        if isinstance(data, list) and len(data) > 0:
            print(f"\nCollected {len(data)} pages:")
            for page in data[:2]:  # Show first 2
                print(f"  - URL: {page.get('url')}")
                if page.get('page_title'):
                    print(f"    Title: {page.get('page_title')}")
                if page.get('markdown'):
                    print(f"    Markdown: {page.get('markdown')[:100]}...")
    
    # Example 2: Discover domain
    print("\n" + "="*50)
    print("Example 2: Discover by Domain")
    print("="*50)
    
    domain = "https://example.com"
    
    result = crawler.discover_by_domain(
        domain_url=domain,
        filter="",  # Include all
        exclude_filter="/admin/*"  # Exclude admin pages
    )
    
    if "snapshot_id" in result:
        snapshot_id = result["snapshot_id"]
        print(f"\n📸 Got Snapshot ID: {snapshot_id}")
        print("Now polling for results...")
        
        data = crawler.poll_until_ready(snapshot_id, poll_interval=5, timeout=120)
        
        if isinstance(data, list) and len(data) > 0:
            print(f"\nDiscovered {len(data)} pages from {domain}:")
            
            # Show URL structure
            internal_urls = [p['url'] for p in data if domain in p.get('url', '')]
            external_urls = [p['url'] for p in data if domain not in p.get('url', '')]
            
            print(f"  Internal URLs: {len(internal_urls)}")
            print(f"  External URLs: {len(external_urls)}")
            
            # Show sample URLs
            print("\n  Sample URLs found:")
            for url in internal_urls[:5]:
                print(f"    - {url}")


if __name__ == "__main__":
    print("BrightData Crawler API - Pure Implementation Test")
    print("Make sure BRIGHTDATA_TOKEN is set in your .env file")
    
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()