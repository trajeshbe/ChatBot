# RAG Service Consolidation - Phase 2 through Phase 5

**Date**: 2025-11-24
**Status**: Phase 1 Complete ✅ | Phase 2-5 Documented for Future Implementation
**Related**: See `/tmp/RAG_CONSOLIDATION_COMPLETE_ANALYSIS.md` for complete analysis

---

## Executive Summary

**Phase 1 (COMPLETE ✅)**: Enhanced RAG Agent consolidation
- Fixed `backend/app/agents/enhanced_rag_agent.py:730` to use `enhanced_rag_service`
- Backend verified healthy
- No breaking changes

**Remaining Phases (THIS DOCUMENT)**:
- **Phase 2**: GraphQL API consolidation
- **Phase 3**: MCP Server consolidation
- **Phase 4**: Deprecate simple RAG agent
- **Phase 5**: Remove regular rag_service.py (after monitoring)

---

## Background

### Why Consolidate?

We currently have two RAG services:

1. **`rag_service.py`** (Nov 13, 2025)
   - Basic RAG functionality
   - No memory hierarchy
   - No session management

2. **`rag_service_enhanced.py`** (Nov 14, 2025)
   - Enhanced with memory hierarchy
   - Session-specific document priority
   - Better observability
   - Advanced reranking

**Goal**: Consolidate to `enhanced_rag_service` only for consistency and maintainability.

### Safety Confirmation

✅ **NO BREAKING CHANGES** - Verified safe because:
1. Both services have identical signatures (after weight parameter fixes)
2. `enhanced_rag_service` is a **superset** of `rag_service`
3. `main.py` already uses enhanced service successfully
4. All parameter flow is complete in both services

---

## Phase 2: GraphQL API Consolidation

### Priority: High
**Timeline**: Next sprint
**Risk**: Low (same pattern as main.py, already working)

### Files to Change

#### File: `backend/app/api/graphql/schema.py`

**Current State** (Lines 5 + 112):
```python
# Line 5 - Import
from app.services.rag_service import rag_service

# Line 112 - Usage
result = await rag_service.query(
    query_text=query_input.query,
    conversation_history=query_input.conversation_history,
    use_cache=query_input.use_cache,
    model_id=query_input.model_id,
    db=db
)
```

**Required Change**:
```python
# Line 5 - Change import to use enhanced service with alias
from app.services.rag_service_enhanced import enhanced_rag_service as rag_service

# Line 112 - No change needed (alias maintains compatibility)
result = await rag_service.query(
    query_text=query_input.query,
    conversation_history=query_input.conversation_history,
    use_cache=query_input.use_cache,
    model_id=query_input.model_id,
    db=db
)
```

### Implementation Steps

1. **Make the change**:
   ```bash
   # Edit the import line
   vim backend/app/api/graphql/schema.py
   # Change line 5 as shown above
   ```

2. **Restart backend**:
   ```bash
   docker-compose restart backend
   ```

3. **Verify health**:
   ```bash
   curl http://localhost:8000/health
   ```

4. **Test GraphQL query**:
   ```bash
   curl -X POST "http://localhost:8000/graphql" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "mutation { query(input: { query: \"Who is Aadhan?\", useCache: false }) { answer sources { filename } modelUsed } }"
     }'
   ```

### Expected Impact

**Benefits**:
- GraphQL queries get memory hierarchy features
- Session-specific document priority
- Better observability and logging
- Consistent with REST API (main.py)

**No Breaking Changes**:
- Same method signature
- Same response format
- Backward compatible via aliasing

### Testing Requirements

```bash
# Test 1: Basic GraphQL query
curl -X POST "http://localhost:8000/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ documents { id filename } }"}'

# Test 2: RAG query with session
curl -X POST "http://localhost:8000/graphql" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { query(input: { query: \"test\", sessionId: \"test-session\" }) { answer } }"
  }'

# Test 3: Monitor logs for errors
docker-compose logs backend --tail=100 | grep -i error
```

### Success Criteria

- ✅ GraphQL endpoint responds normally
- ✅ Queries return expected results
- ✅ No errors in backend logs
- ✅ Memory hierarchy features work (test with session-specific documents)

---

## Phase 3: MCP Server Consolidation

### Priority: Medium
**Timeline**: After Phase 2 (same sprint or next)
**Risk**: Low (same pattern)

### Files to Change

#### File: `backend/app/services/mcp_server_service.py`

