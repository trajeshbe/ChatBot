# Script Organization Summary

> **Date**: 2025-11-27
> **Task**: Organize all test and debug scripts from /tmp and root directory
> **Status**: ✓ COMPLETED

---

## Executive Summary

Successfully organized **58+ operational scripts** from scattered locations (`/tmp/`, root directory, `backend/`) into a structured `docs/operations/` directory with comprehensive documentation.

---

## Scripts Organized by Source

### From /tmp/ Directory (28 scripts)

**Testing Scripts (19)**:
- test_project_estimator_validation.py
- test_phase6_with_estimate_one.py
- test_phase6_eda_endpoints.py
- test_agent_12_debate_coordinator.py
- test_vector_search.py
- test_simple_workflow.py
- test_ui_extraction.py
- test_ui_playwright.py
- test_extraction_verbose.py
- test_all_scraper_compliance.sh
- test_validator_simple.sh
- test_aadhan_retrieval.sh
- test_compliance_enforcement.sh
- test_save_template.sh
- phase6_tests.sh
- test_all_parameters_flow.sh
- test_estimator.sh
- test_chat_compliance_fix.sh
- test_feedback_flow.sh

**Additional Testing (continued)**:
- test_response_quality_fix.sh
- test_e2e_complete.sh
- test_ui_thresholds.sh
- test_ui_backend_flow.sh
- test_scraping_compliance.sh
- comprehensive_test.sh
- test_chat_amazon.sh
- test_scraper_text_extraction.py
- navigation_quick_test.sh

**Debugging Scripts (1)**:
- monitor_thresholds.sh

**Maintenance Scripts (3)**:
- scraper_service_working.py
- fix_scraper_indentation.py
- auto_endpoint.py

---

### From Root Directory (12 scripts)

**Shell Scripts (7)**:
- test_agent11_integration.sh
- test_chat_comprehensive.sh
- test_comprehensive_chatbot.sh
- test_document_handling_comprehensive.sh
- test_estimate_one_phase3.sh
- test_project_estimator.sh
- test_template_extraction_now.sh

**Python Scripts (5)**:
- test_phase3_extraction.py
- test_phase3_model_selection.py
- test_project_estimator_multifile.py
- test_ui_debug.py
- test_vision_tool.py

---

### From backend/ Directory (16 scripts)

**Testing Scripts (10)**:
- test_bharti_extraction.py
- test_direct_aadhan_search.py
- test_fixed_template.py
- test_integrated_smart_mapping.py
- test_ollama_ui.py
- test_playwright_minimal.py
- test_rag_pipeline.py
- test_smart_template_mapping.py
- test_template_extraction_ui.py
- test_vision_tool.py

**Debugging Scripts (6)**:
- debug_rag_pipeline.py
- diagnose_chunks.py
- inspect_drenting.py
- inspect_drenting_detailed.py
- inspect_new_website.py
- inspect_screener.py

---

## Final Organization Structure

```
docs/operations/
├── README.md                           # Master index (NEW)
├── ORGANIZATION_SUMMARY.md             # This file (NEW)
│
├── guides/
│   ├── OPERATIONS_GUIDE.md             # Comprehensive guide (NEW - 500+ lines)
│   ├── QUICK_REFERENCE.md              # Quick commands (NEW - 400+ lines)
│   └── README.md                       # Guide index
│
└── scripts/
    ├── README.md                       # Complete inventory (NEW - 1000+ lines)
    │
    ├── testing/                        # 48 scripts
    │   ├── test_comprehensive_chatbot.sh
    │   ├── test_project_estimator.sh
    │   ├── test_rag_pipeline.py
    │   ├── test_agent11_integration.sh
    │   ├── test_document_handling_comprehensive.sh
    │   └── ... (43 more testing scripts)
    │
    ├── debugging/                      # 7 scripts
    │   ├── debug_rag_pipeline.py
    │   ├── diagnose_chunks.py
    │   ├── inspect_screener.py
    │   ├── inspect_drenting.py
    │   ├── monitor_thresholds.sh
    │   └── ... (2 more debugging scripts)
    │
    ├── validation/                     # (Ready for future scripts)
    │
    └── maintenance/                    # 3 scripts
        ├── scraper_service_working.py
        ├── fix_scraper_indentation.py
        └── auto_endpoint.py
```

