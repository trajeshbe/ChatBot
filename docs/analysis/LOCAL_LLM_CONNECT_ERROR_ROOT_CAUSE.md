# Local LLM ConnectError - Root Cause Investigation

**Date**: 2025-11-18
**Issue**: ConnectError when calling Ollama from UI (but direct backend calls work)
**Status**: 🔍 **INVESTIGATING**

---

## Key Findings

### 1. Backend Direct Calls Work ✅

```bash
# Direct curl from backend container works perfectly:
docker exec rag-backend curl -s http://ollama:11434/api/generate \
  -d '{"model":"qwen2.5:1.5b","prompt":"What is 2+2?","stream":false}'
# Result: {"response": "The answer to 2 + 2 is 4."}
```

### 2. UI Calls Fail with ConnectError ❌

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is 2+2?" \
  -F "model_id=qwen2.5:1.5b"
# Result: {"detail":"RetryError[<Future raised ConnectError>]"}
```

###  3. Timeline - What Changed 3 Days Ago

**Commit b6e8994** (Sun Nov 16, 3 days ago):
- Added `self.ollama_client = httpx.AsyncClient(timeout=120.0)` in `__init__`
- Changed from `llama_cpp_client` to `ollama_client` in `_call_ollama`
- **This introduced module-level httpx client initialization**

**The Problem**: Module-level init creates stale connections (same as Playwright issue)

### 4. Current Code State

**File**: `backend/app/services/llm_service_enhanced.py`

**Lines 38-41 (__init__)**:
```python
# HTTP clients for local models (lazy initialization to avoid stale connections)
self.vllm_client = None
self.ollama_client = None  # ✅ Correct - set to None
self.llama_cpp_client = None
```

**Lines ~30-38 (_ensure_ollama_client)**:
```python
async def _ensure_ollama_client(self):
    """Ensure Ollama client is initialized with fresh connection"""
    if self.ollama_client is None:
        # CRITICAL: Initialize httpx client at runtime to avoid stale connections
        self.ollama_client = httpx.AsyncClient(timeout=120.0)
        logger.debug("🔄 Ollama httpx client initialized (runtime)")
    return self.ollama_client
```

**Lines ~292-343 (_call_ollama)**:
```python
async def _call_ollama(...)  -> Dict:
    """Call Ollama service (local CPU/GPU)"""
    # CRITICAL: Ensure fresh httpx client (runtime initialization)
    client = await self._ensure_ollama_client()  # ✅ Correct pattern

    try:
        response = await client.post(
            f"{settings.OLLAMA_ENDPOINT}/api/generate",
            json={...}
        )
        response.raise_for_status()
        result = response.json()
        return {...}
    except Exception as e:
        logger.error(f"❌ Ollama call failed: {e}")
        raise
# Removed finally block (was trying to close non-existent variable)
```

### 5. NameError Fix Applied ✅

**Previous Bug** (line 346):
```python
finally:
    await fresh_client.aclose()  # ❌ NameError - variable doesn't exist
```

**Fixed** (today):
- Removed the finally block entirely
- Reason: `self.ollama_client` is persistent, should NOT be closed per request

---

## Hypothesis: Why Backend Works But UI Doesn't

### Theory 1: Event Loop / Async Context Issue

**Backend direct call**:
- Simple curl → Ollama (synchronous, no event loop)
- Works every time ✅

**UI call through FastAPI**:
- Browser → FastAPI → RAG Service → LLM Service → Ollama
- Uses async/await throughout
- httpx AsyncClient may not be properly initialized in the FastAPI event loop context
- **ConnectError may be due to httpx client lifecycle in async context**

### Theory 2: Request Lifecycle Issue

The `_ensure_ollama_client()` pattern creates the client ONCE and reuses it:

```python
# First UI request:
if self.ollama_client is None:  # True
    self.ollama_client = httpx.AsyncClient(timeout=120.0)  # Creates client
return self.ollama_client