**Current State** (Lines 355 + 357):
```python
# Line 355 - Import
from app.services.rag_service import rag_service

# Line 357 - Usage
result = await rag_service.query_documents(
    query_text=request.query,
    db=db
)
```

**Required Change**:
```python
# Line 355 - Change import to use enhanced service with alias
from app.services.rag_service_enhanced import enhanced_rag_service as rag_service

# Line 357 - No change needed (alias maintains compatibility)
result = await rag_service.query_documents(
    query_text=request.query,
    db=db
)
```

### Implementation Steps

1. **Make the change**:
   ```bash
   vim backend/app/services/mcp_server_service.py
   # Change line 355 as shown above
   ```

2. **Restart backend**:
   ```bash
   docker-compose restart backend
   ```

3. **Test MCP integration**:
   ```bash
   # Test MCP server health
   curl http://localhost:8000/api/v1/mcp/health

   # Test MCP query (if endpoint exists)
   curl -X POST "http://localhost:8000/api/v1/mcp/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "test query"}'
   ```

### Expected Impact

**Benefits**:
- MCP integration gets enhanced RAG features
- Memory hierarchy support
- Better observability

**No Breaking Changes**:
- Same method signature
- MCP protocol remains unchanged

### Testing Requirements

```bash
# Test 1: MCP server health
curl http://localhost:8000/api/v1/mcp/health

# Test 2: MCP query (adjust endpoint as needed)
# Check mcp_routes.py for actual endpoint

# Test 3: Monitor logs
docker-compose logs backend --tail=100 | grep -i "mcp"
```

### Success Criteria

- ✅ MCP server responds normally
- ✅ Queries through MCP work correctly
- ✅ No errors in backend logs
- ✅ MCP integration tests pass

---

## Phase 4: Deprecate Simple RAG Agent

### Priority: Low
**Timeline**: After Phase 2+3 complete (1-2 weeks monitoring period)
**Risk**: Low (alternative agent exists)

### Background

We have two RAG agents:

1. **`rag_agent.py`** - Simple agent using basic rag_service
2. **`enhanced_rag_agent.py`** - Advanced agent with multi-tool support ✅

The simple agent is redundant after consolidation.

### Files to Change

#### File: `backend/app/agents/rag_agent.py`

**Add deprecation warning** (top of file):
```python
"""
Simple RAG Agent - DEPRECATED

⚠️ DEPRECATION WARNING:
This simple RAG agent is deprecated as of 2025-11-24.
Please use `enhanced_rag_agent.py` instead, which provides:
- Memory hierarchy (short-term + long-term)
- Multi-tool support
- Better observability
- Session management

This file will be removed in the next major version (v2.0.0).
"""

import warnings
warnings.warn(
    "rag_agent.py is deprecated. Use enhanced_rag_agent.py instead.",
    DeprecationWarning,
    stacklevel=2
)

# Rest of existing code...
```

### Documentation Updates

Update the following documentation files:

1. **`docs/architecture/MULTI_TOOL_AGENT_ARCHITECTURE.md`**
   - Mark simple agent as deprecated
   - Point to enhanced_rag_agent.py

2. **`README.md`**
   - Update agent references
   - Remove simple agent from examples

3. **`docs/guides/QUICKSTART.md`**
   - Update to use enhanced agent only

### Migration Guide

Create: `docs/migration/SIMPLE_TO_ENHANCED_RAG_AGENT_MIGRATION.md`

```markdown
# Migrating from Simple to Enhanced RAG Agent

## Before (rag_agent.py)
```python
from app.agents.rag_agent import rag_agent

result = await rag_agent.query(query_text, db)
```

## After (enhanced_rag_agent.py)
```python
from app.agents.enhanced_rag_agent import enhanced_rag_agent

result = await enhanced_rag_agent.query(query_text, db, session_id=session_id)
```

## Key Differences
1. **Session Support**: Enhanced agent supports session_id for memory hierarchy
2. **Multi-Tool**: Access to web scraping, calculations, etc.
3. **Better Context**: Prioritizes session-specific documents

## Benefits
- Memory hierarchy (short-term + long-term)
- Better observability
- More features
```

### Testing Requirements

```bash
# Test 1: Verify deprecation warning appears
python -c "from app.agents.rag_agent import rag_agent; print('Warning should appear above')"

# Test 2: Verify enhanced agent works
# Run existing tests for enhanced_rag_agent

# Test 3: Verify documentation updates
grep -r "rag_agent.py" docs/ | grep -v deprecated
```