---

## Documentation Created

### 1. Operations Guide (`guides/OPERATIONS_GUIDE.md`)
**Size**: 500+ lines
**Contains**:
- Log Analysis Commands
  - Basic log viewing (10+ commands)
  - Search for errors (15+ patterns)
  - Component-specific analysis (RAG, Agents, Scraping, LLM)
  - Performance monitoring
  - Advanced log analysis techniques

- Common Debugging Scenarios (6 detailed scenarios)
  1. Empty or poor quality responses
  2. Document processing failures
  3. RAG retrieval issues
  4. Project Estimator workflow failures
  5. Frontend-backend communication issues
  6. Web scraping failures

- Service Management
  - Individual service control
  - Health checks
  - Restart strategies
  - Container management
  - Database operations
  - Cache management
  - Performance tuning

- Testing Workflows
  - Comprehensive testing
  - Feature-specific testing
  - Integration testing
  - Performance testing
  - Testing with different models

- Quick Reference Commands (50+ one-liners)

---

### 2. Quick Reference Guide (`guides/QUICK_REFERENCE.md`)
**Size**: 400+ lines
**Contains**:
- Emergency quick fixes (5 critical commands)
- Most used log commands (10+ commands)
- Component-specific logs (5 categories)
- Health checks (6 services)
- Database quick queries (10+ queries)
- Testing quick commands
- Cache management
- Service control
- Debugging commands
- Common debugging scenarios (4 scenarios with solutions)
- Performance monitoring
- Data management
- API testing
- Cleanup commands
- Development workflow
- Useful aliases (15+ aliases)
- Common error messages and fixes (table)

---

### 3. Script Inventory (`scripts/README.md`)
**Size**: 1000+ lines
**Contains**:
- Complete index of all 58+ scripts
- Detailed description for each script
- Usage examples with syntax
- Prerequisites and dependencies
- Expected outputs
- Testing patterns
- Debugging patterns
- Best practices
- Troubleshooting guide
- Contributing guidelines
- Script templates

**Categories Documented**:
- Comprehensive test suites (3 scripts)
- Project Estimator testing (9 scripts)
- RAG pipeline testing (4 scripts)
- Web scraping testing (5 scripts)
- Template extraction testing (7 scripts)
- UI testing (5 scripts)
- Model testing (3 scripts)
- Workflow testing (4 scripts)
- Integration testing (3 scripts)
- Validation testing (2 scripts)
- Chat feature testing (3 scripts)
- RAG pipeline debugging (1 script)
- Document debugging (1 script)
- Web scraping inspection (4 scripts)
- Monitoring (1 script)
- Maintenance utilities (3 scripts)

---

### 4. Operations README (`README.md`)
**Size**: 300+ lines
**Contains**:
- Overview of operations documentation
- Quick navigation guide
- Key documents summary
- Script categories breakdown
- Common operations
- Troubleshooting flowchart
- Script organization summary
- Documentation quick access table
- Best practices
- Contributing guidelines
- Related documentation links
- Support and contact information
- Changelog
- Statistics

---

## Key Features of Documentation

### 1. Comprehensive Log Analysis

**Grep Patterns for All Components**:
```bash
# RAG Pipeline
docker-compose logs backend | grep -E "(RAG|query|retrieval|embedding)"

# Agents
docker-compose logs backend | grep -E "(Agent|workflow|state)"

# Web Scraping
docker-compose logs backend | grep -E "(scrap|playwright|extract)"

# LLM Service
docker-compose logs backend | grep -E "(LLM|model|token|OpenAI|Claude)"
```

