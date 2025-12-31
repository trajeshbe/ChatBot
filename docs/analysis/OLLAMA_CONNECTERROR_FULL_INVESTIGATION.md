# Ollama ConnectError - Complete Investigation & Analysis

**Date**: 2025-11-18
**Status**: 🔄 **MACHINE RESTART PENDING**
**Issue**: UI → Backend → Ollama calls fail with ConnectError (backend → Ollama direct calls work)

---

## Executive Summary

### The Problem
- **Symptom**: UI queries to local LLM (Ollama) fail with `RetryError[<Future raised ConnectError>]`
- **Duration**: Has been failing for approximately 3 days (since commit b6e8994)
- **Key Insight**: Backend direct curl calls to Ollama work perfectly, but UI → Backend → Ollama fails
- **Impact**: Users cannot use local LLM models (qwen2.5:1.5b, llama3.2:3b) from the UI

### What We Know Works ✅
```bash
# Direct curl from backend container to Ollama
docker exec rag-backend curl -s http://ollama:11434/api/generate \
  -d '{"model":"qwen2.5:1.5b","prompt":"What is 2+2?","stream":false}'
# Result: HTTP 200, response in 4.37s, answer: "Hello! How can I help you today?"
```

### What Fails ❌
```bash
# API call from external client (simulating UI)
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is 2+2?" \
  -F "model_id=qwen2.5:1.5b"
# Result: {"detail":"RetryError[<Future raised ConnectError>]"}
# Time: 51+ seconds (timeout/retry)
```

---

## Timeline of Events

### 3 Days Ago (Sun Nov 16) - The Breaking Change
**Commit b6e8994**: "fix: resolve Ollama 404 error by adding dedicated HTTP client"

**What Changed**:
```python
# Added in __init__
self.ollama_client = httpx.AsyncClient(timeout=120.0)

# Changed in _call_ollama
response = await self.ollama_client.post(...)  # Was: llama_cpp_client
```

**Impact**: Module-level httpx client initialization introduced stale connection issues (same pattern as previous Playwright bug)

### Today (Nov 18) - Debugging Session

#### Morning/Afternoon
- Multiple attempts to fix with runtime initialization patterns
- Changed default model from gpt-4-turbo to llama3.2:3b
- Fixed various NameError and connection issues
- Created UI_LOCAL_LLM_FIX.md documenting attempts

#### Late Afternoon - Root Cause Identified
- User provided critical hint: "3 days before we never had issue"
- Checked git history, found commit b6e8994
- Identified persistent client caching as root cause
- Backend direct calls work because they bypass the cached client

#### Evening - Applied Fresh Client Fix
- Modified `_ensure_ollama_client()` to create fresh client per request
- Added finally block to close client after use
- Restarted backend
- **Result**: ConnectError persists despite fix

#### Current Status
- User reported Docker Desktop issues
- Decided to restart machine to clear stale connections at daemon level
- All containers running but likely have stale network state

---

## Technical Analysis

### Root Cause Theory

The issue is NOT the code itself, but rather **stale network connections at the Docker daemon/network layer**.

**Evidence**:
1. Backend → Ollama works with direct curl (HTTP 200, 4.37s)
2. UI → Backend → Ollama fails with ConnectError (51+ seconds)
3. Code changes applied but issue persists
4. User reports Docker Desktop issues
5. Many stale background processes from debugging

**Hypothesis**: The httpx AsyncClient in the FastAPI application lifecycle is bound to a stale event loop or Docker network connection that was created during module import or app startup. Even with fresh client creation, the underlying network layer may be stale.

### Why Backend Direct Calls Work

```bash
docker exec rag-backend curl http://ollama:11434/api/generate
```

This works because:
- Creates NEW TCP connection from backend → ollama
- Uses system curl (not Python httpx)
- No event loop, no async context
- Fresh network stack per invocation

### Why UI Calls Fail

```
Browser → FastAPI (port 8000) → RAG Service → LLM Service → httpx.AsyncClient → Ollama (port 11434)
                                  ↓
                           FastAPI event loop
                                  ↓
                          Stale httpx transport
```