### Success Criteria

- ✅ Deprecation warning added to code
- ✅ Documentation updated
- ✅ Migration guide created
- ✅ All references point to enhanced agent

---

## Phase 5: Remove Regular RAG Service

### Priority: Low
**Timeline**: After 1-2 weeks monitoring period post Phase 2+3
**Risk**: Medium (permanent removal - ensure no hidden dependencies)

### Prerequisites

Before removing `rag_service.py`:

1. ✅ Phase 2 complete (GraphQL consolidated)
2. ✅ Phase 3 complete (MCP consolidated)
3. ✅ Phase 4 complete (Simple agent deprecated)
4. ✅ 1-2 weeks of production monitoring
5. ✅ No errors related to rag_service imports
6. ✅ All tests passing

### Monitoring Period

**Duration**: 1-2 weeks after Phase 2+3

**Monitor for**:
```bash
# Check logs for any rag_service imports
docker-compose logs backend | grep "rag_service" | grep -v "enhanced"

# Check for import errors
docker-compose logs backend | grep -i "importerror.*rag_service"

# Monitor query latency (ensure no performance regression)
# Use Grafana dashboard or logs

# Check error rates
# Any increase in errors after consolidation?
```

### Files to Remove

1. **`backend/app/services/rag_service.py`** - Delete entire file

### Files to Update

#### File: `backend/app/main.py`

**Current** (Line 37):
```python
from app.services.rag_service_enhanced import enhanced_rag_service as rag_service
```

**After removal** (simplify):
```python
from app.services.rag_service_enhanced import enhanced_rag_service
```

Then update all usages from `rag_service` → `enhanced_rag_service` for clarity.

### Documentation Updates

1. **Update all references** to rag_service in documentation
2. **Remove mentions** of "two services" or "service choice"
3. **Update architecture diagrams** to show single RAG service

### Implementation Steps

1. **Final verification**:
   ```bash
   # Ensure no imports of old service
   grep -r "from app.services.rag_service import" backend/ --exclude="*enhanced*"

   # Should only show:
   # - This documentation file
   # - Any archived/deprecated files
   ```

2. **Remove the file**:
   ```bash
   # Create backup first
   cp backend/app/services/rag_service.py /tmp/rag_service.py.backup

   # Remove
   rm backend/app/services/rag_service.py
   ```

3. **Update imports** (if needed):
   ```bash
   # Search for any aliasing that can be simplified
   grep -r "enhanced_rag_service as rag_service" backend/

   # Consider simplifying to direct imports for clarity
   ```

4. **Restart and test**:
   ```bash
   docker-compose restart backend
   make test-backend
   ```

5. **Git commit**:
   ```bash
   git add backend/app/services/rag_service.py
   git commit -m "refactor: remove deprecated rag_service.py (consolidation Phase 5 complete)"
   ```

### Testing Requirements

```bash
# Test 1: Verify backend starts without errors
docker-compose restart backend
docker-compose logs backend | grep -i error

# Test 2: Run full test suite
cd backend
pytest tests/ -v

# Test 3: Test all RAG endpoints
curl -X POST "http://localhost:8000/api/v1/query" -F "query=test"
curl -X POST "http://localhost:8000/graphql" -d '{"query": "..."}'

# Test 4: Verify no import errors
python -c "from app.services.rag_service_enhanced import enhanced_rag_service; print('OK')"
```

### Rollback Plan

If issues are discovered:

```bash
# Restore from backup
cp /tmp/rag_service.py.backup backend/app/services/rag_service.py

# Restore any imports that were simplified
git revert <commit-hash>

# Restart
docker-compose restart backend
```

### Success Criteria

- ✅ Backend starts without errors
- ✅ All tests pass
- ✅ No import errors
- ✅ All RAG endpoints work
- ✅ Performance metrics unchanged
- ✅ No errors in production logs
- ✅ Documentation updated

---

## Risk Assessment

### Overall Risk: LOW ✅

| Phase | Risk Level | Impact | Rollback Difficulty |
|-------|-----------|--------|-------------------|
| Phase 2 (GraphQL) | Low | Medium | Easy (1 line change) |
| Phase 3 (MCP) | Low | Low | Easy (1 line change) |
| Phase 4 (Deprecate) | Very Low | Low | Trivial (just warnings) |
| Phase 5 (Remove) | Medium | High | Moderate (restore file) |

