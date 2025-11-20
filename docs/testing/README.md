# Testing Documentation

Test reports, test results, and testing guides.

---

## Latest Test Reports

### Application Test Report (2025-11-20)

**`APPLICATION_TEST_REPORT.md`**
- **Date**: 2025-11-20
- **Status**: ✅ ALL TESTS PASSED
- **Success Rate**: 100% (8/8 tests)
- **Duration**: ~15 minutes

#### Tests Performed:
1. ✅ API Keys Management
2. ✅ Database Schema Verification
3. ✅ Ollama Model Pull Endpoint
4. ✅ MASTER_ENCRYPTION_KEY Configuration
5. ✅ API Key Encryption
6. ✅ Save New API Key
7. ✅ End-to-End RAG Query
8. ✅ Ollama Models Availability

#### Fixes Verified:
- Fix #1: Ollama Model Pull (HTTP 422) ✅
- Fix #2: MASTER_ENCRYPTION_KEY Configuration ✅
- Fix #3: Database Schema ✅
- Fix #4: Fallback Logic ✅

---

## Historical Test Reports

For older test reports, see root-level:
- `TESTING_GUIDE.md` - General testing guide
- `TEST_RESULTS_SUMMARY.md` - Test results
- `WEB_SCRAPER_TEST_REPORT.md` - Web scraper tests
- `WEB_SCRAPER_TEST_RESULTS.md` - Scraper results
- `OLLAMA_MANAGEMENT_TESTING_REPORT.md` - Ollama tests
- `SCRIPTS_VALIDATION_SUMMARY.md` - Scripts validation

---

## Testing Guidelines

### Running Tests

#### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

#### Frontend Tests
```bash
cd frontend
npm test
```

#### Integration Tests
```bash
./scripts/testing/test-integration.sh
```

### Test Coverage
- Minimum: 80%
- Critical paths: 100%

---

## Service Health Checks

All services verified as healthy (2025-11-20):
- Backend (rag-backend)
- Frontend (rag-frontend)
- PostgreSQL (rag-postgres)
- Redis (rag-redis)
- Ollama (rag-ollama)
- MinIO (rag-minio)
- Grafana, Prefect, etc.

---

## Quick Links

- [Latest Test Report](./APPLICATION_TEST_REPORT.md)
- [Fixes Documentation](../fixes/)
- [Testing Scripts](../../scripts/testing/README.md)
- [Back to Documentation Index](../DOCUMENTATION_INDEX.md)

---

**Last Updated**: 2025-11-20
