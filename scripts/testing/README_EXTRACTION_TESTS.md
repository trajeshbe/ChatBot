# Extraction Features Test Suite

## Overview

Comprehensive automated testing suite for all extraction features including Smart Extraction, AI Navigation, Template operations, and backend health checks.

## Quick Start

```bash
# Run all tests
./scripts/testing/test-extraction-features.sh

# Run specific test (e.g., Test 1 only)
./scripts/testing/test-extraction-features.sh 1

# Run multiple tests (e.g., Tests 1, 3, and 5)
./scripts/testing/test-extraction-features.sh 1,3,5
```

## Prerequisites

1. **Backend Running**: Services must be running at `localhost:8000`
   ```bash
   docker-compose up -d backend frontend
   ```

2. **OpenAI API Key**: Required for AI-powered tests
   - Ensure `OPENAI_API_KEY` is set in `.env` file

3. **Dependencies**:
   - `jq` - JSON processor (install: `sudo apt-get install jq`)
   - `curl` - HTTP client (usually pre-installed)

## Test Suite

### Test 1: Smart Extraction - Mystery Books
**What it tests**: Basic AI-powered data extraction from a category page

- **URL**: https://books.toscrape.com/catalogue/category/books/mystery_3/index.html
- **Expected**: Extract ~20 mystery books with title, price, and availability
- **Duration**: ~20-40 seconds
- **Validates**:
  - Smart Extraction API functionality
  - Playwright + OpenAI integration
  - Structured data extraction

### Test 2: AI-Powered Navigation
**What it tests**: Ability to navigate through website to reach target content

- **Starting URL**: https://books.toscrape.com/ (homepage)
- **Instructions**: "Navigate to the Fantasy category and extract all fantasy books"
- **Expected**: AI navigates to Fantasy category, extracts ~19 books
- **Duration**: ~60-90 seconds
- **Validates**:
  - AI navigation capabilities
  - Multi-step workflow execution
  - Navigation path tracking

### Test 3: Single Book Page Extraction
**What it tests**: Extraction from individual product pages

- **URL**: https://books.toscrape.com/catalogue/sharp-objects_997/index.html
- **Expected**: Extract title, price, availability, description, UPC
- **Duration**: ~15-25 seconds
- **Validates**:
  - Detail page extraction
  - Multiple field types
  - Field identification accuracy

### Test 4: Template Listing
**What it tests**: Template storage and retrieval

- **Endpoint**: `GET /api/v1/extract/templates`
- **Expected**: List all saved extraction templates
- **Duration**: <1 second
- **Validates**:
  - Template storage functionality
  - Template metadata retrieval
  - Database connectivity

### Test 5: Backend Health Check
**What it tests**: Backend service health and feature flags

- **Endpoint**: `GET /health`
- **Expected**: Healthy status with feature flags
- **Duration**: <1 second
- **Validates**:
  - Backend availability
  - Feature configuration
  - Service health

## Output

### Console Output
Tests provide real-time feedback with color-coded results:
- 🔵 **Blue**: Informational messages
- ✅ **Green**: Success messages
- ❌ **Red**: Error messages
- ⚠️  **Yellow**: Warning messages

### Results Files
All test results are saved to timestamped directory:
```
/tmp/extraction_tests_YYYYMMDD_HHMMSS/
├── test1_smart_extraction.json
├── test2_ai_navigation.json
├── test3_single_book.json
├── test4_templates.json
└── test5_health.json
```

### Summary Report
After all tests complete, you'll see:
```
============================================================================
TEST SUMMARY
============================================================================
Total Tests:  5
Passed:       5
Failed:       0

All results saved to: /tmp/extraction_tests_20251119_184500
```

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed

## Usage Examples

### Run full test suite
```bash
./scripts/testing/test-extraction-features.sh
```

### Run only quick tests (Tests 1, 3, 4, 5 - skip AI navigation)
```bash
./scripts/testing/test-extraction-features.sh 1,3,4,5
```

### Run only critical tests (Smart Extraction + Health)
```bash
./scripts/testing/test-extraction-features.sh 1,5
```

### Custom API URL
```bash
API_URL=http://backend:8000 ./scripts/testing/test-extraction-features.sh
```

## Troubleshooting

### "Backend not responding"
- Check if backend is running: `docker-compose ps backend`
- Check backend logs: `docker-compose logs backend | tail -50`
- Restart backend: `docker-compose restart backend`

### "jq not found"
```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq
```

### Tests timing out
- AI navigation test can take up to 90 seconds
- Check OpenAI API rate limits
- Verify network connectivity to test URLs

### Extraction failures
- Ensure OpenAI API key is valid and has credits
- Check if test website (books.toscrape.com) is accessible
- Review detailed error in result JSON files

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Test Extraction Features
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: docker-compose up -d
      - name: Run extraction tests
        run: ./scripts/testing/test-extraction-features.sh
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Manual UI Testing

For comprehensive UI testing, refer to:
- `/tmp/MANUAL_UI_TEST_GUIDE.md` - Detailed manual test procedures
- `/tmp/API_TEST_RESULTS_2025-11-19.md` - Latest automated test results

## Extending the Test Suite

To add new tests, edit `test-extraction-features.sh`:

1. Create new test function:
```bash
test_my_new_feature() {
    print_header "TEST 6: My New Feature"

    # Your test logic here

    record_test_result "My Feature" "PASS" "Feature works"
}
```

2. Add to test runner:
```bash
run_tests() {
    # ... existing code ...
    test_my_new_feature
}
```

## Support

For issues or questions:
- Check backend logs: `docker-compose logs backend`
- Review test result JSON files in `/tmp/extraction_tests_*`
- Consult main documentation: `docs/guides/WEB_SCRAPER_ENHANCED_GUIDE.md`