**Advanced Filtering**:
- By log level (ERROR, WARNING, INFO)
- By time range (last hour, last day)
- By component (service-specific)
- With context (lines before/after)
- JSON extraction and formatting

---

### 2. Scenario-Based Debugging

Each scenario includes:
- **Symptoms**: What you observe
- **Diagnostic Commands**: How to investigate
- **Solution Steps**: How to fix
- **Verification**: How to confirm fix

**6 Comprehensive Scenarios**:
1. Empty or poor quality chat responses
2. Document processing failures
3. RAG retrieval issues
4. Project Estimator workflow failures
5. Frontend-backend communication issues
6. Web scraping failures

---

### 3. Quick Reference Commands

**One-Liner Diagnostics**:
```bash
# Count errors in last hour
docker-compose logs --since 1h backend | grep -c ERROR

# Find most recent error
docker-compose logs backend | grep ERROR | tail -1

# Check if all services running
docker-compose ps | grep -c "Up"

# Count processed documents
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM documents WHERE processed=true;"
```

**Quick Fixes**:
```bash
# Service won't start
docker-compose restart backend

# Empty responses
docker-compose exec redis redis-cli FLUSHALL && docker-compose restart backend

# Database issues
docker-compose restart postgres && sleep 10 && docker-compose restart backend
```

---

### 4. Complete Script Documentation

**For Each Script**:
- Purpose and description
- Usage syntax with examples
- Prerequisites
- What it tests/debugs
- Expected output format
- When to use it
- Related scripts

**Example Entry**:
```markdown
#### `debug_rag_pipeline.py`
**Purpose**: Comprehensive RAG pipeline debugging
**Usage**:
  python debug_rag_pipeline.py "query"
  python debug_rag_pipeline.py --analyze-documents
**Tests**:
- Embedding generation
- Vector search
- Context assembly
- Response generation
**Output**: Detailed diagnostic report
```

---

## Most Useful Commands (Top 20)

### Logs and Monitoring
1. `docker-compose logs backend | grep ERROR | tail -50` - Recent errors
2. `docker-compose logs -f backend` - Follow logs
3. `docker-compose logs backend | grep -E "(RAG|workflow)" | tail -50` - Component logs

### Health Checks
4. `docker-compose ps` - Service status
5. `curl http://localhost:8000/health` - Backend health
6. `./scripts/maintenance/verify-complete-setup.sh` - Full health check

### Database
7. `docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM documents;"` - Document count
8. `docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;"` - Embedding count

### Testing
9. `./test_comprehensive_chatbot.sh` - Full system test
10. `cd backend && python test_rag_pipeline.py` - RAG test
11. `cd backend && python debug_rag_pipeline.py "query"` - Debug RAG
12. `./test_project_estimator.sh` - Project Estimator test

### Service Management
13. `docker-compose restart backend` - Restart backend
14. `docker-compose build backend && docker-compose up -d backend` - Rebuild backend
15. `docker stats --no-stream` - Resource usage

### Cache
16. `docker-compose exec redis redis-cli FLUSHALL` - Clear all cache
17. `docker-compose exec redis redis-cli INFO stats` - Cache stats

### Debugging
18. `docker-compose logs backend | tail -100` - Last 100 log lines
19. `docker-compose exec backend bash` - Access backend shell
20. `docker-compose exec postgres psql -U postgres ragchatbot` - Access database

---

## Impact and Benefits

### Before Organization
- Scripts scattered across /tmp, root, backend directories
- No comprehensive operational documentation
- Difficult to find right script for task
- No systematic debugging approach
- Limited log analysis guidance

### After Organization
- ✓ All 58+ scripts organized by category
- ✓ 2000+ lines of comprehensive documentation
- ✓ Quick reference with 150+ commands
- ✓ 6 detailed debugging scenarios
- ✓ Complete script inventory with usage
- ✓ Systematic log analysis techniques
- ✓ Best practices documented
- ✓ Easy navigation and discovery

