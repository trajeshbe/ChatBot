# Project Isolation Debugging - Comprehensive Logging Added

## Date: 2025-12-01

---

## Problem Status

**Issue**: Project filtering in RAG queries is NOT working despite multiple code fixes. User queries from Global project return results from Construction Intelligence project files.

**Current Status**: ⏳ **INVESTIGATING** - Added comprehensive debug logging to trace project_id flow through entire stack.

---

## Debug Logging Added

### Purpose
To trace the `project_id` parameter as it flows through the entire request stack:
1. Frontend → API Endpoint
2. API Endpoint → Enhanced RAG Agent
3. Enhanced RAG Agent → RAG Service
4. RAG Service → Document Service → SQL

### Files Modified

#### 1. API Endpoint (`backend/app/main.py` - Line 641-642)

**Location**: `/api/v1/query` endpoint

**Added Logging**:
```python
# 🔍 DEBUG: Log project_id received from frontend
logger.info(f"🔍 DEBUG [API /query endpoint]: project_id from Form = {project_id}")
```

**Purpose**: Verify that frontend is actually sending project_id in the request.

---

#### 2. RAG Service (`backend/app/services/rag_service_enhanced.py` - Line 74-75)

**Location**: `query()` function start

**Added Logging**:
```python
# 🔍 DEBUG: Log incoming project_id parameter
logger.info(f"🔍 DEBUG [RAG Service query()]: project_id parameter = {project_id}")
```

**Purpose**: Verify that RAG service receives project_id from enhanced agent.

---

#### 3. Enhanced RAG Agent (`backend/app/agents/enhanced_rag_agent.py`)

**Location 1**: FORCE_RAG routing path (Line 203-204)

**Added Logging**:
```python
# 🔍 DEBUG: Log project_id being passed to RAG
logger.info(f"🔍 DEBUG [FORCE_RAG path]: project_id = {tool_params_rag.get('project_id')}")
```

**Purpose**: Verify that project_id is in tool_params when FORCE_RAG routing is used.

**Location 2**: `_execute_tool_document_rag` method (Line 1194-1195)

**Added Logging**:
```python
# 🔍 DEBUG: Log project_id received in _execute_tool_document_rag
logger.info(f"🔍 DEBUG [_execute_tool_document_rag]: project_id from tool_params = {tool_params.get('project_id')}")
```

**Purpose**: Verify that project_id is received when executing the RAG tool.

---

## Expected Debug Log Flow

When a user queries from Global project, logs should show:

```
[API /query endpoint] 🔍 DEBUG: project_id from Form = <Global-UUID>
[Enhanced RAG Agent] 🔍 DEBUG [FORCE_RAG path]: project_id = <Global-UUID>
[Enhanced RAG Agent] 🔍 DEBUG [_execute_tool_document_rag]: project_id from tool_params = <Global-UUID>
[RAG Service] 🔍 DEBUG [RAG Service query()]: project_id parameter = <Global-UUID>
[RAG Service] 📁 Query scoped to project from parameter: <Global-UUID>
```

### If Logs Show `None` at Any Stage

This will pinpoint exactly where project_id is getting lost:

- **None at API level** → Frontend not sending it
- **None at Agent level** → user_preferences not being built correctly
- **None at RAG Service** → Enhanced agent not passing it through
- **None but no SQL filter** → Document service not using it

---

## Actions Taken This Session

1. ✅ **Cleared Redis cache** - Eliminated cached results
2. ✅ **Added debug logging** at 4 critical points in the stack
3. ✅ **Restarted backend** to apply logging changes

---

## Previous Fixes Applied (Still Not Working)

### Fix 1: RAG Service (`rag_service_enhanced.py` - Lines 159-174)

**Problem**: Line 160 was executing `project_id = None`, overwriting the parameter.

**Fix**: Changed to conditional:
```python
if project_id is None:  # Only get from session if not provided
```

---

### Fix 2: Enhanced RAG Agent (`enhanced_rag_agent.py`)