### Mitigation Strategies

1. **Incremental Rollout**:
   - Complete one phase at a time
   - Monitor for 24-48 hours between phases
   - Don't rush to Phase 5

2. **Testing at Each Phase**:
   - Run full test suite
   - Manual endpoint testing
   - Log monitoring

3. **Rollback Readiness**:
   - Keep backups before deletions
   - Document rollback procedures
   - Test rollback in dev environment

4. **Monitoring**:
   - Watch error rates
   - Monitor query latency
   - Check resource usage

---

## Timeline Recommendation

### Aggressive Timeline (1-2 weeks)
```
Week 1:
- Monday: Phase 2 (GraphQL) - 2 hours
- Wednesday: Phase 3 (MCP) - 2 hours
- Friday: Phase 4 (Deprecation warnings) - 1 hour

Week 2:
- Monitor production (entire week)
- Friday: Phase 5 (Remove file) - 3 hours (if monitoring looks good)
```

### Conservative Timeline (4 weeks)
```
Week 1: Phase 2 (GraphQL)
Week 2: Phase 3 (MCP) + Phase 4 (Deprecate)
Week 3-4: Monitor production extensively
Week 4 End: Phase 5 (Remove file)
```

### Recommended: Conservative Approach
- More time to catch edge cases
- Better production validation
- Lower risk

---

## Testing Strategy

### After Each Phase

1. **Unit Tests**:
   ```bash
   cd backend
   pytest tests/ -v --cov=app --cov-report=term
   ```

2. **Integration Tests**:
   ```bash
   # Test RAG query flow
   ./scripts/testing/test-integration.sh
   ```

3. **Manual Testing**:
   ```bash
   # REST API
   curl -X POST "http://localhost:8000/api/v1/query" \
     -F "query=Who is Aadhan?" \
     -F "use_cache=false"

   # GraphQL
   curl -X POST "http://localhost:8000/graphql" \
     -H "Content-Type: application/json" \
     -d '{"query": "{ documents { id filename } }"}'
   ```

4. **Log Monitoring**:
   ```bash
   # Check for errors
   docker-compose logs backend --tail=200 | grep -i error

   # Check for warnings
   docker-compose logs backend --tail=200 | grep -i warning
   ```

5. **Performance Testing**:
   ```bash
   # Measure query latency
   time curl -X POST "http://localhost:8000/api/v1/query" \
     -F "query=test query" \
     -F "use_cache=false"
   ```

### Final Validation (Before Phase 5)

Run comprehensive test suite:

```bash
# All unit tests
make test-backend

# All integration tests
./scripts/testing/test-integration.sh

# Document upload/query flow
./scripts/testing/test-document-flow.sh

# Check all imports
python -c "
from app.services.rag_service_enhanced import enhanced_rag_service
from app.agents.enhanced_rag_agent import enhanced_rag_agent
print('All imports successful')
"

# Verify no references to old service
grep -r "from app.services.rag_service import" backend/ --exclude="*enhanced*"
# Should return nothing (except archived docs)
```

---

## Success Metrics

### Phase 2 Success Metrics
- GraphQL queries respond < 2s (average)
- Error rate < 0.1%
- Memory hierarchy features work
- Session-specific queries prioritize session docs

### Phase 3 Success Metrics
- MCP integration works normally
- No increase in error rates
- Latency unchanged or improved

### Phase 4 Success Metrics
- Deprecation warnings visible in logs
- Documentation updated
- Migration guide available

### Phase 5 Success Metrics
- Zero import errors
- All tests pass (100%)
- No increase in error rates
- Performance unchanged or better
- Codebase cleaner (fewer files)

---

## Dependencies and Prerequisites

### Phase 2 Prerequisites
- ✅ Phase 1 complete (enhanced_rag_agent.py)
- ✅ Both services have identical signatures
- ✅ Backend healthy

### Phase 3 Prerequisites
- ✅ Phase 2 complete and validated
- ✅ 24-48 hours monitoring after Phase 2

### Phase 4 Prerequisites
- ✅ Phase 2 and 3 complete
- ✅ All critical paths using enhanced service

### Phase 5 Prerequisites
- ✅ Phases 2, 3, 4 complete
- ✅ 1-2 weeks production monitoring
- ✅ Zero issues discovered
- ✅ Team consensus to proceed

