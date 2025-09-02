# Crawler Testing Scripts

This folder contains all the test scripts for the Crawler API.

## Main Working Script
- **pure_crawler_api.py** - The core implementation that actually works (moved to root)

## Essential Testing Tools
- **save_crawler_result.py** - Polls a snapshot ID and saves the result
- **check_snapshot_status.py** - Just checks status without polling

## Quick Testing Scripts  
- **quick_param_tester.py** - Quickly test different params, saves to crawler_tests/
- **test_crawler_simple.py** - Simple test without polling

## Data Gathering Scripts (various approaches)
- **data_gatherer.py** - Comprehensive data gathering with analysis
- **quick_data_gatherer.py** - Quick version without waiting
- **comprehensive_data_gatherer.py** - Full parameter tracking version
- **simple_crawler_tester.py** - Simple one file per test

## Specific Test Scripts
- **test_crawl_real_site.py** - Tests on real sites
- **test_discover_and_save.py** - Tests discover operation
- **test_poll_snapshot.py** - Tests polling mechanism
- **test_quotes_site.py** - Tests on quotes.toscrape.com
- **trigger_httpbin_crawl.py** - Triggers httpbin tests
- **trigger_quotes_discover.py** - Triggers quotes site discover

## Usage

1. For quick testing with different parameters:
```bash
python quick_param_tester.py
```

2. To poll a snapshot and get data:
```bash
python save_crawler_result.py <snapshot_id>
```

3. To check status without polling:
```bash
python check_snapshot_status.py <snapshot_id>
```