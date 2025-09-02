#!/usr/bin/env python3
"""
comprehensive_data_gatherer.py - Comprehensive test with full parameter tracking

This saves:
1. The exact API parameters used
2. The raw API responses  
3. The processed data
4. Complete analysis
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from pure_crawler_api import PureCrawlerAPI

class ComprehensiveCrawlerTest:
    """Test crawler with complete parameter and response tracking"""
    
    def __init__(self, output_dir: str = "crawler_test_data"):
        self.crawler = PureCrawlerAPI()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(output_dir) / self.timestamp
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Master log of all operations
        self.master_log = []
        
    def save_operation(self, operation_name: str, data: Dict[str, Any]):
        """Save operation data with full details"""
        # Create operation directory
        op_dir = self.output_dir / operation_name
        op_dir.mkdir(exist_ok=True)
        
        # Save different aspects
        files_saved = {}
        
        # 1. API Parameters
        if "api_params" in data:
            filepath = op_dir / "api_params.json"
            with open(filepath, 'w') as f:
                json.dump(data["api_params"], f, indent=2)
            files_saved["api_params"] = str(filepath)
        
        # 2. API Response (snapshot info)
        if "api_response" in data:
            filepath = op_dir / "api_response.json"
            with open(filepath, 'w') as f:
                json.dump(data["api_response"], f, indent=2)
            files_saved["api_response"] = str(filepath)
        
        # 3. Crawled Data
        if "crawled_data" in data:
            filepath = op_dir / "crawled_data.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data["crawled_data"], f, indent=2, ensure_ascii=False)
            files_saved["crawled_data"] = str(filepath)
        
        # 4. Analysis
        if "analysis" in data:
            filepath = op_dir / "analysis.json"
            with open(filepath, 'w') as f:
                json.dump(data["analysis"], f, indent=2)
            files_saved["analysis"] = str(filepath)
        
        # 5. Complete record
        complete_record = {
            "operation_name": operation_name,
            "timestamp": datetime.now().isoformat(),
            "files": files_saved,
            **data
        }
        
        filepath = op_dir / "complete_record.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(complete_record, f, indent=2, ensure_ascii=False)
        
        return files_saved
    
    def test_collect_single(self, name: str, url: str, **kwargs):
        """Test single URL collection with full parameter tracking"""
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print(f"Type: COLLECT (single URL)")
        print(f"URL: {url}")
        print("-"*60)
        
        # Prepare API parameters
        api_params = {
            "operation": "collect_by_url",
            "dataset_id": self.crawler.DATASET_ID,
            "endpoint": f"{self.crawler.BASE_URL}/trigger",
            "headers": {
                "Authorization": "Bearer <token>",  # Masked for security
                "Content-Type": "application/json"
            },
            "params": {
                "dataset_id": self.crawler.DATASET_ID,
                "include_errors": "true"
            },
            "data": [{"url": url}],
            "custom_params": kwargs
        }
        
        operation_data = {
            "test_name": name,
            "test_type": "collect_single",
            "url": url,
            "api_params": api_params,
            "start_time": datetime.now().isoformat()
        }
        
        # Make API call
        result = self.crawler.collect_by_url([url])
        operation_data["api_response"] = result
        
        if "snapshot_id" in result:
            snapshot_id = result["snapshot_id"]
            print(f"✅ Snapshot ID: {snapshot_id}")
            
            # Poll for data
            print("Polling for results...")
            data = self.crawler.poll_until_ready(snapshot_id, poll_interval=5, timeout=120)
            operation_data["crawled_data"] = data
            
            # Analyze
            if isinstance(data, list):
                analysis = self.analyze_data(data)
                operation_data["analysis"] = analysis
                
                print(f"✅ Success! Got {len(data)} page(s)")
                print(f"   Formats available: {', '.join(analysis['formats_found'])}")
        else:
            operation_data["error"] = result
            print(f"❌ Failed: {result}")
        
        operation_data["end_time"] = datetime.now().isoformat()
        
        # Save everything
        files = self.save_operation(f"collect_{name.lower().replace(' ', '_')}", operation_data)
        print(f"📁 Saved to: {self.output_dir / f'collect_{name.lower().replace(' ', '_')}'}")
        
        # Add to master log
        self.master_log.append({
            "name": name,
            "type": "collect_single",
            "snapshot_id": result.get("snapshot_id"),
            "status": "success" if "snapshot_id" in result else "failed",
            "files": files
        })
        
        return operation_data
    
    def test_discover(self, name: str, domain: str, filter_pattern: str = "", 
                     exclude_pattern: str = "", **kwargs):
        """Test domain discovery with full parameter tracking"""
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print(f"Type: DISCOVER")
        print(f"Domain: {domain}")
        if filter_pattern:
            print(f"Filter: {filter_pattern}")
        if exclude_pattern:
            print(f"Exclude: {exclude_pattern}")
        print("-"*60)
        
        # Prepare API parameters
        api_params = {
            "operation": "discover_by_domain",
            "dataset_id": self.crawler.DATASET_ID,
            "endpoint": f"{self.crawler.BASE_URL}/trigger",
            "headers": {
                "Authorization": "Bearer <token>",
                "Content-Type": "application/json"
            },
            "params": {
                "dataset_id": self.crawler.DATASET_ID,
                "include_errors": "true",
                "type": "discover_new",
                "discover_by": "domain_url"
            },
            "data": [{
                "url": domain,
                "filter": filter_pattern,
                "exclude_filter": exclude_pattern
            }],
            "custom_params": kwargs
        }
        
        operation_data = {
            "test_name": name,
            "test_type": "discover",
            "domain": domain,
            "filter": filter_pattern,
            "exclude": exclude_pattern,
            "api_params": api_params,
            "start_time": datetime.now().isoformat()
        }
        
        # Make API call
        result = self.crawler.discover_by_domain(domain, filter_pattern, exclude_pattern)
        operation_data["api_response"] = result
        
        if "snapshot_id" in result:
            snapshot_id = result["snapshot_id"]
            print(f"✅ Snapshot ID: {snapshot_id}")
            
            # Poll for data (longer timeout for discover)
            print("Polling for discovery results...")
            data = self.crawler.poll_until_ready(snapshot_id, poll_interval=10, timeout=180)
            operation_data["crawled_data"] = data
            
            # Analyze
            if isinstance(data, list):
                analysis = self.analyze_discovery(data, domain)
                operation_data["analysis"] = analysis
                
                print(f"✅ Success! Discovered {len(data)} page(s)")
                print(f"   Internal URLs: {analysis['internal_count']}")
                print(f"   External URLs: {analysis['external_count']}")
        else:
            operation_data["error"] = result
            print(f"❌ Failed: {result}")
        
        operation_data["end_time"] = datetime.now().isoformat()
        
        # Save everything
        files = self.save_operation(f"discover_{name.lower().replace(' ', '_')}", operation_data)
        print(f"📁 Saved to: {self.output_dir / f'discover_{name.lower().replace(' ', '_')}'}")
        
        # Add to master log
        self.master_log.append({
            "name": name,
            "type": "discover",
            "snapshot_id": result.get("snapshot_id"),
            "status": "success" if "snapshot_id" in result else "failed",
            "files": files
        })
        
        return operation_data
    
    def test_batch_collect(self, name: str, urls: List[str], **kwargs):
        """Test batch URL collection with full parameter tracking"""
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print(f"Type: BATCH COLLECT")
        print(f"URLs: {len(urls)} pages")
        for url in urls[:3]:
            print(f"  - {url}")
        if len(urls) > 3:
            print(f"  ... and {len(urls)-3} more")
        print("-"*60)
        
        # Prepare API parameters
        api_params = {
            "operation": "collect_by_url_batch",
            "dataset_id": self.crawler.DATASET_ID,
            "endpoint": f"{self.crawler.BASE_URL}/trigger",
            "headers": {
                "Authorization": "Bearer <token>",
                "Content-Type": "application/json"
            },
            "params": {
                "dataset_id": self.crawler.DATASET_ID,
                "include_errors": "true"
            },
            "data": [{"url": url} for url in urls],
            "url_count": len(urls),
            "custom_params": kwargs
        }
        
        operation_data = {
            "test_name": name,
            "test_type": "batch_collect",
            "urls": urls,
            "url_count": len(urls),
            "api_params": api_params,
            "start_time": datetime.now().isoformat()
        }
        
        # Make API call
        result = self.crawler.collect_by_url(urls)
        operation_data["api_response"] = result
        
        if "snapshot_id" in result:
            snapshot_id = result["snapshot_id"]
            print(f"✅ Snapshot ID: {snapshot_id}")
            
            # Poll for data
            print("Polling for batch results...")
            data = self.crawler.poll_until_ready(snapshot_id, poll_interval=5, timeout=180)
            operation_data["crawled_data"] = data
            
            # Analyze
            if isinstance(data, list):
                analysis = self.analyze_batch(data, urls)
                operation_data["analysis"] = analysis
                
                print(f"✅ Success! Got {len(data)} page(s)")
                print(f"   Success rate: {analysis['success_rate']:.1f}%")
        else:
            operation_data["error"] = result
            print(f"❌ Failed: {result}")
        
        operation_data["end_time"] = datetime.now().isoformat()
        
        # Save everything
        files = self.save_operation(f"batch_{name.lower().replace(' ', '_')}", operation_data)
        print(f"📁 Saved to: {self.output_dir / f'batch_{name.lower().replace(' ', '_')}'}")
        
        # Add to master log
        self.master_log.append({
            "name": name,
            "type": "batch_collect",
            "snapshot_id": result.get("snapshot_id"),
            "status": "success" if "snapshot_id" in result else "failed",
            "files": files
        })
        
        return operation_data
    
    def analyze_data(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze crawled data"""
        analysis = {
            "total_pages": len(data),
            "formats_found": [],
            "content_sizes": {},
            "has_markdown": 0,
            "has_html": 0,
            "has_text": 0,
            "has_json_ld": 0,
            "has_title": 0
        }
        
        for page in data:
            if page.get("markdown"):
                analysis["has_markdown"] += 1
                if "markdown" not in analysis["formats_found"]:
                    analysis["formats_found"].append("markdown")
            
            if page.get("page_html"):
                analysis["has_html"] += 1
                if "html" not in analysis["formats_found"]:
                    analysis["formats_found"].append("html")
                analysis["content_sizes"][page.get("url", "unknown")] = len(page["page_html"])
            
            if page.get("html2text"):
                analysis["has_text"] += 1
                if "text" not in analysis["formats_found"]:
                    analysis["formats_found"].append("text")
            
            if page.get("ld_json"):
                analysis["has_json_ld"] += 1
                if "json-ld" not in analysis["formats_found"]:
                    analysis["formats_found"].append("json-ld")
            
            if page.get("page_title"):
                analysis["has_title"] += 1
        
        return analysis
    
    def analyze_discovery(self, data: List[Dict], base_domain: str) -> Dict[str, Any]:
        """Analyze discovery results"""
        analysis = self.analyze_data(data)
        
        # Add discovery-specific analysis
        urls = [page.get("url", "") for page in data]
        base = base_domain.replace("https://", "").replace("http://", "").rstrip("/")
        
        internal_urls = [u for u in urls if base in u]
        external_urls = [u for u in urls if base not in u]
        
        analysis.update({
            "internal_urls": internal_urls,
            "external_urls": external_urls,
            "internal_count": len(internal_urls),
            "external_count": len(external_urls),
            "crawl_depth": self.calculate_depth(internal_urls, base)
        })
        
        return analysis
    
    def analyze_batch(self, data: List[Dict], requested_urls: List[str]) -> Dict[str, Any]:
        """Analyze batch collection results"""
        analysis = self.analyze_data(data)
        
        # Check which URLs were successfully collected
        collected_urls = [page.get("url", "") for page in data]
        analysis["requested_count"] = len(requested_urls)
        analysis["collected_count"] = len(collected_urls)
        analysis["success_rate"] = (len(collected_urls) / len(requested_urls)) * 100 if requested_urls else 0
        analysis["missing_urls"] = [u for u in requested_urls if u not in collected_urls]
        
        return analysis
    
    def calculate_depth(self, urls: List[str], base_domain: str) -> Dict[str, int]:
        """Calculate URL depth distribution"""
        depth_counts = {}
        for url in urls:
            if base_domain in url:
                path = url.split(base_domain)[-1]
                depth = path.count("/") - 1 if path else 0
                depth_key = f"depth_{depth}"
                depth_counts[depth_key] = depth_counts.get(depth_key, 0) + 1
        return depth_counts
    
    def run_test_suite(self):
        """Run comprehensive test suite"""
        print("\n" + "="*80)
        print("COMPREHENSIVE CRAWLER API TEST SUITE")
        print(f"Output: {self.output_dir}")
        print("="*80)
        
        tests = [
            # Single page collections with different content types
            {"type": "collect_single", "name": "Simple HTML", "url": "https://example.com"},
            {"type": "collect_single", "name": "API Docs", "url": "https://httpbin.org"},
            
            # Batch collections
            {"type": "batch", "name": "HTTPBin Pages", "urls": [
                "https://httpbin.org/",
                "https://httpbin.org/html",
                "https://httpbin.org/xml",
                "https://httpbin.org/forms/post"
            ]},
            
            # Discovery with filters
            {"type": "discover", "name": "Example Full", "domain": "https://example.com"},
            {"type": "discover", "name": "HTTPBin Forms", "domain": "https://httpbin.org", 
             "filter": "/forms/*", "exclude": ""},
        ]
        
        for test in tests:
            try:
                if test["type"] == "collect_single":
                    self.test_collect_single(test["name"], test["url"])
                elif test["type"] == "batch":
                    self.test_batch_collect(test["name"], test["urls"])
                elif test["type"] == "discover":
                    self.test_discover(
                        test["name"], 
                        test["domain"],
                        test.get("filter", ""),
                        test.get("exclude", "")
                    )
                
                time.sleep(2)  # Brief pause between tests
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
                self.master_log.append({
                    "name": test["name"],
                    "type": test["type"],
                    "status": "exception",
                    "error": str(e)
                })
        
        # Save master log
        master_log_path = self.output_dir / "master_log.json"
        with open(master_log_path, 'w') as f:
            json.dump(self.master_log, f, indent=2)
        
        # Generate summary
        self.generate_summary()
        
        print("\n" + "="*80)
        print("TEST SUITE COMPLETE")
        print(f"Results saved to: {self.output_dir}")
        print(f"Master log: {master_log_path}")
        print("="*80)
    
    def generate_summary(self):
        """Generate test summary"""
        summary = {
            "test_run": self.timestamp,
            "output_directory": str(self.output_dir),
            "total_tests": len(self.master_log),
            "successful": sum(1 for t in self.master_log if t.get("status") == "success"),
            "failed": sum(1 for t in self.master_log if t.get("status") in ["failed", "exception"]),
            "tests": self.master_log
        }
        
        summary_path = self.output_dir / "test_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📊 SUMMARY")
        print(f"   Total tests: {summary['total_tests']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Summary saved: {summary_path}")


def main():
    tester = ComprehensiveCrawlerTest()
    tester.run_test_suite()


if __name__ == "__main__":
    main()