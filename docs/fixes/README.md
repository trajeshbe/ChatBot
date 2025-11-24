# Fixes Documentation

Recent fixes, issue resolutions, and troubleshooting summaries.

---

## Latest Fixes

### 2025-11-20 Session

**`FIXES_SUMMARY_2025-11-20.md`**
- **Status**: ✅ ALL ISSUES RESOLVED
- **Tests**: 8/8 passed (100% success rate)

#### Issues Fixed:
1. **HTTP 422 Error** - Ollama model pull endpoint
   - Fixed parameter naming conflict in FastAPI
   - Changed `request: PullModelRequest` to `model_name: str = Body(..., embed=True)`
   - Location: `/backend/app/api/routes/ollama_models.py:191`

2. **"Failed to load API keys" Error**
   - Added MASTER_ENCRYPTION_KEY to docker-compose.yml
   - Location: `docker-compose.yml:247`

3. **Database Error When Saving API Keys**
   - Added missing `meta_info` column (JSONB)
   - Changed `api_key_encrypted` type from bytea to TEXT
   - Restarted backend to clear cached prepared statements

4. **No Fallback When Database Fails**
   - Implemented complete fallback chain
   - Database → Environment variable
   - Comprehensive logging with emoji indicators
   - Location: `/backend/app/services/llm_service.py`

---

## Historical Fixes

For older fixes and historical issues, see root-level fix summaries:
- `FIXES_APPLIED.md`
- `ISSUES_AND_FIXES.md`
- `OLLAMA_FIX.md`
- `FRONTEND_CACHE_FIX.md`
- And more...

---

## Testing Verification

All fixes have been tested and verified:
- API keys endpoint working
- Ollama model pull successful
- Database operations functional
- Encryption/decryption working
- Fallback logic operational

See [Testing Documentation](../testing/APPLICATION_TEST_REPORT.md) for complete test results.

---

## Quick Links

- [Latest Fixes Summary](./FIXES_SUMMARY_2025-11-20.md)
- [Security Documentation](../security/)
- [Testing Reports](../testing/)
- [Back to Documentation Index](../DOCUMENTATION_INDEX.md)

---

**Last Updated**: 2025-11-24

---

## Tool Calling Model ID Fix (2025-11-24)

### TOOL_CALLING_MODEL_ID_FIX_2025-11-24.md
**Status**: ✅ ALL ISSUES RESOLVED
**Priority**: HIGH
**Impact**: Multi-Tool Agent, Web Scraping, Tool Registry

Complete fix for GPT-4 function calling parameter passing issues:

#### Issues Fixed:
1. **Smart Extraction Tool Missing model_id** - Added parameter to wrapper and JSON payload
2. **Navigation Agent Tool Missing model_id** - Added llm_provider and model_id parameters
3. **Auto-Selection Logic Override** - Changed OR to AND logic to preserve explicit parameters
4. **UltraSmartExtractor Missing model_id** - Added to extract_to_table() method signature
5. **Parameter Flow Chain** - Ensured model_id flows through all 6 layers correctly

#### Results:
- ✅ All tool calling working without errors
- ✅ Navigation agent executing successfully
- ✅ Web extraction returning actual data (20 books extracted)
- ✅ Model ID correctly flowing: `qwen2.5:1.5b-instruct-q4_K_M`
- ✅ GPT-4 tool selection working
- ✅ Cost-optimized architecture maintained (GPT-4 for selection, Ollama for execution)

**Quick Reference**: Use this for understanding the complete parameter flow fix.

---

## Tool Tracking Fixes (2025-11-23)

### TOOL_TRACKING_COMPLETE_FIX.md
Complete fix summary for tool tracking issues. Includes all 3 critical bugs found and fixed:
1. Tool selection logic (navigation vs extraction)
2. TOOL_TRACKING_ENABLED setting missing
3. Metadata JSON serialization bug (critical!)

**Quick Reference**: Use this for understanding the complete fix history.

### TOOL_TRACKING_FIXES.md
Detailed implementation guide for tool tracking fixes. Includes:
- Root cause analysis
- Code changes with line numbers
- Testing procedures
- Expected behavior after fixes

**Quick Reference**: Use this for detailed technical implementation.

### TOOL_TRACKING_SETTINGS_FIX.md
Specific fix for TOOL_TRACKING_ENABLED configuration error.
- Settings error details
- Removed feature flag requirement
- Always-on tracking with graceful failures

**Quick Reference**: Use this for understanding the settings bug.

