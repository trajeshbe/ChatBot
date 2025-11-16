# Scripts Directory

Utility scripts organized by category for development, testing, debugging, and maintenance.

## 📁 Directory Structure

### [setup/](./setup/)
Scripts for initial setup and configuration.
- Database initialization
- Service configuration
- LLM model setup

### [testing/](./testing/)
Test scripts for integration, end-to-end, and validation testing.
- API testing
- RAG pipeline testing
- LLM integration testing
- Performance testing

### [debugging/](./debugging/)
Diagnostic and debugging scripts.
- Service health checks
- Log analysis
- Error diagnostics
- Database debugging

### [maintenance/](./maintenance/)
Maintenance and operational scripts.
- Service validation
- Health monitoring
- System verification

### [archive/](./archive/)
Deprecated and historical scripts (kept for reference).

---

## 🚀 Quick Reference

### First Time Setup
```bash
# 1. Setup database
./setup/setup-database.sh

# 2. Start services
./setup/start-services.sh

# 3. Validate everything works
./maintenance/validate-services.sh
```

### Testing
```bash
# Run integration tests
./testing/test-integration.sh

# Test document upload
./testing/test-upload-endpoint.sh

# Test RAG pipeline
./testing/test_rag_validation.py
```

### Debugging
```bash
# Diagnose backend issues
./debugging/diagnose-backend.sh

# Check document processing
./debugging/diagnose-documents.sh

# Debug RAG queries
./debugging/debug-rag.sh
```

### Maintenance
```bash
# Validate all services
./maintenance/validate-services.sh

# Verify complete setup
./maintenance/verify-complete-setup.sh

# Monitor uploads in real-time
./maintenance/watch-upload-realtime.sh
```

---

## 📝 Script Naming Conventions

- **setup-*.sh**: Setup and initialization scripts
- **test-*.sh / test_*.py**: Test scripts
- **diagnose-*.sh**: Diagnostic scripts
- **debug-*.sh / debug_*.py**: Debugging scripts
- **check-*.sh / check_*.py**: Status check scripts
- **validate-*.sh**: Validation scripts
- **verify-*.sh**: Verification scripts

---

## 🔗 Related Documentation

- **Setup Guides**: [../docs/setup/](../docs/setup/)
- **Debugging Guides**: [../docs/debugging/](../docs/debugging/)
- **Main Documentation**: [../README.md](../README.md)

---

**Last Updated**: 2025-11-16
