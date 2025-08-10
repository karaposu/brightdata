# BrightData SDK Smoke Tests

Comprehensive test suite for the BrightData Python SDK, organized by component with progressive complexity.

## Structure

```
smoke_tests/
├── web_unlocker/           # Web Unlocker API tests
│   ├── test_0_imports_and_init.py    # Import validation and initialization
│   ├── test_1_basic_operations.py    # Basic fetching and error handling
│   └── test_2_advanced_features.py   # Async, concurrent, and stress tests
│
├── browserapi/             # Browser API tests
│   ├── test_0_imports_and_init.py    # Import validation and strategies
│   ├── test_1_basic_operations.py    # Basic operations and configurations
│   └── test_2_advanced_features.py   # Pool management and performance
│
└── specialized_scraper/    # Scraper-specific tests
    ├── test_0_imports_and_init.py    # Registry and scraper discovery
    ├── test_1_basic_operations.py    # URL routing and basic scraping
    └── test_2_advanced_features.py   # Batch operations and fallbacks
```

## Running Tests

### Prerequisites

1. Copy `.env.example` to `.env` in the project root:
```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:
```bash
# Main BrightData API Token (required for specialized scrapers)
BRIGHTDATA_TOKEN=your_token_here

# Web Unlocker Configuration (required for Web Unlocker)
BRIGHTDATA_WEBUNLOCKER_BEARER=your_bearer_here
BRIGHTDATA_WEBUNLOCKER_APP_ZONE_STRING=your_zone_here
```

Note: The `.env` file should be in the project root directory (same level as `setup.py`), not in the smoke_tests directory.

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Run Individual Test Suites

```bash
# Web Unlocker tests
python smoke_tests/web_unlocker/test_0_imports_and_init.py
python smoke_tests/web_unlocker/test_1_basic_operations.py
python smoke_tests/web_unlocker/test_2_advanced_features.py

# Browser API tests
python smoke_tests/browserapi/test_0_imports_and_init.py
python smoke_tests/browserapi/test_1_basic_operations.py
python smoke_tests/browserapi/test_2_advanced_features.py

# Specialized Scraper tests
python smoke_tests/specialized_scraper/test_0_imports_and_init.py
python smoke_tests/specialized_scraper/test_1_basic_operations.py
python smoke_tests/specialized_scraper/test_2_advanced_features.py
```

### Run All Tests

```bash
# Create a test runner script
python -m smoke_tests.run_all
```

## Test Categories

### Level 0: Imports and Initialization (10 tests each)
- Import validation
- Dependency checking
- Class initialization
- Configuration options
- Default values
- Method availability

### Level 1: Basic Operations (10 tests each)
- Simple synchronous operations
- Error handling
- Result validation
- Parameter testing
- Basic async operations
- Cost tracking

### Level 2: Advanced Features (10 tests each)
- Concurrent operations
- Performance testing
- Stress testing
- Edge cases
- Memory efficiency
- Complex scenarios

## Test Coverage

### Web Unlocker
- ✅ Environment configuration
- ✅ Sync/Async operations
- ✅ Error handling
- ✅ File downloads
- ✅ Cost calculation
- ✅ Concurrent requests
- ✅ Timeout handling
- ✅ Special characters
- ✅ Large content
- ✅ Stress testing

### Browser API
- ✅ Strategy patterns (noop, semaphore, pool)
- ✅ Window sizing
- ✅ Wait options
- ✅ Headless/Headed modes
- ✅ Cost tracking
- ✅ Domain extraction
- ✅ Concurrent limiting
- ✅ Pool management
- ✅ Resource blocking
- ✅ Session reuse

### Specialized Scrapers
- ✅ Auto-detection
- ✅ Registry system
- ✅ URL classification
- ✅ Fallback mechanisms
- ✅ Batch operations
- ✅ Discovery endpoints
- ✅ Multi-bucket support
- ✅ Async polling
- ✅ Cost aggregation
- ✅ Performance optimization

## Expected Results

Each test file outputs:
- Individual test results with ✓/✗ indicators
- Detailed error messages for failures
- Performance metrics where applicable
- Summary statistics

Example output:
```
============================================================
Web Unlocker - Test Suite 0: Imports and Initialization
============================================================

[Test 01] Importing BrightdataWebUnlocker...
✓ Successfully imported BrightdataWebUnlocker

[Test 02] Checking dependencies...
✓ requests (HTTP requests) is available
✓ aiohttp (Async HTTP) is available
...

============================================================
Summary: 10 passed, 0 failed out of 10 tests
============================================================
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the package is installed correctly
2. **Environment Variables**: Check `.env` file and variable names
3. **Network Issues**: Some tests require internet connectivity
4. **API Limits**: Be aware of rate limits when running stress tests
5. **Async Errors**: Ensure Python 3.7+ for proper async support

### Debug Mode

Set environment variable for verbose output:
```bash
export BRIGHTDATA_DEBUG=1
```

## Contributing

When adding new tests:
1. Follow the naming convention: `test_XX_description()`
2. Include clear test descriptions
3. Return `True` for pass, `False` for fail
4. Handle exceptions gracefully
5. Add performance metrics where relevant