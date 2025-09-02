#!/usr/bin/env python3
"""
data_gatherer.py - Comprehensive data gathering script for Crawler API testing

This script tests various websites with different parameters and saves results
in a structured way for analysis.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from pure_crawler_api import PureCrawlerAPI

class CrawlerDataGatherer:
    """Gather crawler data from various sources with different parameters"""
    
    def __init__(self, output_dir: str = "crawler_data"):
        self.crawler = PureCrawlerAPI()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create timestamp for this run
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.output_dir / self.run_timestamp
        self.run_dir.mkdir(exist_ok=True)
        
        # Track all operations
        self.operations_log = []
        
    def save_json(self, data: Any, filename: str, subdir: Optional[str] = None):
        """Save data to JSON file in organized structure"""
        if subdir:
            dir_path = self.run_dir / subdir
            dir_path.mkdir(exist_ok=True)
            filepath = dir_path / filename
        else:
            filepath = self.run_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def test_collect_single(self, url: str, name: str) -> Dict[str, Any]:
        """Test collect_by_url with a single URL"""
        print(f"\n{'='*60}")
        print(f"Testing COLLECT on: {name}")
        print(f"URL: {url}")
        print("-"*60)
        
        operation = {
            "type": "collect_single",
            "name": name,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "status": "started"
        }
        
        # Trigger collection
        result = self.crawler.collect_by_url([url])
        
        if "snapshot_id" in result:
            snapshot_id = result["snapshot_id"]
            operation["snapshot_id"] = snapshot_id
            print(f"✅ Snapshot ID: {snapshot_id}")
            
            # Poll for results
            print("Polling for results...")
            data = self.crawler.poll_until_ready(snapshot_id, poll_interval=5, timeout=120)
            
            # Save raw data
            filename = f"collect_{name.replace(' ', '_').lower()}.json"
            filepath = self.save_json(data, filename, "collect")
            
            # Analyze results
            if isinstance(data, list):
                operation["status"] = "success"
                operation["records"] = len(data)
                operation["filepath"] = str(filepath)
                
                # Analyze content types
                content_analysis = self.analyze_content(data)
                operation["analysis"] = content_analysis
                
                print(f"✅ Collected {len(data)} pages")
                print(f"   Saved to: {filepath}")
                self.print_analysis(content_analysis)
                
            else:
                operation["status"] = "error"
                operation["error"] = data
                print(f"❌ Error: {data}")
        else:
            operation["status"] = "failed"
            operation["error"] = result
            print(f"❌ Failed to get snapshot: {result}")
        
        self.operations_log.append(operation)
        return operation
    
    def test_discover(self, domain: str, name: str, 
                     filter_pattern: str = "", 
                     exclude_pattern: str = "") -> Dict[str, Any]:
        """Test discover_by_domain with various filters"""
        print(f"\n{'='*60}")
        print(f"Testing DISCOVER on: {name}")
        print(f"Domain: {domain}")
        if filter_pattern:
            print(f"Filter: {filter_pattern}")
        if exclude_pattern:
            print(f"Exclude: {exclude_pattern}")
        print("-"*60)
        
        operation = {
            "type": "discover",
            "name": name,
            "domain": domain,
            "filter": filter_pattern,
            "exclude": exclude_pattern,
            "timestamp": datetime.now().isoformat(),
            "status": "started"
        }
        
        # Trigger discovery
        result = self.crawler.discover_by_domain(
            domain_url=domain,
            filter=filter_pattern,
            exclude_filter=exclude_pattern
        )
        
        if "snapshot_id" in result:
            snapshot_id = result["snapshot_id"]
            operation["snapshot_id"] = snapshot_id
            print(f"✅ Snapshot ID: {snapshot_id}")
            
            # Poll for results (longer timeout for discover)
            print("Polling for discovery results (this may take time)...")
            data = self.crawler.poll_until_ready(snapshot_id, poll_interval=10, timeout=300)
            
            # Save raw data
            filename = f"discover_{name.replace(' ', '_').lower()}.json"
            filepath = self.save_json(data, filename, "discover")
            
            # Analyze results
            if isinstance(data, list):
                operation["status"] = "success"
                operation["records"] = len(data)
                operation["filepath"] = str(filepath)
                
                # Analyze discovered URLs
                url_analysis = self.analyze_urls(data, domain)
                operation["url_analysis"] = url_analysis
                
                # Analyze content
                content_analysis = self.analyze_content(data)
                operation["content_analysis"] = content_analysis
                
                print(f"✅ Discovered {len(data)} pages")
                print(f"   Saved to: {filepath}")
                self.print_url_analysis(url_analysis)
                self.print_analysis(content_analysis)
                
            else:
                operation["status"] = "error"
                operation["error"] = data
                print(f"❌ Error: {data}")
        else:
            operation["status"] = "failed"
            operation["error"] = result
            print(f"❌ Failed to get snapshot: {result}")
        
        self.operations_log.append(operation)
        return operation
    
    def test_batch_collect(self, urls: List[str], name: str) -> Dict[str, Any]:
        """Test collect_by_url with multiple URLs"""
        print(f"\n{'='*60}")
        print(f"Testing BATCH COLLECT: {name}")
        print(f"URLs: {len(urls)} pages")
        for url in urls[:3]:  # Show first 3
            print(f"  - {url}")
        if len(urls) > 3:
            print(f"  ... and {len(urls)-3} more")
        print("-"*60)
        
        operation = {
            "type": "batch_collect",
            "name": name,
            "urls": urls,
            "url_count": len(urls),
            "timestamp": datetime.now().isoformat(),
            "status": "started"
        }
        
        # Trigger batch collection
        result = self.crawler.collect_by_url(urls)
        
        if "snapshot_id" in result:
            snapshot_id = result["snapshot_id"]
            operation["snapshot_id"] = snapshot_id
            print(f"✅ Snapshot ID: {snapshot_id}")
            
            # Poll for results
            print("Polling for batch results...")
            data = self.crawler.poll_until_ready(snapshot_id, poll_interval=5, timeout=180)
            
            # Save raw data
            filename = f"batch_{name.replace(' ', '_').lower()}.json"
            filepath = self.save_json(data, filename, "batch")
            
            # Analyze results
            if isinstance(data, list):
                operation["status"] = "success"
                operation["records"] = len(data)
                operation["filepath"] = str(filepath)
                
                # Analyze content
                content_analysis = self.analyze_content(data)
                operation["analysis"] = content_analysis
                
                print(f"✅ Collected {len(data)} pages")
                print(f"   Saved to: {filepath}")
                self.print_analysis(content_analysis)
                
            else:
                operation["status"] = "error"
                operation["error"] = data
                print(f"❌ Error: {data}")
        else:
            operation["status"] = "failed"
            operation["error"] = result
            print(f"❌ Failed to get snapshot: {result}")
        
        self.operations_log.append(operation)
        return operation
    
    def analyze_content(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze content types and availability"""
        if not data:
            return {}
        
        analysis = {
            "total_pages": len(data),
            "formats_available": {
                "markdown": 0,
                "html2text": 0,
                "page_html": 0,
                "ld_json": 0,
                "page_title": 0
            },
            "content_sizes": {
                "markdown_avg": 0,
                "html_avg": 0,
                "text_avg": 0
            },
            "fields_present": set()
        }
        
        markdown_sizes = []
        html_sizes = []
        text_sizes = []
        
        for page in data:
            # Track which fields are present
            analysis["fields_present"].update(page.keys())
            
            # Count format availability
            if page.get("markdown"):
                analysis["formats_available"]["markdown"] += 1
                markdown_sizes.append(len(page["markdown"]))
            
            if page.get("html2text"):
                analysis["formats_available"]["html2text"] += 1
                text_sizes.append(len(page["html2text"]))
            
            if page.get("page_html"):
                analysis["formats_available"]["page_html"] += 1
                html_sizes.append(len(page["page_html"]))
            
            if page.get("ld_json"):
                analysis["formats_available"]["ld_json"] += 1
            
            if page.get("page_title"):
                analysis["formats_available"]["page_title"] += 1
        
        # Calculate averages
        if markdown_sizes:
            analysis["content_sizes"]["markdown_avg"] = sum(markdown_sizes) // len(markdown_sizes)
        if html_sizes:
            analysis["content_sizes"]["html_avg"] = sum(html_sizes) // len(html_sizes)
        if text_sizes:
            analysis["content_sizes"]["text_avg"] = sum(text_sizes) // len(text_sizes)
        
        analysis["fields_present"] = list(analysis["fields_present"])
        
        return analysis
    
    def analyze_urls(self, data: List[Dict], base_domain: str) -> Dict[str, Any]:
        """Analyze URL patterns in discovered data"""
        if not data:
            return {}
        
        urls = [page.get("url", "") for page in data]
        base = base_domain.replace("https://", "").replace("http://", "").rstrip("/")
        
        analysis = {
            "total_urls": len(urls),
            "internal_urls": [],
            "external_urls": [],
            "url_patterns": {},
            "depth_analysis": {}
        }
        
        for url in urls:
            if base in url:
                analysis["internal_urls"].append(url)
                
                # Analyze URL depth
                path = url.split(base)[-1]
                depth = path.count("/") - 1
                depth_key = f"depth_{depth}"
                analysis["depth_analysis"][depth_key] = analysis["depth_analysis"].get(depth_key, 0) + 1
                
                # Extract patterns
                if "/page" in url:
                    analysis["url_patterns"]["pagination"] = analysis["url_patterns"].get("pagination", 0) + 1
                if "/category" in url or "/catalogue" in url:
                    analysis["url_patterns"]["category"] = analysis["url_patterns"].get("category", 0) + 1
                if "/product" in url or "/item" in url:
                    analysis["url_patterns"]["product"] = analysis["url_patterns"].get("product", 0) + 1
            else:
                analysis["external_urls"].append(url)
        
        analysis["internal_count"] = len(analysis["internal_urls"])
        analysis["external_count"] = len(analysis["external_urls"])
        
        return analysis
    
    def print_analysis(self, analysis: Dict[str, Any]):
        """Print content analysis results"""
        if not analysis:
            return
        
        print("\n📊 Content Analysis:")
        print(f"   Total pages: {analysis.get('total_pages', 0)}")
        
        formats = analysis.get("formats_available", {})
        print(f"   Formats available:")
        for fmt, count in formats.items():
            if count > 0:
                print(f"     - {fmt}: {count} pages")
        
        sizes = analysis.get("content_sizes", {})
        if any(sizes.values()):
            print(f"   Average content sizes:")
            for fmt, size in sizes.items():
                if size > 0:
                    print(f"     - {fmt}: {size:,} chars")
    
    def print_url_analysis(self, analysis: Dict[str, Any]):
        """Print URL analysis results"""
        if not analysis:
            return
        
        print("\n🔗 URL Analysis:")
        print(f"   Total URLs: {analysis.get('total_urls', 0)}")
        print(f"   Internal: {analysis.get('internal_count', 0)}")
        print(f"   External: {analysis.get('external_count', 0)}")
        
        if analysis.get("url_patterns"):
            print(f"   URL patterns found:")
            for pattern, count in analysis["url_patterns"].items():
                print(f"     - {pattern}: {count}")
        
        if analysis.get("depth_analysis"):
            print(f"   URL depth distribution:")
            for depth, count in sorted(analysis["depth_analysis"].items()):
                print(f"     - {depth}: {count} pages")
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("\n" + "="*80)
        print("CRAWLER API DATA GATHERING")
        print(f"Output directory: {self.run_dir}")
        print("="*80)
        
        test_suite = [
            # Single page collections
            {
                "type": "collect_single",
                "name": "Simple HTML",
                "url": "https://example.com"
            },
            {
                "type": "collect_single", 
                "name": "HTTP Testing",
                "url": "https://httpbin.org"
            },
            {
                "type": "collect_single",
                "name": "JSON Placeholder",
                "url": "https://jsonplaceholder.typicode.com"
            },
            
            # Batch collections
            {
                "type": "batch_collect",
                "name": "Multiple HTTPBin Endpoints",
                "urls": [
                    "https://httpbin.org/",
                    "https://httpbin.org/forms/post",
                    "https://httpbin.org/html",
                    "https://httpbin.org/xml"
                ]
            },
            
            # Domain discoveries with filters
            {
                "type": "discover",
                "name": "Example.com Full",
                "domain": "https://example.com",
                "filter": "",
                "exclude": ""
            },
            {
                "type": "discover",
                "name": "HTTPBin Limited",
                "domain": "https://httpbin.org",
                "filter": "/forms/*",
                "exclude": ""
            }
        ]
        
        # Run each test
        for test in test_suite:
            try:
                if test["type"] == "collect_single":
                    self.test_collect_single(test["url"], test["name"])
                elif test["type"] == "batch_collect":
                    self.test_batch_collect(test["urls"], test["name"])
                elif test["type"] == "discover":
                    self.test_discover(
                        test["domain"], 
                        test["name"],
                        test.get("filter", ""),
                        test.get("exclude", "")
                    )
                
                # Small delay between operations
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error in test '{test['name']}': {e}")
                self.operations_log.append({
                    "name": test["name"],
                    "status": "exception",
                    "error": str(e)
                })
        
        # Save operations log
        log_path = self.save_json(self.operations_log, "operations_log.json")
        
        # Generate summary report
        self.generate_summary()
        
        print("\n" + "="*80)
        print("DATA GATHERING COMPLETE")
        print(f"Results saved to: {self.run_dir}")
        print(f"Operations log: {log_path}")
        print("="*80)
    
    def generate_summary(self):
        """Generate a summary report of all operations"""
        summary = {
            "run_timestamp": self.run_timestamp,
            "total_operations": len(self.operations_log),
            "successful": sum(1 for op in self.operations_log if op.get("status") == "success"),
            "failed": sum(1 for op in self.operations_log if op.get("status") in ["failed", "error", "exception"]),
            "total_pages_collected": sum(op.get("records", 0) for op in self.operations_log),
            "operations": self.operations_log
        }
        
        # Save summary
        summary_path = self.save_json(summary, "summary.json")
        
        print("\n📋 SUMMARY")
        print(f"   Total operations: {summary['total_operations']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Total pages collected: {summary['total_pages_collected']}")
        print(f"   Summary saved to: {summary_path}")


def main():
    """Run the data gathering process"""
    gatherer = CrawlerDataGatherer()
    
    # You can run all tests
    gatherer.run_all_tests()
    
    # Or run specific tests
    # gatherer.test_collect_single("https://example.com", "Example")
    # gatherer.test_discover("https://httpbin.org", "HTTPBin", filter="/forms/*")


if __name__ == "__main__":
    main()