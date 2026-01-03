# British Council & CRU POC - Import Issue Summary

**Date:** 2026-01-02
**Status:** 🔧 Import errors discovered - needs correction

---

## Issue Found

The British Council and CRU POC implementations have **import errors** that prevent them from loading. The services were built assuming certain tier1 infrastructure classes/functions that don't match the actual codebase.

### Root Cause

**File:** `backend/app/tier_3/customer_solutions/british_council_service.py` (line 8)
**File:** `backend/app/tier_3/customer_solutions/cru_service.py` (line 11)

**Error:**
```
ImportError: cannot import name 'RerankerService' from 'app.tier_1.embeddings.reranker_service'
```

**Issue:** The `reranker_service.py` exports `CrossEncoderReranker` class and `get_reranker()` function, not `RerankerService` / `get_reranker_service()`.

---

## What Was Completed

### Files Created/Modified:
1. ✅ `backend/app/tier_3/customer_solutions/british_council_schemas.py` - Enhanced schemas
2. ✅ `backend/app/tier_3/customer_solutions/british_council_service.py` - Service implementation (HAS IMPORT ERRORS)
3. ✅ `backend/app/tier_3/customer_solutions/cru_schemas.py` - Enhanced schemas
4. ✅ `backend/app/tier_3/customer_solutions/cru_service.py` - Service implementation (HAS IMPORT ERRORS)
5. ✅ Routes files (british_council_routes.py, cru_routes.py) - Already correctly configured
6. ✅ `POC_IMPLEMENTATION_COMPLETE.md` - Documentation

### What Works:
- Routes are registered in `backend/app/main.py` (lines 2480-2513)
- Endpoints `/api/v1/customer/british_council/status` and `/process` are defined
- Endpoints `/api/v1/customer/cru/status` and `/process` are defined
- Frontend `ModuleInterface` component is ready to render them
- Schemas are correctly defined

### What Doesn't Work:
- Service implementations fail to import due to incorrect tier1 service references
- Endpoints return 404 because services can't be instantiated

---

## Tier1 Services - Actual vs. Assumed

| Service | Assumed Import | Actual Export |
|---------|---------------|---------------|
| **Reranker** | `from app.tier_1.rag.reranker_service import Reranker Service, get_reranker_service` | `from app.tier_1.embeddings.reranker_service import CrossEncoderReranker, get_reranker` |
| **Intelligent Retrieval** | Assumed exists at `app.tier_1.rag.intelligent_retrieval_service` | ✅ EXISTS at `app.tier_1.rag.intelligent_retrieval_service` |
| **Elasticsearch** | Assumed exists at `app.tier_1.rag.elasticsearch_service` | ✅ EXISTS at `app.tier_1.rag.elasticsearch_service` |
| **Rank Fusion** | Assumed exists at `app.tier_1.rag.rank_fusion_service` | ✅ EXISTS at `app.tier_1.rag.rank_fusion_service` |
| **Confidence Scorer** | Assumed exists at `app.tier_1.rag.confidence_scorer` | ✅ EXISTS at `app.tier_1.rag.confidence_scorer` |

---

## Next Steps to Fix

### Option 1: Fix Imports (Quick Fix - 5 min)
Update both service files to use correct imports:

**In `british_council_service.py` and `cru_service.py`:**

```python
# BEFORE (WRONG):
from app.tier_1.embeddings.reranker_service import RerankerService, get_reranker_service

# AFTER (CORRECT):
from app.tier_1.embeddings.reranker_service import CrossEncoderReranker, get_reranker
```

Then update usage in code:
```python
# BEFORE:
self.reranker = get_reranker_service()

# AFTER:
self.reranker = get_reranker()
```

### Option 2: Simplify Implementation (Medium Fix - 15 min)
Create minimal placeholder services similar to Grant Thornton POC:
- Remove complex RAG logic
- Use only LLMService for basic responses
- Keep schemas and routes intact
- Return mock/placeholder data

### Option 3: Full Implementation (Complete Fix - 1 hour)
1. Check ALL tier1 service signatures
2. Update service implementations to match actual APIs
3. Test imports manually
4. Restart backend
5. Verify endpoints
6. Test via UI

---

## Recommended Approach

**Use Option 1** (Fix Imports) because:
- Most infrastructure DOES exist (intelligent_retrieval, elasticsearch, etc.)
- Only the reranker import is wrong
- Minimal code changes needed
- Preserves the enhanced RAG functionality

---

## Testing After Fix

```bash
# 1. Test imports
docker exec rag-backend python -c "from app.tier_3.customer_solutions.british_council_service import British_councilService; print('✓ OK')"

# 2. Restart backend
docker restart rag-backend && sleep 15

# 3. Test endpoints
curl http://localhost:8000/api/v1/customer/british_council/status | jq '.'
curl http://localhost:8000/api/v1/customer/cru/status | jq '.'
```

---

## Current State

**Backend:** Running but POC routes return 404
**Frontend:** ModuleInterface ready to render POCs
**Routes:** Registered but failing at import time
**Schemas:** ✅ Working
**Services:** ❌ Import errors

---

## Files to Fix

1. `backend/app/tier_3/customer_solutions/british_council_service.py` (line 8 + usage)
2. `backend/app/tier_3/customer_solutions/cru_service.py` (line 11 + usage)

**Changes needed:** ~6 lines total across 2 files

---

**Priority:** P1 - Blocking POC functionality
**Estimated fix time:** 5-10 minutes
**Risk:** Low - isolated to POC implementations