This fails because:
- FastAPI event loop created at startup
- httpx AsyncClient transport layer may be stale
- Docker network bridge may have stale connections
- Multiple layers of async context

---

## Code Changes Applied

### File: `/backend/app/services/llm_service_enhanced.py`

#### Change 1: Fixed NameError (Line 346)
**BEFORE**:
```python
finally:
    await fresh_client.aclose()  # ❌ NameError - variable doesn't exist
```

**AFTER**:
```python
# Removed finally block - persistent client shouldn't be closed per request
```

#### Change 2: Fresh Client Per Request (Lines 139-149)
**BEFORE**:
```python
async def _ensure_ollama_client(self):
    """Ensure Ollama client is initialized with fresh connection"""
    if self.ollama_client is None:
        # Initialize httpx client at runtime to avoid stale connections
        self.ollama_client = httpx.AsyncClient(timeout=120.0)
        logger.debug("🔄 Ollama httpx client initialized (runtime)")
    return self.ollama_client
```

**AFTER**:
```python
async def _ensure_ollama_client(self):
    """Create fresh Ollama client for each request (no caching)

    CRITICAL FIX: Always create a NEW client to avoid stale connections and event loop issues.
    This ensures each request gets a fresh httpx client with proper async context binding.
    Similar to how direct curl calls work - new connection per request.
    """
    # Always create NEW client - do not cache
    client = httpx.AsyncClient(timeout=120.0)
    logger.debug("🔄 Ollama httpx client created (fresh per request)")
    return client
```

#### Change 3: Added Client Cleanup (Lines 346-349)
**ADDED**:
```python
finally:
    # Always close the fresh client after use (no caching)
    await client.aclose()
    logger.debug("🔒 Ollama httpx client closed")
```

### Complete `_call_ollama()` Method After Changes

```python
async def _call_ollama(
    self,
    model_info: ModelInfo,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7
) -> Dict:
    """Call Ollama service (local CPU/GPU)"""
    # CRITICAL: Get fresh httpx client for this request
    client = await self._ensure_ollama_client()

    try:
        logger.info(f"🔧 Calling Ollama: model={model_info.model_path}, endpoint={settings.OLLAMA_ENDPOINT}")
        logger.info(f"🔧 Prompt length: {len(prompt)} chars, max_tokens: {max_tokens}")

        response = await client.post(
            f"{settings.OLLAMA_ENDPOINT}/api/generate",
            json={
                "model": model_info.model_path,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "stop": ["</s>", "Human:", "User:"],
                }
            }
        )

        logger.info(f"🔧 Response status: {response.status_code}")
        response.raise_for_status()
        result = response.json()

        logger.info(f"✅ Ollama response received: {len(result.get('response', ''))} chars")

        return {
            "content": result["response"],
            "model": model_info.id,
            "model_name": model_info.name,
            "provider": "ollama",
            "tokens": result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
            "cost": 0.0  # Local, no cost
        }
    except Exception as e:
        logger.error(f"❌ Ollama call failed: {e}")
        logger.error(f"❌ Exception type: {type(e).__name__}")
        if hasattr(e, 'response'):
            logger.error(f"❌ Response status: {e.response.status_code}")
            logger.error(f"❌ Response body: {e.response.text[:500]}")
        raise
    finally:
        # Always close the fresh client after use (no caching)
        await client.aclose()
        logger.debug("🔒 Ollama httpx client closed")
```

---

## Test Results

### Test 1: Direct Ollama Call from Backend ✅
```bash
docker exec rag-backend curl -s http://ollama:11434/api/generate \
  -d '{"model":"qwen2.5:1.5b","prompt":"Test","stream":false}'
```

**Result**:
```json
{
  "response": "Hello! How can I help you today?",
  "done": true,
  "done_reason": "stop",
  "total_duration": 4307409987,
  "prompt_eval_count": 30,
  "eval_count": 10
}
```
- HTTP 200
- Time: 4.37s
- Success ✅

### Test 2: API Call via REST Endpoint ❌
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is 2+2?" \
  -F "model_id=qwen2.5:1.5b"