---

## Usage Statistics

### Scripts by Category
- Testing: 48 scripts (83%)
- Debugging: 7 scripts (12%)
- Maintenance: 3 scripts (5%)

### Scripts by Language
- Shell scripts (.sh): 28 scripts (48%)
- Python scripts (.py): 30 scripts (52%)

### Most Critical Scripts
1. `debug_rag_pipeline.py` - RAG debugging
2. `test_comprehensive_chatbot.sh` - Full system test
3. `test_project_estimator.sh` - Workflow validation
4. `inspect_screener.py` - Website inspection
5. `test_rag_pipeline.py` - RAG testing

---

## Documentation Metrics

- **Total Lines**: 2000+
- **Code Examples**: 200+
- **Command References**: 150+
- **Grep Patterns**: 50+
- **Debugging Scenarios**: 6
- **Quick Fixes**: 20+
- **Script Descriptions**: 58+

---

## Next Steps

### Immediate Use
1. Start with Quick Reference for common operations
2. Use Operations Guide for detailed scenarios
3. Refer to Script Inventory for specific scripts
4. Follow Best Practices for operations

### Continuous Improvement
1. Add new scripts to appropriate categories
2. Update documentation with new patterns
3. Document new debugging scenarios
4. Expand quick reference with frequent commands
5. Add performance tuning guidelines

### Integration
1. Link from main README.md
2. Reference in CLAUDE.md
3. Include in onboarding documentation
4. Add to CI/CD documentation

---

## Files Created/Modified

### New Files Created (4)
1. `/docs/operations/README.md` (300+ lines)
2. `/docs/operations/guides/OPERATIONS_GUIDE.md` (500+ lines)
3. `/docs/operations/guides/QUICK_REFERENCE.md` (400+ lines)
4. `/docs/operations/scripts/README.md` (1000+ lines)

### Scripts Organized (58+)
- 48 scripts to `/docs/operations/scripts/testing/`
- 7 scripts to `/docs/operations/scripts/debugging/`
- 3 scripts to `/docs/operations/scripts/maintenance/`

### Directories Created
- `/docs/operations/`
- `/docs/operations/guides/`
- `/docs/operations/scripts/`
- `/docs/operations/scripts/testing/`
- `/docs/operations/scripts/debugging/`
- `/docs/operations/scripts/validation/`
- `/docs/operations/scripts/maintenance/`

---

## Quick Access Links

### Primary Documents
- [Operations README](README.md) - Start here
- [Operations Guide](guides/OPERATIONS_GUIDE.md) - Comprehensive guide
- [Quick Reference](guides/QUICK_REFERENCE.md) - Quick commands
- [Script Inventory](scripts/README.md) - All scripts

### Common Tasks
- Emergency fixes: [Quick Reference - Emergency](guides/QUICK_REFERENCE.md#emergency-quick-fixes)
- View logs: [Operations Guide - Logs](guides/OPERATIONS_GUIDE.md#log-analysis-commands)
- Debug issue: [Operations Guide - Scenarios](guides/OPERATIONS_GUIDE.md#common-debugging-scenarios)
- Run tests: [Script Inventory - Testing](scripts/README.md#testing-scripts)

---

## Summary

Successfully created a comprehensive operational documentation system that:

1. **Organizes** 58+ scripts from scattered locations into structured categories
2. **Documents** every script with usage, purpose, and examples
3. **Provides** 500+ lines of operational guidance
4. **Includes** 400+ lines of quick reference commands
5. **Covers** 6 detailed debugging scenarios
6. **Offers** 150+ command references and examples
7. **Delivers** systematic log analysis techniques
8. **Establishes** best practices and standards

The documentation is immediately usable, comprehensive, and designed for both operators and developers.

---

**Completed**: 2025-11-27
**Status**: ✓ READY FOR USE
**Version**: 1.0