---

## Communication Plan

### Before Each Phase
1. **Announce in team chat**: "Starting RAG consolidation Phase X"
2. **Expected downtime**: None (rolling restart only)
3. **Rollback plan**: Document rollback steps

### During Implementation
1. **Monitor logs actively** (dedicated window)
2. **Test immediately** after deployment
3. **Report status** in team chat

### After Each Phase
1. **Success report**: "Phase X complete - all tests pass"
2. **Metrics update**: "Error rate: X%, Latency: Xms"
3. **Next steps**: "Proceeding to Phase Y in Z days"

---

## Rollback Procedures

### Phase 2 Rollback (GraphQL)
```bash
# Revert schema.py change
vim backend/app/api/graphql/schema.py
# Change line 5 back to: from app.services.rag_service import rag_service

# Restart
docker-compose restart backend

# Verify
curl http://localhost:8000/health
```

### Phase 3 Rollback (MCP)
```bash
# Revert mcp_server_service.py change
vim backend/app/services/mcp_server_service.py
# Change line 355 back to: from app.services.rag_service import rag_service

# Restart
docker-compose restart backend
```

### Phase 4 Rollback (Deprecation)
```bash
# Remove deprecation warnings
vim backend/app/agents/rag_agent.py
# Remove warning code

# Revert documentation changes
git revert <commit-hash>
```

### Phase 5 Rollback (File Removal)
```bash
# Restore from backup
cp /tmp/rag_service.py.backup backend/app/services/rag_service.py

# Restore any import changes
git revert <commit-hash>

# Restart
docker-compose restart backend

# Verify
make test-backend
```

---

## Post-Implementation Validation

### Immediate (Within 1 hour)
- ✅ All services healthy
- ✅ Basic queries work
- ✅ No errors in logs

### Short-term (24 hours)
- ✅ Error rate within normal range
- ✅ Latency within acceptable limits
- ✅ No user complaints
- ✅ All tests continue to pass

### Medium-term (1 week)
- ✅ Production metrics stable
- ✅ No edge cases discovered
- ✅ Team confident in changes

### Long-term (2+ weeks)
- ✅ Consider permanent removal (Phase 5)
- ✅ Update architecture documentation
- ✅ Close consolidation tickets

---

## References

### Related Documentation
- **Complete Analysis**: `/tmp/RAG_CONSOLIDATION_COMPLETE_ANALYSIS.md`
- **Usage Analysis**: `/tmp/RAG_SERVICE_USAGE_ANALYSIS.md`
- **Memory Hierarchy Guide**: `docs/architecture/MEMORY_HIERARCHY_GUIDE.md`
- **RAG Architecture**: `docs/evaluation/RAG_EVALUATION_ARCHITECTURE.md`

### Code Files
- Enhanced RAG Service: `backend/app/services/rag_service_enhanced.py`
- Regular RAG Service: `backend/app/services/rag_service.py` (to be removed)
- Enhanced RAG Agent: `backend/app/agents/enhanced_rag_agent.py`
- GraphQL Schema: `backend/app/api/graphql/schema.py`
- MCP Server: `backend/app/services/mcp_server_service.py`

### Git History
```bash
# View service creation history
git log --all --oneline --grep="rag_service"

# View recent changes
git log --oneline -20 backend/app/services/
```

---

## Contact and Escalation

### Questions During Implementation
- Review this document
- Check `/tmp/RAG_CONSOLIDATION_COMPLETE_ANALYSIS.md`
- Review git history for context

### If Issues Arise
1. **Stop immediately** - don't proceed to next phase
2. **Capture logs**: `docker-compose logs backend > issue_logs.txt`
3. **Check monitoring**: Grafana dashboards
4. **Rollback if needed**: Follow rollback procedures above
5. **Document issue**: Create issue in tracking system
6. **Team discussion**: Before proceeding

---

## Conclusion

This consolidation plan provides a safe, incremental path to:
1. ✅ Simplify codebase (remove redundant service)
2. ✅ Improve consistency (single RAG service)
3. ✅ Enable advanced features everywhere (memory hierarchy)
4. ✅ Reduce maintenance burden

**Recommended Approach**: Conservative timeline (4 weeks) with thorough monitoring at each phase.

**Next Step**: Proceed with **Phase 2** (GraphQL consolidation) when ready.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Status**: Ready for Phase 2 Implementation