**Three Locations Fixed**:

1. **Line 199** - FORCE_RAG tool_params dict
   ```python
   "project_id": user_preferences.get('project_id') if user_preferences else None,  # Added
   ```

2. **Line 959** - Synthesis query call
   ```python
   project_id=state["user_preferences"].get("project_id"),  # Added
   ```

3. **Line 1206** - Force RAG execution
   ```python
   project_id=tool_params.get('project_id'),  # Added
   ```

---

## What Debug Logs Will Reveal

### Scenario 1: Frontend Not Sending project_id
```
🔍 DEBUG [API /query endpoint]: project_id from Form = None
```
**Action**: Check frontend ChatInterface.tsx sendMessage() function.

### Scenario 2: Agent Not Receiving project_id
```
🔍 DEBUG [API /query endpoint]: project_id from Form = <UUID>
🔍 DEBUG [FORCE_RAG path]: project_id = None
```
**Action**: Check how user_preferences is built in main.py.

### Scenario 3: RAG Service Not Receiving project_id
```
🔍 DEBUG [_execute_tool_document_rag]: project_id from tool_params = <UUID>
🔍 DEBUG [RAG Service query()]: project_id parameter = None
```
**Action**: Check enhanced_rag_service.query() call parameters.

### Scenario 4: Filter Not Being Applied
```
🔍 DEBUG [RAG Service query()]: project_id parameter = <UUID>
(No "📁 Query scoped to project" log)
```
**Action**: Check document_service.py SQL query construction.

---

## Next Steps

1. **User Tests Query** - Ask user to query "tell me about Children book" from Global project
2. **Examine Debug Logs** - Check where project_id is None or missing
3. **Identify Root Cause** - Based on which layer shows None first
4. **Apply Targeted Fix** - Fix the specific layer that's losing project_id
5. **Verify Fix** - Retest and confirm project filtering works

---

## Database Context

### Global Project Files
```sql
SELECT filename FROM documents d
JOIN projects p ON d.project_id = p.id
WHERE p.name = 'Global';
```

**Result**: 9 files - NO children's books

### Construction Intelligence Files
```
book1 - smart
Children1 - smart
```

**These files should NOT appear in Global project queries.**

---

## Test Query

**Query**: "tell me about Children book"
**Expected**: No results (Global has no children's books)
**Actual (Before Fix)**: Results from book1-smart, Children1-smart (Construction Intelligence)

---

## Debug Commands

### Watch logs in real-time
```bash
docker-compose logs backend -f | grep -E "🔍 DEBUG|📁 Query scoped|FORCE_RAG"
```

### Check specific query logs
```bash
docker-compose logs backend --tail=300 --since=5m | grep -E "🔍 DEBUG|project_id"
```

### Verify Redis cache cleared
```bash
docker-compose exec redis redis-cli KEYS "*"
```

---

## Status: ⏳ DEBUGGING IN PROGRESS

**Backend**: Restarted with debug logging
**Cache**: Cleared
**Logs**: Ready to capture project_id flow

**Waiting for**: User to test query and provide results so we can analyze debug logs.

---

## Files Modified Summary

| File | Lines Changed | Purpose |
|------|--------------|---------|
| `backend/app/main.py` | 641-642 | Log project_id from frontend |
| `backend/app/services/rag_service_enhanced.py` | 74-75 | Log project_id at RAG entry |
| `backend/app/agents/enhanced_rag_agent.py` | 203-204 | Log project_id in FORCE_RAG path |
| `backend/app/agents/enhanced_rag_agent.py` | 1194-1195 | Log project_id in tool execution |

**Total Debug Logging Points**: 4

---

## Related Documentation

- Previous session: `/tmp/PASSWORD_HASHING_SECURITY_FIX_COMPLETE.md`
- Project RAG filtering: `/tmp/PROJECT_RAG_FILTERING_IMPLEMENTATION_COMPLETE.md`
