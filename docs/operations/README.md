# Operations Documentation

> **Last Updated**: 2025-11-27
> **Purpose**: Central hub for all operational documentation, scripts, and guides

---

## Overview

This directory contains comprehensive operational documentation for running, debugging, testing, and maintaining the Enterprise RAG Chatbot system. All scripts have been organized from `/tmp` and root directories into structured categories.

---

## Documentation Structure

```
operations/
├── guides/                    # Operational guides
│   ├── OPERATIONS_GUIDE.md   # Comprehensive operations guide
│   ├── QUICK_REFERENCE.md    # Quick reference commands
│   └── README.md             # This file
│
└── scripts/                   # Organized operational scripts
    ├── testing/              # 48 test scripts
    ├── debugging/            # 7 debug scripts
    ├── validation/           # Validation scripts
    ├── maintenance/          # 3 maintenance scripts
    └── README.md             # Complete script inventory
```

---

## Quick Navigation

### For Operators

**New to the system?**
- Start with: [Quick Reference Guide](guides/QUICK_REFERENCE.md)
- Then read: [Operations Guide](guides/OPERATIONS_GUIDE.md)

**Need to debug an issue?**
- Quick fixes: [Quick Reference - Emergency Section](guides/QUICK_REFERENCE.md#emergency-quick-fixes)
- Detailed debugging: [Operations Guide - Debugging Scenarios](guides/OPERATIONS_GUIDE.md#common-debugging-scenarios)

**Need to run tests?**
- Test overview: [Operations Guide - Testing Workflows](guides/OPERATIONS_GUIDE.md#testing-workflows)
- All test scripts: [Script Inventory - Testing](scripts/README.md#testing-scripts)

### For Developers

**Making changes?**
- Pre-change checklist: [Operations Guide - Best Practices](guides/OPERATIONS_GUIDE.md#best-practices)
- Testing workflow: [Quick Reference - Development Workflow](guides/QUICK_REFERENCE.md#development-workflow)

**Need to analyze logs?**
- Log commands: [Quick Reference - Log Commands](guides/QUICK_REFERENCE.md#most-used-log-commands)
- Component-specific: [Operations Guide - Log Analysis](guides/OPERATIONS_GUIDE.md#log-analysis-commands)

**Creating new scripts?**
- Template: [Script Inventory - Contributing](scripts/README.md#contributing-new-scripts)
- Standards: [Operations Guide - Best Practices](guides/OPERATIONS_GUIDE.md#best-practices)

---

## Key Documents

### 1. Operations Guide
**File**: `guides/OPERATIONS_GUIDE.md`

**Contains**:
- Comprehensive log analysis techniques
- Common debugging scenarios with solutions
- Service management procedures
- Testing workflows
- Quick reference commands
- Best practices

**When to use**: Full operational reference, troubleshooting guide

---

### 2. Quick Reference
**File**: `guides/QUICK_REFERENCE.md`

**Contains**:
- Emergency quick fixes
- Most used commands
- One-liner diagnostics
- Common error messages and fixes
- Useful aliases

**When to use**: Quick access during operations, copy-paste commands

---

### 3. Script Inventory
**File**: `scripts/README.md`

**Contains**:
- Complete index of all 58+ operational scripts
- Detailed description of each script
- Usage examples
- Prerequisites and dependencies
- Expected outputs

**When to use**: Finding and using operational scripts

---

## Script Categories

### Testing Scripts (48 scripts)

Located in: `scripts/testing/`

**Categories**:
- Comprehensive test suites (3)
- Project Estimator testing (9)
- RAG pipeline testing (4)
- Web scraping testing (5)
- Template extraction testing (7)
- UI testing (5)
- Model testing (3)
- Workflow testing (4)
- Integration testing (3)
- Validation testing (2)
- Chat feature testing (3)

**Most used**:
```bash
./test_comprehensive_chatbot.sh          # Full system test
./test_project_estimator.sh              # Project Estimator test
cd backend && python test_rag_pipeline.py # RAG pipeline test
```

**See**: [Script Inventory - Testing Scripts](scripts/README.md#testing-scripts)

---

### Debugging Scripts (7 scripts)

Located in: `scripts/debugging/`

**Scripts**:
- `debug_rag_pipeline.py` - Comprehensive RAG debugging
- `diagnose_chunks.py` - Document chunking analysis
- `inspect_screener.py` - CSS selector inspection
- `inspect_drenting.py` - Website inspection
- `monitor_thresholds.sh` - Real-time monitoring

**Most used**:
```bash
cd backend && python debug_rag_pipeline.py "query"  # Debug RAG
cd backend && python inspect_screener.py             # Inspect website
./monitor_thresholds.sh                              # Monitor system
```

**See**: [Script Inventory - Debugging Scripts](scripts/README.md#debugging-scripts)

---

### Maintenance Scripts (3 scripts)

Located in: `scripts/maintenance/`

**Scripts**:
- `scraper_service_working.py` - Reference implementation
- `fix_scraper_indentation.py` - Auto-fix code issues
- `auto_endpoint.py` - Generate API endpoints

**See**: [Script Inventory - Maintenance Scripts](scripts/README.md#maintenance-scripts)

---

## Common Operations

### System Health Check

```bash
# Quick health check
docker-compose ps
curl http://localhost:8000/health

# Comprehensive health check
./scripts/maintenance/verify-complete-setup.sh
```

**More**: [Quick Reference - Health Checks](guides/QUICK_REFERENCE.md#health-checks)

---

### Viewing Logs

```bash
# Recent errors
docker-compose logs backend | grep ERROR | tail -50

# Follow logs
docker-compose logs -f backend

# Component-specific
docker-compose logs backend | grep -E "(RAG|workflow|scrap)" | tail -50
```

**More**: [Operations Guide - Log Analysis](guides/OPERATIONS_GUIDE.md#log-analysis-commands)

---

### Debugging Issues

```bash
# Empty responses
cd backend && python debug_rag_pipeline.py "test query"

# Service issues
docker-compose logs backend | tail -100

# Database issues
docker-compose exec postgres psql -U postgres -d ragchatbot
```

**More**: [Operations Guide - Debugging Scenarios](guides/OPERATIONS_GUIDE.md#common-debugging-scenarios)

---

### Running Tests

```bash
# Full system test
./test_comprehensive_chatbot.sh

# Specific feature test
cd backend && python test_rag_pipeline.py

# Integration test
./scripts/testing/comprehensive-validation.sh
```

**More**: [Operations Guide - Testing Workflows](guides/OPERATIONS_GUIDE.md#testing-workflows)

---

### Service Management

```bash
# Restart service
docker-compose restart backend

# Rebuild service
docker-compose build backend && docker-compose up -d backend

# View resources
docker stats --no-stream
```

**More**: [Operations Guide - Service Management](guides/OPERATIONS_GUIDE.md#service-management)

---

## Troubleshooting Flowchart

```
Issue Detected
    ↓
Check Quick Reference for immediate fix
    ↓
Issue persists?
    ↓
Check Operations Guide for debugging scenario
    ↓
Run appropriate debugging script
    ↓
Check logs with component-specific filter
    ↓
Apply fix from guide
    ↓
Run test to verify
    ↓
Document new issue if not covered
```

---

## Script Organization Summary

### Total Scripts Organized: 58+

**From `/tmp/` directory**: 28 scripts
- Testing: 19
- Debugging: 1
- Maintenance: 3
- Validation: 5

**From root directory**: 12 scripts
- Testing: 12

**From `backend/` directory**: 16 scripts
- Testing: 10
- Debugging: 6

**Existing in `scripts/`**: Preserved
- Setup: 8 scripts
- Testing: 15 scripts
- Debugging: 10 scripts
- Maintenance: 3 scripts

---

## Documentation Quick Access

| Need | Document | Section |
|------|----------|---------|
| Fix urgent issue | Quick Reference | Emergency Quick Fixes |
| Understand log error | Operations Guide | Log Analysis Commands |
| Debug empty responses | Operations Guide | Scenario 1 |
| Test after changes | Script Inventory | Testing Scripts |
| Find specific script | Script Inventory | Script Index |
| Monitor performance | Quick Reference | Performance Monitoring |
| Service management | Operations Guide | Service Management |
| Database queries | Quick Reference | Database Quick Queries |
| API testing | Quick Reference | API Testing |

---

## Best Practices

### Before Operations

1. **Read Quick Reference** for command syntax
2. **Check service health** before starting
3. **Review recent logs** for context
4. **Have backup** of important data

### During Operations

1. **Use appropriate script** from inventory
2. **Monitor logs** in real-time
3. **Document issues** encountered
4. **Test incrementally** after changes

### After Operations

1. **Verify fix** with tests
2. **Check logs** for new issues
3. **Update documentation** if needed
4. **Clean up** temporary data

---

## Contributing

### Adding New Scripts

1. **Create script** following template in [Script Inventory](scripts/README.md#script-template)
2. **Place in appropriate directory** (testing/debugging/maintenance)
3. **Add to inventory** in `scripts/README.md`
4. **Update guide** if introducing new pattern
5. **Test script** thoroughly
6. **Document usage** with examples

### Improving Documentation

1. **Identify gap** in current documentation
2. **Draft update** with clear examples
3. **Test commands** for accuracy
4. **Submit with context** about the issue
5. **Update version** and last updated date

---

## Related Documentation

### Main Documentation
- **README.md**: Project overview and setup
- **CLAUDE.md**: AI assistant development guide
- **STATUS.md**: Current project status
- **CONTRIBUTING.md**: Contribution guidelines

### Specialized Guides
- **Setup**: `/docs/setup/` - Setup and configuration
- **Architecture**: `/docs/architecture/` - System architecture
- **Debugging**: `/docs/debugging/` - Detailed debugging guides
- **Testing**: `/docs/testing/` - Testing documentation
- **Evaluation**: `/docs/evaluation/` - RAG evaluation guides

### Scripts
- **Main Scripts**: `/scripts/` - Original organized scripts
  - Setup scripts: `/scripts/setup/`
  - Testing scripts: `/scripts/testing/`
  - Debugging scripts: `/scripts/debugging/`
  - Maintenance scripts: `/scripts/maintenance/`

---

## Support and Contact

### For Issues

1. **Check Quick Reference** for immediate solutions
2. **Review Operations Guide** for detailed scenarios
3. **Run diagnostic scripts** to gather information
4. **Check existing documentation** in related guides
5. **Document and report** if issue is not covered

### For Questions

1. **Search documentation** using keywords
2. **Check script inventory** for existing tools
3. **Review related guides** for context
4. **Consult team** with specific questions
5. **Update documentation** with answers for future reference

---

## Changelog

### Version 1.0 (2025-11-27)

**Added**:
- Complete operations documentation structure
- Comprehensive Operations Guide (500+ lines)
- Quick Reference Guide (400+ lines)
- Complete Script Inventory (1000+ lines)
- Organized 58+ scripts from /tmp, root, and backend
- Script categories: testing, debugging, validation, maintenance

**Organized**:
- 48 testing scripts with detailed descriptions
- 7 debugging scripts with usage examples
- 3 maintenance scripts with purposes
- All scripts categorized and documented

**Documented**:
- Log analysis techniques and patterns
- 6 common debugging scenarios with solutions
- Service management procedures
- Testing workflows and patterns
- Quick reference commands
- Best practices and troubleshooting

---

## Statistics

- **Total Scripts Organized**: 58+
- **Testing Scripts**: 48
- **Debugging Scripts**: 7
- **Maintenance Scripts**: 3
- **Documentation Pages**: 4
- **Total Lines**: 2000+
- **Code Examples**: 200+
- **Command References**: 150+

---

**Last Updated**: 2025-11-27
**Maintainer**: DevOps Team
**Version**: 1.0