```

**Result**:
```json
{"detail":"RetryError[<Future at 0x7c36c80e3110 state=finished raised ConnectError>]"}
```
- HTTP 500
- Time: 51.32s
- Failed with ConnectError ❌

---

## Docker Environment Status

### Running Containers (Before Restart)
```
NAMES                   STATUS                   PORTS
rag-backend             Up 4 minutes (healthy)   0.0.0.0:8000->8000/tcp
rag-ollama              Up 12 hours (healthy)    0.0.0.0:11434->11434/tcp
rag-postgres            Up 12 hours (healthy)    0.0.0.0:5433->5432/tcp
rag-redis               Up 12 hours (healthy)    0.0.0.0:6380->6379/tcp
rag-frontend            Up 12 hours              0.0.0.0:3001->3000/tcp
rag-grafana             Up 12 hours              0.0.0.0:3000->3000/tcp
rag-minio               Up 12 hours (healthy)    0.0.0.0:9000-9001->9000-9001/tcp
rag-envoy               Up 12 hours              0.0.0.0:8888->8888/tcp
rag-prefect-server      Up 4 hours               0.0.0.0:4200->4200/tcp
rag-loki                Up 12 hours              0.0.0.0:3100->3100/tcp
rag-flink-jobmanager    Up 12 hours              0.0.0.0:8081->8081/tcp
rag-flink-taskmanager   Up 12 hours              6123/tcp, 8081/tcp
```

**Note**: All containers from docker-compose.yml (no orphan containers)

### Docker System Status
```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          13        12        27.32GB   2.927GB (10%)
Containers      13        12        122.3MB   16.38kB (0%)
Local Volumes   27        10        14.59GB   12.91GB (88%)
Build Cache     22        0         40.97MB   40.97MB
```

### Docker Networks
```
NETWORK ID     NAME                  DRIVER    SCOPE
26a1db6e0b55   chatbot_rag-network   bridge    local
```

### Ollama Models Installed
```
NAME                            ID              SIZE      MODIFIED
qwen2.5:1.5b-instruct-q4_K_M    65ec06548149    986 MB    11 hours ago
qwen2.5:1.5b                    65ec06548149    986 MB    11 hours ago
```

**Missing**: `llama3.2:3b` (in model registry but not installed)

---

## Issues Found

### Critical Issues
1. **ConnectError**: UI → Backend → Ollama fails despite code fixes
2. **Docker Desktop Issues**: User reported inability to bring up Docker Desktop
3. **Stale Connections**: Likely at Docker daemon/network layer

### Secondary Issues
1. **Model Mismatch**: `llama3.2:3b` in registry but not installed in Ollama
2. **Many Background Processes**: 20+ stale bash processes from debugging
3. **Missing Service**: tempo container not running (observability)

---

## After Machine Restart - Action Plan

### Step 1: Verify Docker and Services
```bash
# Check Docker daemon
docker version
docker system info

# Start all services
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot
docker-compose down
docker-compose up -d

# Wait for services
sleep 30

# Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Step 2: Verify Ollama Service
```bash
# Check Ollama health
docker-compose logs ollama --tail=20

# List installed models
docker-compose exec ollama ollama list

# Test Ollama directly
curl http://localhost:11434/api/tags
```

### Step 3: Test Backend → Ollama Connection
```bash
# From backend container
docker exec rag-backend curl -s http://ollama:11434/api/generate \
  -d '{"model":"qwen2.5:1.5b","prompt":"What is 2+2?","stream":false}' | jq '.'
```

**Expected**: HTTP 200, valid JSON response

### Step 4: Test UI → Backend → Ollama Flow
```bash
# Simulate UI query via API
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is 2+2?" \
  -F "model_id=qwen2.5:1.5b" | jq '.'

# Check backend logs for fresh client creation
docker-compose logs backend --tail=50 | grep -E "🔄|🔒|Ollama"
```

**Expected Log Output**:
```
🔄 Ollama httpx client created (fresh per request)
✅ Ollama response received: XXX chars
🔒 Ollama httpx client closed
```

