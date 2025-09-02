# Crawler API Discovery Tests

## Overview
These tests validate the `discover_by_domain` functionality for crawling entire domains. Each test is in its own file for easier individual execution.

**Note:** Discovery operations can take 5-10+ minutes as they crawl entire domains. Consider using smaller test domains (like example.com) for faster results.

## Individual Test Files

### Basic Tests
- `test_02_01_discover_basic.py` - Basic domain discovery with defaults
- `test_02_02_discover_depth_0.py` - Single page only (depth=0)
- `test_02_03_discover_depth_1.py` - Page + direct links (depth=1)
- `test_02_04_discover_depth_2.py` - Two levels deep (depth=2)

### Filter Tests
- `test_02_05_discover_filter.py` - Filter pattern only
- `test_02_06_discover_filter_depth.py` - Filter + depth combined
- `test_02_07_discover_exclude.py` - Exclude pattern
- `test_02_08_discover_all_params.py` - All parameters combined

### Special Tests
- `test_02_09_discover_ignore_sitemap.py` - Ignore sitemap.xml
- `test_02_10_discover_convenience.py` - crawl_domain() convenience function

## Running Individual Tests

```bash
# Run a specific test
python -m smoke_tests.crawler_api.test_02_01_discover_basic

# Run with custom timeout (if needed)
timeout 10m python -m smoke_tests.crawler_api.test_02_04_discover_depth_2
```

## Running All Discovery Tests

```bash
# Run all discovery tests (original combined file)
python -m smoke_tests.crawler_api.test_02_discover_by_domain
```

## Test Domains

- **example.com** - Small, simple site (good for quick tests)
- **httpbin.org** - More complex, many endpoints (slower)

## Expected Timings

| Test | Domain | Expected Time |
|------|--------|--------------|
| depth=0 | example.com | 1-2 minutes |
| depth=1 | example.com | 2-5 minutes |
| depth=2 | example.com | 5-10 minutes |
| depth=1 | httpbin.org | 5-10 minutes |
| with filters | any | Similar or faster |

## Troubleshooting

If tests timeout:
1. Increase timeout values in the test files
2. Use simpler test domains
3. Run tests individually instead of all at once
4. Check BrightData API status