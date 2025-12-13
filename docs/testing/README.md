# Testing Documentation

This directory contains all test reports, test summaries, and testing-related documentation.

## Test Reports (2025-12-12)

### Comprehensive Test Reports
- **[COMPREHENSIVE_TEST_REPORT_2025-12-12.md](COMPREHENSIVE_TEST_REPORT_2025-12-12.md)** - Full system validation (88% pass rate)
  - Backend unit tests
  - API endpoint tests
  - Agent task tests
  - MinIO integration tests
  - Test infrastructure analysis

- **[FINAL_COMPREHENSIVE_CHAT_TEST_REPORT_2025-12-12.md](FINAL_COMPREHENSIVE_CHAT_TEST_REPORT_2025-12-12.md)** - End-to-end chat functionality testing
  - Direct LLM queries
  - Document processing
  - RAG queries
  - Context & memory tests
  - Edge cases & error handling

### Agent Testing
- **[TESTING_AGENT_FIXES.md](TESTING_AGENT_FIXES.md)** - Agent fixes validation
- **[TESTING_COMPLETE_SUMMARY.md](TESTING_COMPLETE_SUMMARY.md)** - Complete test summary

## Running Tests

### Backend Tests
```bash
# Run all backend tests
docker-compose exec backend pytest tests/ -v

# Run specific test file
docker-compose exec backend pytest tests/test_tool_registry.py -v

# Run with coverage
docker-compose exec backend pytest tests/ -v --cov=app --cov-report=html
```

### Integration Tests
```bash
# Comprehensive chat test
python3 comprehensive_chat_test.py

# Upload and RAG pipeline test
./scripts/testing/test-integration.sh
```

## Test Coverage

Current test coverage (2025-12-12):
- **Backend Unit Tests**: 79% (11/14 passed)
- **API Endpoints**: 100% (5/5 passed)
- **Agent Tasks**: 100% (3/3 passed)
- **MinIO Integration**: 100% (2/2 passed)
- **Overall**: 88% (21/24 passed)

## Related Documentation

- [Debugging Guide](../debugging/DEBUG_QUICK_REFERENCE.md)
- [RAG Debugging](../debugging/RAG_DEBUGGING_GUIDE.md)
- [Evaluation Guide](../evaluation/EVALUATION_GUIDE.md)

---

**Last Updated**: 2025-12-12
