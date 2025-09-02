#!/usr/bin/env python3
"""
brightdata/crawlerapi/crawler_api.py

BrightData Crawler API implementation for collecting and discovering web content.
Supports both single URL collection and full domain discovery with filtering.
"""

import os
import time
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

import requests
import aiohttp
from dotenv import load_dotenv

from brightdata.models import CrawlResult

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CrawlerAPI:
    """
    BrightData Crawler API client for web crawling and content extraction.
    
    Supports two main operations:
    1. Collect - Get specific URLs
    2. Discover - Crawl entire domains with filters
    """
    
    DATASET_ID = "gd_m6gjtfmeh43we6cqc"
    BASE_URL = "https://api.brightdata.com/datasets/v3"
    
    # Cost estimation (needs verification from BrightData)
    COST_PER_PAGE = 0.001  # $0.001 per page (estimate)
    
    def __init__(self, bearer_token: Optional[str] = None):
        """
        Initialize Crawler API client.
        
        Args:
            bearer_token: BrightData API token. If not provided, uses BRIGHTDATA_TOKEN env var.
        """
        self.bearer_token = bearer_token or os.getenv('BRIGHTDATA_TOKEN')
        if not self.bearer_token:
            raise ValueError("BRIGHTDATA_TOKEN not found. Set it in .env or pass as parameter")
        
        self.dataset_id = self.DATASET_ID
        self.base_url = self.BASE_URL
        
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
    
    # ===== SYNCHRONOUS METHODS =====
    
    def collect_by_url(
        self, 
        urls: Union[str, List[str]],
        include_errors: bool = True
    ) -> CrawlResult:
        """
        Collect content from specific URLs.
        
        Args:
            urls: Single URL or list of URLs to collect
            include_errors: Whether to include error details in response
            
        Returns:
            CrawlResult with collected page data
        """
        # Ensure urls is a list
        if isinstance(urls, str):
            urls = [urls]
        
        # Prepare request
        endpoint = f"{self.BASE_URL}/trigger"
        params = {
            "dataset_id": self.DATASET_ID,
            "include_errors": str(include_errors).lower(),
        }
        
        # Format data for API
        data = [{"url": url} for url in urls]
        
        # Track request time
        request_time = datetime.utcnow()
        
        # Make request
        logger.debug(f"Triggering collect for {len(urls)} URL(s)")
        response = requests.post(
            endpoint,
            headers=self.headers,
            params=params,
            json=data
        )
        
        # Handle response
        if response.status_code == 200:
            result = response.json()
            snapshot_id = result.get("snapshot_id")
            
            # Create initial CrawlResult
            crawl_result = CrawlResult(
                success=True,
                operation="collect",
                status="triggered",
                input_urls=urls,
                snapshot_id=snapshot_id,
                request_sent_at=request_time,
                snapshot_id_received_at=datetime.utcnow(),
                crawl_params={"include_errors": include_errors}
            )
            
            return crawl_result
        else:
            # Handle error
            return CrawlResult(
                success=False,
                operation="collect",
                status="error",
                input_urls=urls,
                error=f"HTTP {response.status_code}: {response.text}",
                request_sent_at=request_time
            )
    
    def discover_by_domain(
        self,
        domain: str,
        filter_pattern: str = "",
        exclude_pattern: str = "",
        depth: Optional[int] = None,
        ignore_sitemap: Optional[bool] = None,
        include_errors: bool = True
    ) -> CrawlResult:
        """
        Discover and crawl all URLs from a domain.
        
        Args:
            domain: The domain URL to crawl
            filter_pattern: Include only URLs matching this pattern (glob-style)
            exclude_pattern: Exclude URLs matching this pattern
            depth: Maximum crawl depth from starting URL
            ignore_sitemap: Whether to ignore sitemap.xml
            include_errors: Whether to include error details
            
        Returns:
            CrawlResult with discovered pages
        """
        # Prepare request
        endpoint = f"{self.BASE_URL}/trigger"
        params = {
            "dataset_id": self.DATASET_ID,
            "include_errors": str(include_errors).lower(),
            "type": "discover_new",
            "discover_by": "domain_url",
        }
        
        # Build data payload
        data_item = {
            "url": domain,
            "filter": filter_pattern,
            "exclude_filter": exclude_pattern
        }
        
        # Add optional parameters
        if depth is not None:
            data_item["depth"] = depth
        if ignore_sitemap is not None:
            data_item["ignore_sitemap"] = ignore_sitemap
        
        data = [data_item]
        
        # Track request time
        request_time = datetime.utcnow()
        
        # Make request
        logger.debug(f"Triggering discover for domain: {domain}")
        response = requests.post(
            endpoint,
            headers=self.headers,
            params=params,
            json=data
        )
        
        # Track all parameters sent
        crawl_params = {
            "filter": filter_pattern,
            "exclude_filter": exclude_pattern,
            "include_errors": include_errors,
            "type": "discover_new",
            "discover_by": "domain_url"
        }
        if depth is not None:
            crawl_params["depth"] = depth
        if ignore_sitemap is not None:
            crawl_params["ignore_sitemap"] = ignore_sitemap
        
        # Handle response
        if response.status_code == 200:
            result = response.json()
            snapshot_id = result.get("snapshot_id")
            
            # Create initial CrawlResult
            crawl_result = CrawlResult(
                success=True,
                operation="discover",
                status="triggered",
                domain=domain,
                snapshot_id=snapshot_id,
                request_sent_at=request_time,
                snapshot_id_received_at=datetime.utcnow(),
                crawl_params=crawl_params
            )
            
            return crawl_result
        else:
            # Handle error
            return CrawlResult(
                success=False,
                operation="discover",
                status="error",
                domain=domain,
                error=f"HTTP {response.status_code}: {response.text}",
                request_sent_at=request_time,
                crawl_params=crawl_params
            )
    
    def get_snapshot_status(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Check the status of a snapshot.
        
        Args:
            snapshot_id: The snapshot ID to check
            
        Returns:
            Status information dictionary
        """
        endpoint = f"{self.BASE_URL}/progress/{snapshot_id}"
        
        response = requests.get(endpoint, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"HTTP {response.status_code}: {response.text}",
                "snapshot_id": snapshot_id
            }
    
    def get_snapshot_data(self, snapshot_id: str, format: str = "json") -> Any:
        """
        Retrieve the actual data from a completed snapshot.
        
        Args:
            snapshot_id: The snapshot ID to retrieve
            format: Output format (json, csv, jsonl)
            
        Returns:
            The crawled data
        """
        endpoint = f"{self.BASE_URL}/snapshot/{snapshot_id}"
        params = {"format": format}
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        
        if response.status_code == 200:
            if format == "json":
                return response.json()
            else:
                return response.text
        elif response.status_code == 202:
            # 202 means "building" - this is not an error, just not ready yet
            try:
                data = response.json()
                if data.get("status") == "building":
                    return {"status": "building", "message": data.get("message", "Snapshot is building")}
            except:
                pass
            return {"status": "building", "message": "Snapshot is building"}
        else:
            return {
                "error": f"HTTP {response.status_code}: {response.text}",
                "snapshot_id": snapshot_id
            }
    
    def poll_until_ready(
        self,
        crawl_result: CrawlResult,
        poll_interval: int = 10,
        timeout: int = 300
    ) -> CrawlResult:
        """
        Poll snapshot until ready and update CrawlResult with data.
        
        Args:
            crawl_result: The CrawlResult to update
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait
            
        Returns:
            Updated CrawlResult with data or error
        """
        if not crawl_result.snapshot_id:
            crawl_result.status = "error"
            crawl_result.error = "No snapshot_id available"
            return crawl_result
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check status
            status = self.get_snapshot_status(crawl_result.snapshot_id)
            crawl_result.snapshot_polled_at.append(datetime.utcnow())
            
            if "error" in status:
                crawl_result.status = "error"
                crawl_result.error = status.get("error")
                crawl_result.success = False
                return crawl_result
            
            current_status = status.get("status", "unknown")
            
            if current_status == "ready":
                # Get the data
                data = self.get_snapshot_data(crawl_result.snapshot_id)
                crawl_result.data_received_at = datetime.utcnow()
                
                # Check if data is still building (202 response)
                if isinstance(data, dict) and data.get("status") == "building":
                    # Not actually ready yet, continue polling
                    crawl_result.status = "building"
                    time.sleep(poll_interval)
                    continue
                
                if isinstance(data, list):
                    crawl_result.pages = data
                    crawl_result.page_count = len(data)
                    crawl_result.status = "ready"
                    crawl_result.success = True
                    
                    # Populate collection duration if available
                    if "collection_duration" in status:
                        crawl_result.collection_duration_ms = status["collection_duration"]
                    
                    # Analyze content
                    crawl_result.analyze_content()
                    
                    # Estimate cost
                    crawl_result.cost = crawl_result.page_count * self.COST_PER_PAGE
                    
                elif isinstance(data, dict) and "error" in data:
                    crawl_result.status = "error"
                    crawl_result.error = data.get("error")
                    crawl_result.success = False
                else:
                    crawl_result.pages = [data] if data else []
                    crawl_result.page_count = 1 if data else 0
                    crawl_result.status = "ready"
                
                return crawl_result
                
            elif current_status in ["failed", "error"]:
                crawl_result.status = current_status
                crawl_result.error = status.get("error", "Unknown error")
                crawl_result.success = False
                return crawl_result
            
            # Still running, wait
            time.sleep(poll_interval)
        
        # Timeout reached
        crawl_result.status = "timeout"
        crawl_result.error = f"Timeout after {timeout} seconds"
        crawl_result.success = False
        return crawl_result
    
    # ===== ASYNCHRONOUS METHODS =====
    
    async def collect_by_url_async(
        self,
        urls: Union[str, List[str]],
        include_errors: bool = True
    ) -> CrawlResult:
        """
        Async version of collect_by_url.
        """
        if isinstance(urls, str):
            urls = [urls]
        
        endpoint = f"{self.BASE_URL}/trigger"
        params = {
            "dataset_id": self.DATASET_ID,
            "include_errors": str(include_errors).lower(),
        }
        
        data = [{"url": url} for url in urls]
        request_time = datetime.utcnow()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                headers=self.headers,
                params=params,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    snapshot_id = result.get("snapshot_id")
                    
                    return CrawlResult(
                        success=True,
                        operation="collect",
                        status="triggered",
                        input_urls=urls,
                        snapshot_id=snapshot_id,
                        request_sent_at=request_time,
                        snapshot_id_received_at=datetime.utcnow(),
                        crawl_params={"include_errors": include_errors}
                    )
                else:
                    text = await response.text()
                    return CrawlResult(
                        success=False,
                        operation="collect",
                        status="error",
                        input_urls=urls,
                        error=f"HTTP {response.status}: {text}",
                        request_sent_at=request_time
                    )
    
    async def discover_by_domain_async(
        self,
        domain: str,
        filter_pattern: str = "",
        exclude_pattern: str = "",
        depth: Optional[int] = None,
        ignore_sitemap: Optional[bool] = None,
        include_errors: bool = True
    ) -> CrawlResult:
        """
        Async version of discover_by_domain.
        """
        endpoint = f"{self.BASE_URL}/trigger"
        params = {
            "dataset_id": self.DATASET_ID,
            "include_errors": str(include_errors).lower(),
            "type": "discover_new",
            "discover_by": "domain_url",
        }
        
        data_item = {
            "url": domain,
            "filter": filter_pattern,
            "exclude_filter": exclude_pattern
        }
        
        if depth is not None:
            data_item["depth"] = depth
        if ignore_sitemap is not None:
            data_item["ignore_sitemap"] = ignore_sitemap
        
        data = [data_item]
        request_time = datetime.utcnow()
        
        crawl_params = {
            "filter": filter_pattern,
            "exclude_filter": exclude_pattern,
            "include_errors": include_errors,
            "type": "discover_new",
            "discover_by": "domain_url"
        }
        if depth is not None:
            crawl_params["depth"] = depth
        if ignore_sitemap is not None:
            crawl_params["ignore_sitemap"] = ignore_sitemap
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                headers=self.headers,
                params=params,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    snapshot_id = result.get("snapshot_id")
                    
                    return CrawlResult(
                        success=True,
                        operation="discover",
                        status="triggered",
                        domain=domain,
                        snapshot_id=snapshot_id,
                        request_sent_at=request_time,
                        snapshot_id_received_at=datetime.utcnow(),
                        crawl_params=crawl_params
                    )
                else:
                    text = await response.text()
                    return CrawlResult(
                        success=False,
                        operation="discover",
                        status="error",
                        domain=domain,
                        error=f"HTTP {response.status}: {text}",
                        request_sent_at=request_time,
                        crawl_params=crawl_params
                    )
    
    async def poll_until_ready_async(
        self,
        crawl_result: CrawlResult,
        poll_interval: int = 10,
        timeout: int = 300
    ) -> CrawlResult:
        """
        Async version of poll_until_ready.
        """
        if not crawl_result.snapshot_id:
            crawl_result.status = "error"
            crawl_result.error = "No snapshot_id available"
            return crawl_result
        
        start_time = asyncio.get_event_loop().time()
        
        async with aiohttp.ClientSession() as session:
            while asyncio.get_event_loop().time() - start_time < timeout:
                # Check status
                endpoint = f"{self.BASE_URL}/progress/{crawl_result.snapshot_id}"
                
                async with session.get(endpoint, headers=self.headers) as response:
                    if response.status == 200:
                        status = await response.json()
                        crawl_result.snapshot_polled_at.append(datetime.utcnow())
                        
                        current_status = status.get("status", "unknown")
                        
                        if current_status == "ready":
                            # Get the data
                            data_endpoint = f"{self.BASE_URL}/snapshot/{crawl_result.snapshot_id}"
                            params = {"format": "json"}
                            
                            async with session.get(
                                data_endpoint,
                                headers=self.headers,
                                params=params
                            ) as data_response:
                                if data_response.status == 200:
                                    data = await data_response.json()
                                    crawl_result.data_received_at = datetime.utcnow()
                                    
                                    if isinstance(data, list):
                                        crawl_result.pages = data
                                        crawl_result.page_count = len(data)
                                        crawl_result.status = "ready"
                                        crawl_result.success = True
                                        
                                        if "collection_duration" in status:
                                            crawl_result.collection_duration_ms = status["collection_duration"]
                                        
                                        crawl_result.analyze_content()
                                        crawl_result.cost = crawl_result.page_count * self.COST_PER_PAGE
                                    else:
                                        crawl_result.pages = [data] if data else []
                                        crawl_result.page_count = 1 if data else 0
                                        crawl_result.status = "ready"
                                    
                                    return crawl_result
                                elif data_response.status == 202:
                                    # 202 means "building" - continue polling
                                    crawl_result.status = "building"
                                    # Don't return, let the loop continue
                        
                        elif current_status in ["failed", "error"]:
                            crawl_result.status = current_status
                            crawl_result.error = status.get("error", "Unknown error")
                            crawl_result.success = False
                            return crawl_result
                    else:
                        crawl_result.status = "error"
                        crawl_result.error = f"HTTP {response.status}"
                        crawl_result.success = False
                        return crawl_result
                
                # Still running, wait
                await asyncio.sleep(poll_interval)
        
        # Timeout reached
        crawl_result.status = "timeout"
        crawl_result.error = f"Timeout after {timeout} seconds"
        crawl_result.success = False
        return crawl_result


# ===== CONVENIENCE FUNCTIONS =====

def crawl_url(url: str, **kwargs) -> CrawlResult:
    """
    Simple function to crawl a single URL and get results.
    
    Args:
        url: The URL to crawl
        **kwargs: Additional parameters for the crawler
        
    Returns:
        CrawlResult with the page data
    """
    crawler = CrawlerAPI()
    result = crawler.collect_by_url(url)
    
    if result.success and result.snapshot_id:
        # Poll for results
        poll_interval = kwargs.get("poll_interval", 10)
        timeout = kwargs.get("timeout", 120)
        result = crawler.poll_until_ready(result, poll_interval, timeout)
    
    return result


def crawl_domain(domain: str, **kwargs) -> CrawlResult:
    """
    Simple function to crawl an entire domain.
    
    Args:
        domain: The domain to crawl
        **kwargs: Additional parameters (filter, exclude_filter, depth, etc.)
        
    Returns:
        CrawlResult with all discovered pages
    """
    crawler = CrawlerAPI()
    result = crawler.discover_by_domain(
        domain,
        filter_pattern=kwargs.get("filter", ""),
        exclude_pattern=kwargs.get("exclude", ""),
        depth=kwargs.get("depth"),
        ignore_sitemap=kwargs.get("ignore_sitemap")
    )
    
    if result.success and result.snapshot_id:
        # Poll for results (longer timeout for discovery)
        poll_interval = kwargs.get("poll_interval", 15)
        timeout = kwargs.get("timeout", 600)
        result = crawler.poll_until_ready(result, poll_interval, timeout)
    
    return result


# ===== ASYNC CONVENIENCE FUNCTIONS =====

async def acrawl_url(url: str, **kwargs) -> CrawlResult:
    """
    Asynchronously crawl a single URL using the Crawler API.
    
    This is a convenience function that:
    1. Creates a CrawlerAPI instance
    2. Calls collect_by_url with the URL
    3. Polls until ready using async polling
    4. Returns the complete CrawlResult
    
    Args:
        url: The URL to crawl
        **kwargs: Additional arguments:
            - bearer_token: Optional API token
            - include_errors: Include error details (default: True)
            - poll_interval: Seconds between polls (default: 10)
            - timeout: Maximum wait time in seconds (default: 300)
    
    Returns:
        CrawlResult with the crawled page data
    """
    crawler = CrawlerAPI(bearer_token=kwargs.get("bearer_token"))
    
    # Trigger the collection
    result = await crawler.collect_by_url_async([url], kwargs.get("include_errors", True))
    
    if result.success and result.snapshot_id:
        # Poll for results
        poll_interval = kwargs.get("poll_interval", 10)
        timeout = kwargs.get("timeout", 300)
        result = await crawler.poll_until_ready_async(result, poll_interval, timeout)
    
    return result


async def acrawl_domain(domain: str, **kwargs) -> CrawlResult:
    """
    Asynchronously crawl an entire domain using the Crawler API.
    
    This is a convenience function that:
    1. Creates a CrawlerAPI instance
    2. Calls discover_by_domain with the domain
    3. Polls until ready using async polling
    4. Returns the complete CrawlResult
    
    Args:
        domain: The domain to discover (e.g., "https://example.com")
        **kwargs: Additional arguments:
            - bearer_token: Optional API token
            - filter_pattern: Include only URLs matching this pattern
            - exclude_pattern: Exclude URLs matching this pattern
            - depth: Maximum crawl depth
            - ignore_sitemap: Whether to ignore sitemap.xml
            - poll_interval: Seconds between polls (default: 15)
            - timeout: Maximum wait time in seconds (default: 600)
    
    Returns:
        CrawlResult with all discovered pages
    """
    crawler = CrawlerAPI(bearer_token=kwargs.get("bearer_token"))
    
    # Trigger the discovery
    result = await crawler.discover_by_domain_async(
        domain,
        filter_pattern=kwargs.get("filter_pattern", ""),
        exclude_pattern=kwargs.get("exclude_pattern", ""),
        depth=kwargs.get("depth"),
        ignore_sitemap=kwargs.get("ignore_sitemap")
    )
    
    if result.success and result.snapshot_id:
        # Poll for results (longer timeout for discovery)
        poll_interval = kwargs.get("poll_interval", 15)
        timeout = kwargs.get("timeout", 600)
        result = await crawler.poll_until_ready_async(result, poll_interval, timeout)
    
    return result


# ===== MAIN (for testing) =====

def main():
    """Test the Crawler API."""
    
    # Test collect
    print("Testing collect_by_url...")
    crawler = CrawlerAPI()
     
    result = crawler.collect_by_url("https://example.com")
    print(f"Collect triggered: {result.snapshot_id}")
    
    if result.success:
        result = crawler.poll_until_ready(result, poll_interval=5, timeout=60)
        if result.success:
            print(f"Collected {result.page_count} pages")
            for page in result.pages[:1]:  # Show first page
                print(f"  - {page.get('url')}")
                if page.get('markdown'):
                    print(f"    Markdown: {page['markdown'][:100]}...")
    
    # Test discover
    print("\nTesting discover_by_domain...")
    result = crawler.discover_by_domain("https://example.com", depth=1)
    print(f"Discover triggered: {result.snapshot_id}")
    
    if result.success:
        result = crawler.poll_until_ready(result, poll_interval=10, timeout=120)
        if result.success:
            print(f"Discovered {result.page_count} pages")
            for url in result.get_urls():
                print(f"  - {url}")


if __name__ == "__main__":
    main()