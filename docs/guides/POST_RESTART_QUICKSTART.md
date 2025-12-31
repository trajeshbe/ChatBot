# Post-Restart Quick Start Guide

**Date**: 2025-11-18
**Purpose**: Fast track to testing after machine restart

---

## Quick Test Commands

### 1. Start Services (2 minutes)
```bash
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot
docker-compose down
docker-compose up -d
sleep 30
docker ps
```

### 2. Test Ollama from Backend (30 seconds)
```bash
# Should return HTTP 200 with model info
curl http://localhost:11434/api/tags | jq '.models[].name'

# Should return "Hello! How can I help you today?"
docker exec rag-backend curl -s http://ollama:11434/api/generate \
  -d '{"model":"qwen2.5:1.5b","prompt":"Test","stream":false}' | jq '.response'
```

### 3. Test UI → Backend → Ollama (CRITICAL TEST)
```bash
# This is what's been failing
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is 2+2?" \
  -F "model_id=qwen2.5:1.5b" | jq '.'
```

**Expected Success**:
```json
{
  "answer": "The answer to 2 + 2 is 4.",
  "sources": [],
  "model_used": "qwen2.5:1.5b",
  "tokens": 45,
  "latency_ms": 4500.0
}
```

**If Still Fails**:
```json
{"detail":"RetryError[<Future raised ConnectError>]"}
```

### 4. Check Backend Logs
```bash
# Should see fresh client creation
docker-compose logs backend --tail=30 | grep -E "🔄|🔒|Ollama|ConnectError"
```

**Expected**:
```
🔄 Ollama httpx client created (fresh per request)
✅ Ollama response received: XXX chars
🔒 Ollama httpx client closed
```

---

## If ConnectError Persists

### Investigate Event Loop
```bash
# Check for event loop mismatch
docker-compose logs backend | grep -i "event\|loop\|async" | tail -20
```

### Investigate Docker Network
```bash
# Verify backend can reach ollama
docker exec rag-backend ping -c 3 ollama
docker exec rag-backend nslookup ollama

# Check network configuration
docker network inspect chatbot_rag-network | jq '.[0].Containers | to_entries[] | {name: .value.Name, ipv4: .value.IPv4Address}'
```

### Alternative Fix: Context Manager Pattern
If fresh client per request still fails, try context manager:

**File**: `/backend/app/services/llm_service_enhanced.py`
**Method**: `_call_ollama()`

```python
async def _call_ollama(...) -> Dict:
    """Call Ollama service (local CPU/GPU)"""
    # Use context manager instead of manual client management
    async with httpx.AsyncClient(timeout=120.0) as client:
        logger.info(f"🔧 Calling Ollama: model={model_info.model_path}")

        response = await client.post(
            f"{settings.OLLAMA_ENDPOINT}/api/generate",
            json={...}
        )
        response.raise_for_status()
        result = response.json()

        return {
            "content": result["response"],
            "model": model_info.id,
            ...
        }
```

Then restart: `docker-compose restart backend`

---

## Secondary Task: Template Extractor

**After** Ollama is working, test template extraction:

```bash
curl -X POST http://localhost:8000/api/v1/extract/preset/screener_in \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.screener.in/company/BHARTIARTL/consolidated/"}' | jq '.'
```

**Expected**: Excel file with 22 columns populated

---

## Files to Reference

1. **Full Investigation**: `OLLAMA_CONNECTERROR_FULL_INVESTIGATION.md`
2. **Root Cause Doc**: `LOCAL_LLM_CONNECT_ERROR_ROOT_CAUSE.md`
3. **Code Changes**: `/backend/app/services/llm_service_enhanced.py` (lines 139-149, 292-349)

---

## Contact Points

All analysis saved in repository. Resume from here after restart.
