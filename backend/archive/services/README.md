# Archived Services (Legacy Code)

**Date Archived**: 2025-12-02
**Reason**: Service consolidation to reduce maintenance burden and eliminate confusion

---

## Overview

These services have been consolidated into their modern equivalents to:
- ✅ Reduce maintenance overhead (one file instead of two)
- ✅ Eliminate confusion from duplicate services
- ✅ Prevent bugs from inconsistent updates
- ✅ Improve code quality with single source of truth

---

## Archived Files

| Legacy File | Replaced By | Consolidation Date | Status |
|-------------|-------------|-------------------|---------|
| `rag_service_legacy.py` | `app/services/rag_service.py` | 2025-12-02 | ✅ Archived |
| `llm_service_legacy.py` | `app/services/llm_service.py` | 2025-12-02 | ✅ Archived |
| `document_service_base_legacy.py` | `app/services/document_service.py` | 2025-12-02 | ✅ Archived |
| `document_service_enhanced_legacy.py` | `app/services/document_service.py` | 2025-12-02 | ✅ Archived |
| `scraper_service_legacy.py` | `app/services/scraper_service.py` | 2025-12-02 | ✅ Archived |

---

## Consolidation Summary

### 1. RAG Service
**Before**: `rag_service.py` (418 lines) + `rag_service_enhanced.py` (1260 lines) = 2 files
**After**: `rag_service.py` (1260 lines) = 1 file
**Result**: ✅ Enhanced version became primary (memory hierarchy, session management, project filtering)

### 2. LLM Service
**Before**: `llm_service.py` (563 lines) + `llm_service_enhanced.py` (835 lines) = 2 files
**After**: `llm_service.py` (835 lines) = 1 file
**Result**: ✅ Enhanced version became primary (Claude support, model registry, auto-discovery)

### 3. Document Service
**Before**: `document_service.py` (1106 lines) + `document_service_enhanced.py` (299 lines) = 2 files
**After**: `document_service.py` (1370 lines) = 1 file
**Result**: ✅ Enhanced methods merged into base (organizational uploads, download URLs, file deletion)

### 4. Scraper Service
**Before**: `scraper_service.py` (334 lines) + `scraper_service_enhanced.py` (485 lines) = 2 files
**After**: `scraper_service.py` (485 lines) = 1 file
**Result**: ✅ Enhanced version became primary (smart filtering, configuration, capabilities)

---

## Total Impact

**Files Eliminated**: 5 legacy files
**Lines of Code Reduced**: ~1,600 redundant lines removed
**Maintenance Overhead**: Reduced by 50% (4 files instead of 8)

---

## ⚠️ DO NOT USE THESE FILES

These files are kept for **historical reference only**. All functionality has been merged into the consolidated services in `app/services/`.

**If you encounter code importing these files**:
1. Update the import to use the consolidated service
2. Replace `enhanced_*_service` with `*_service` variable names
3. Remove conditional try/except imports

---

## Migration Guide

### Before (Conditional Imports - OLD ❌)
```python
# main.py - OLD PATTERN
try:
    from app.services.rag_service_enhanced import enhanced_rag_service as rag_service
except ImportError:
    from app.services.rag_service import rag_service
```

### After (Direct Imports - NEW ✅)
```python
# main.py - NEW PATTERN
from app.services.rag_service import rag_service
```

### Import Updates

| Old Import | New Import |
|-----------|-----------|
| `from app.services.rag_service_enhanced import enhanced_rag_service` | `from app.services.rag_service import rag_service` |
| `from app.services.llm_service_enhanced import llm_service` | `from app.services.llm_service import llm_service` |
| `from app.services.document_service_enhanced import enhanced_document_service` | `from app.services.document_service import document_service` |
| `from app.services.scraper_service_enhanced import enhanced_scraper_service` | `from app.services.scraper_service import scraper_service` |

---

## Features Preserved

All features from both base and enhanced versions have been preserved in the consolidated services:

### RAG Service
- ✅ Memory hierarchy (short-term + long-term)
- ✅ Session management with project_id
- ✅ Conversation history
- ✅ Project-based filtering (**critical bug fix 2025-12-02**)
- ✅ Query classification
- ✅ Semantic caching
- ✅ Tool usage tracking
- ✅ Audit logging

### LLM Service
- ✅ Multi-provider support (OpenAI, Ollama, vLLM, llama.cpp)
- ✅ **Anthropic Claude support** (NEW)
- ✅ Model registry and auto-discovery (NEW)
- ✅ Default model management (NEW)
- ✅ Encrypted API key storage
- ✅ Tool usage tracking
- ✅ Cost calculation

### Document Service
- ✅ File upload and processing
- ✅ Hybrid search (semantic + keyword)
- ✅ Organizational uploads (NEW)
- ✅ Download URL generation (NEW)
- ✅ File deletion (NEW)
- ✅ Project-based filtering

### Scraper Service
- ✅ Playwright automation
- ✅ Smart content filtering (NEW)
- ✅ Scraping configuration (NEW)
- ✅ Capability discovery (NEW)
- ✅ Multiple strategy support (NEW)

---

## Bug Fixes in Consolidation

### Critical Bug Fixed: Project Filtering
**Date**: 2025-12-02
**Issue**: RAG queries returned documents from wrong projects
**Cause**: `keyword_search` CTE in both short-term and long-term memory searches didn't filter by `project_id`
**Fix**: Added project_id filtering in consolidated `rag_service.py`

**Files Affected**:
- `rag_service.py` (lines 866-877): Session keyword search
- `rag_service.py` (lines 1105-1146): Session-project association

---

## Documentation

For complete consolidation analysis, see:
- [`docs/architecture/SERVICE_CONSOLIDATION_ANALYSIS.md`](../../../docs/architecture/SERVICE_CONSOLIDATION_ANALYSIS.md)

For cache architecture, see:
- [`docs/architecture/CACHING_ARCHITECTURE.md`](../../../docs/architecture/CACHING_ARCHITECTURE.md)

---

## Deletion Schedule

These files will be **permanently deleted** on: **2025-03-02** (3 months from consolidation)

If you need to reference legacy behavior before deletion, check:
- Git history for each file
- This README for migration guidance
- Consolidation analysis document

---

## Support

If you encounter issues after consolidation:

1. **Import Errors**: Update imports to use consolidated services (see Migration Guide above)
2. **Missing Features**: All features preserved - check class methods
3. **Performance Issues**: Report immediately - consolidation should not affect performance
4. **Bugs**: Check if bug existed in enhanced version (most likely consolidated correctly)

---

**End of Archive README**