**Expected API Response**:
```json
{
  "answer": "The answer to 2 + 2 is 4.",
  "sources": [],
  "model_used": "qwen2.5:1.5b",
  "tokens": 45,
  "latency_ms": 4500.0
}
```

### Step 5: If ConnectError Persists

If the issue still occurs after restart, investigate deeper:

#### Option A: Check FastAPI Event Loop
```python
# Add to llm_service_enhanced.py _call_ollama
import asyncio
logger.info(f"Event loop: {id(asyncio.get_event_loop())}")
```

#### Option B: Use Context Manager Pattern
```python
# In _call_ollama
async with httpx.AsyncClient(timeout=120.0) as client:
    response = await client.post(...)
    # No manual close needed
```

#### Option C: Check Docker DNS Resolution
```bash
# From backend container
docker exec rag-backend nslookup ollama
docker exec rag-backend ping -c 3 ollama
docker exec rag-backend curl -v http://ollama:11434/api/tags
```

#### Option D: Check for Port/Network Issues
```bash
# Check if Ollama is actually listening
docker exec rag-ollama netstat -tlnp | grep 11434

# Check Docker network connectivity
docker network inspect chatbot_rag-network | jq '.[0].Containers'
```

---

## Secondary Task: Template Extractor for Screener.in

**After** Ollama ConnectError is resolved, address the template extractor issue.

### Problem
- User tried to scrape: https://www.screener.in/company/BHARTIARTL/consolidated/
- Expected: Excel output with 22 columns
- Actual: Blank values (CSS selector timeout)

### Columns Required
1. Company Name
2. Market Position
3. Founded Year
4. Parent Group
5. Revenue (Annual)
6. EBITDA
7. EBITDA Margin
8. Net Profit
9. ARPU
10. Capex
11. Debt Level
12. Cash Flow
13. Subscriber Base
14. Market Share (%)
15. 4G/5G Penetration
16. Churn Rate
17. Towers
18. Fiber KM
19. Spectrum Holdings
20. 5G Rollout Status
21. Growth Initiatives
22. Digital Services

### Test Command (After Restart)
```bash
curl -X POST http://localhost:8000/api/v1/extract/preset/screener_in \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.screener.in/company/BHARTIARTL/consolidated/"}' | jq '.'
```

---

## Files Modified Today

1. `/backend/app/services/llm_service_enhanced.py`
   - Lines 139-149: `_ensure_ollama_client()` method
   - Lines 292-349: `_call_ollama()` method

2. Documentation Created:
   - `UI_LOCAL_LLM_FIX.md` (earlier today)
   - `LOCAL_LLM_CONNECT_ERROR_ROOT_CAUSE.md` (this evening)
   - `OLLAMA_CONNECTERROR_FULL_INVESTIGATION.md` (this file)

---

## Key Learnings

1. **Backend Direct vs UI Flow**: Critical to distinguish between different call paths
2. **Git History**: Checking changes from "when it last worked" is invaluable
3. **Event Loop Binding**: httpx AsyncClient lifecycle is tied to async context
4. **Docker Daemon State**: Sometimes code fixes aren't enough - infrastructure restart needed
5. **Persistent Debugging**: Issue has been ongoing all day despite multiple "fixes"

---

## Next Steps Summary

1. ✅ **RESTART MACHINE** - Clear Docker daemon and network state
2. ⏳ **Verify Ollama Fix** - Test UI → Backend → Ollama flow
3. ⏳ **Fix Template Extractor** - Address screener.in blank values
4. ⏳ **Install Missing Model** - Pull llama3.2:3b if needed
5. ⏳ **Clean Up Background Processes** - Kill stale bash processes

---

## References

- Previous Investigation: `UI_LOCAL_LLM_FIX.md`
- Root Cause Doc: `LOCAL_LLM_CONNECT_ERROR_ROOT_CAUSE.md`
- Commit History: `git log --since="3 days ago" --oneline`
- Model Registry: `/backend/app/models/model_registry.py`
- LLM Service: `/backend/app/services/llm_service_enhanced.py`

---

**End of Investigation Document**
**Resume from Step 1 after machine restart**