# Second UI request:
if self.ollama_client is None:  # False (client already exists)
return self.ollama_client  # Reuses SAME client
```

**Problem**: If the first client creation happened during module import or FastAPI startup, the httpx transport layer may have stale connections or event loop mismatch.

### Theory 3: FastAPI Lifespan vs Request Lifecycle

**Current initialization**:
- `llm_service = EnhancedLLMService()` - Module-level singleton (line ~521)
- `await llm_service.initialize()` - Called in lifespan (lines 104-108 in main_enhanced.py)
- BUT `ollama_client` is NOT created until FIRST request calls `_ensure_ollama_client()`

**Potential Issue**:
- The client is created in a request-handling async context
- But the event loop may be different or the transport may not be properly initialized

---

## Proposed Fixes

### Fix Option 1: Create Fresh Client Per Request (Most Reliable)

**Change `_ensure_ollama_client()` to always create fresh client**:

```python
async def _ensure_ollama_client(self):
    """Create fresh Ollama client for each request (no caching)"""
    # Always create NEW client to avoid stale connections
    client = httpx.AsyncClient(timeout=120.0)
    logger.debug("🔄 Ollama httpx client created (fresh per request)")
    return client
```

**Change `_call_ollama()` to close client after use**:

```python
async def _call_ollama(...) -> Dict:
    """Call Ollama service (local CPU/GPU)"""
    client = await self._ensure_ollama_client()  # Fresh client

    try:
        response = await client.post(...)
        response.raise_for_status()
        result = response.json()
        return {...}
    finally:
        await client.aclose()  # ✅ Close fresh client after use
```

**Pros**:
- Guarantees no stale connections
- Each request gets a fresh httpx client with proper event loop binding
- Similar to how curl works (new connection per request)

**Cons**:
- Slightly more overhead (client creation per request)
- But Ollama is local, so overhead is minimal

### Fix Option 2: Initialize Client in Lifespan

**Modify `main_enhanced.py` lifespan to explicitly create Ollama client**:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    try:
        # Initialize LLM service
        await llm_service.initialize()

        # CRITICAL: Explicitly create Ollama client in lifespan event loop
        if llm_service.ollama_client is None:
            llm_service.ollama_client = httpx.AsyncClient(timeout=120.0)
            logger.info("✅ Ollama client created in lifespan")

        yield
    finally:
        await llm_service.close()
```

**Pros**:
- Client created ONCE in main event loop
- Reused across requests

**Cons**:
- May still have event loop binding issues
- Still using persistent client (potential for stale connections)

### Fix Option 3: Use httpx.AsyncClient as Context Manager

**Modify `_call_ollama()` to use context manager pattern**:

```python
async def _call_ollama(...) -> Dict:
    """Call Ollama service (local CPU/GPU)"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(...)
        response.raise_for_status()
        result = response.json()
        return {...}
```

**Pros**:
- Cleanest pattern for httpx
- Automatic resource cleanup
- Fresh client per request

**Cons**:
- Doesn't use `_ensure_ollama_client()` anymore

---

## Recommended Action

**Try Fix Option 1 first** (fresh client per request) - most reliable and mirrors the working curl behavior.

If that doesn't work, then the issue may be deeper (Docker networking, DNS resolution, etc.).

---

## Testing Plan

1. Apply Fix Option 1
2. Restart backend: `docker-compose restart backend`
3. Test from UI: Select qwen2.5:1.5b, send query
4. Test from curl: `curl -X POST http://localhost:8000/api/v1/query -F "query=test" -F "model_id=qwen2.5:1.5b"`
5. Check backend logs for "🔄 Ollama httpx client created (fresh per request)"
6. Verify NO ConnectError

---

## Files to Modify

1. `/backend/app/services/llm_service_enhanced.py`:
   - `_ensure_ollama_client()` method
   - `_call_ollama()` method

---

## Next Steps

Apply Fix Option 1 and test.
