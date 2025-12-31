# Chat UI Stuck on "Processing..." - Debug Guide

> **Issue**: Chat shows "Processing..." but no response appears
> **Last Updated**: 2025-12-22

---

## 🔍 What "Processing..." Means

When you see "Processing..." in the chat UI, this is what should be happening:

1. **Frontend sends query** to backend API (`POST /api/v1/query`)
2. **Backend processes**:
   - Check if RAG mode is enabled
   - Search for relevant documents (if RAG)
   - Call Ollama/OpenAI to generate response
   - Stream response back to frontend
3. **Frontend displays** streaming response token by token

If it's stuck on "Processing...", one of these steps is failing.

---

## 🐛 Common Causes & Fixes

### Cause 1: Frontend Not Sending Request (Most Common)

**Symptoms**:
- UI shows "Processing..."
- No requests in backend logs
- No requests in Ollama logs

**Debug**:
1. **Open Browser Developer Tools**: Press `F12`
2. **Go to Console tab**: Look for red errors
3. **Go to Network tab**:
   - Filter by "XHR" or "Fetch"
   - Look for `/api/v1/query` request
   - Check if request was sent

**Common JavaScript Errors**:
- `Cannot read property 'value' of null` → Model dropdown not loaded
- `Fetch failed` → Backend not reachable
- `CORS error` → CORS misconfiguration
- `401 Unauthorized` → Not logged in

**Fix**:
- **Hard refresh browser**: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- **Clear browser cache**: Settings → Clear browsing data
- **Check if logged in**: Look for username in UI, or login again
- **Verify model selected**: Check dropdown shows a model name

---

### Cause 2: Model Not Loaded in Ollama

**Symptoms**:
- Request reaches backend (shows in logs)
- Backend tries to call Ollama
- Ollama fails because model not found
- Frontend never gets response

**Debug**:
```bash
# Check available models
curl -s http://localhost:11434/api/tags | jq -r '.models[] | .name'
```

Should show:
- `qwen2.5:1.5b-instruct-q4_K_M`
- `qwen2.5:1.5b`
- etc.

**Check backend logs**:
```bash
docker-compose logs backend --tail 50 | grep -i "model not found\|ollama"
```

**Fix**:
```bash
# Pull the model
docker-compose exec ollama ollama pull qwen2.5:1.5b

# Restart Ollama
docker-compose restart ollama
```

---

### Cause 3: Ollama Taking Too Long (Timeout)

**Symptoms**:
- Request reaches Ollama
- Ollama generating response (slow on CPU)
- Frontend times out waiting

**Debug**:
```bash
# Check if Ollama is processing
docker-compose exec ollama ps aux | grep ollama

# Check GPU usage (if available)
nvidia-smi

# Check Ollama logs for generation
docker-compose logs ollama --tail 100 | grep -i "generating\|POST /api"
```

**Fix**:
- **Wait longer**: CPU generation can take 1-5 minutes for first response
- **Use smaller model**: Select `qwen2.5:1.5b` instead of larger models
- **Enable GPU**: If you have GPU, make sure Ollama can access it

---

### Cause 4: Backend Crashed or Stuck

**Symptoms**:
- Request sent from frontend
- Backend logs stop
- No response

**Debug**:
```bash
# Check backend status
docker-compose ps backend

# Should show "Up (healthy)"
# If shows "Restarting" or "Exited" → Backend crashed

# Check backend logs for errors
docker-compose logs backend --tail 100
```

Look for:
- `CUDA out of memory` → GPU OOM
- `Connection refused` → Can't connect to Ollama/PostgreSQL
- `Traceback` → Python exception

**Fix**:
```bash
# Restart backend
docker-compose restart backend

# Wait for healthy
docker-compose ps backend

# Should show (healthy) status
```

---

### Cause 5: RAG Query Slow (Document Search)

**Symptoms**:
- Using RAG mode
- Large document collection
- Query takes long time to search

**Debug**:
```bash
# Check how many documents/chunks
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM document_chunks;
"

# Check if vector index exists
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT indexname FROM pg_indexes WHERE tablename = 'document_chunks';
"
```

**Fix**:
- **Use session scope**: Upload fewer documents per session
- **Rebuild vector index**:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_chunks_embedding
  ON document_chunks USING ivfflat (embedding vector_cosine_ops);
  ```
- **Disable RAG temporarily**: Test with RAG off to see if it's faster

---

## 🧪 Step-by-Step Debugging

### Step 1: Check Browser Console

1. Open http://localhost:3001
2. Press `F12` to open Developer Tools
3. Go to **Console** tab
4. Type your question and press Send
5. **Look for errors** in console

**What to look for**:
- Red error messages
- Failed fetch requests
- JavaScript exceptions

---

### Step 2: Check Network Tab

1. In Developer Tools, go to **Network** tab
2. Type your question and press Send
3. Look for `/api/v1/query` request
4. Click on it to see details:
   - **Request**: Check payload (query text, session_id, etc.)
   - **Response**: Check if response received
   - **Status**: Should be 200 (OK)

**Common statuses**:
- `200 OK` → Request succeeded
- `401 Unauthorized` → Not logged in
- `404 Not Found` → Endpoint doesn't exist
- `500 Internal Server Error` → Backend error
- `(pending)` → Still waiting for response
- `(failed)` → Network error

---

### Step 3: Check Backend Logs Live

Open a terminal and run:
```bash
# Follow backend logs in real-time
docker-compose logs -f backend
```

Then in browser, send your question and watch the logs.

**What to look for**:
- `POST /api/v1/query` → Request received
- `Generating response` → Calling LLM
- `200 OK` → Response sent
- Any `ERROR` or `Traceback` lines

---

### Step 4: Test Ollama Directly

Bypass frontend/backend and test Ollama:

```bash
# Test if Ollama responds
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:1.5b",
  "prompt": "Hello, how are you?",
  "stream": false
}' | jq .

# Should return JSON with "response" field
```

If this works, Ollama is fine. Problem is in frontend or backend.

If this fails:
- Ollama not running
- Model not loaded
- Ollama crashed

---

### Step 5: Check All Services

```bash
# Check all container status
docker-compose ps

# All should show "Up"
# Backend should show "(healthy)"
```

If any service is down:
```bash
docker-compose restart <service-name>
```

---

## 🎯 Quick Fixes (Try These First)

### Fix 1: Hard Refresh Browser
**Most common fix** - clears cached JavaScript:
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

### Fix 2: Restart Backend
```bash
docker-compose restart backend
docker-compose logs backend --tail 20
```

### Fix 3: Restart Frontend
```bash
docker-compose restart frontend
```

### Fix 4: Check Model Selected
- Make sure a model is selected in the dropdown
- Try selecting a different model

### Fix 5: Try Direct Ollama Test
```bash
# Verify Ollama works
curl http://localhost:11434/api/tags

# Should list models
```

---

## 📊 What Should Be Happening

### Successful Query Flow:

```
User types question
    ↓
Frontend sends POST /api/v1/query
    ↓
Backend receives request (logs: "POST /api/v1/query")
    ↓
Backend searches documents (if RAG enabled)
    ↓
Backend calls Ollama /api/generate
    ↓
Ollama generates response (takes 10-60 seconds)
    ↓
Backend streams response to frontend
    ↓
Frontend displays response token by token
    ↓
Response complete, "Processing..." disappears
```

### Backend Logs (Successful):
```
INFO: POST /api/v1/query
INFO: Received query: "What products does Choles offer?"
INFO: Session ID: abc-123-def
INFO: RAG enabled: True
INFO: Searching documents...
INFO: Found 5 relevant chunks
INFO: Generating response with model: qwen2.5:1.5b
INFO: Calling Ollama...
INFO: Streaming response...
INFO: Response complete (tokens: 150, time: 15.2s)
INFO: 200 OK
```

### Ollama Logs (Successful):
```
[GIN] POST /api/generate
[Generating response...]
[GIN] 200 | 15.234s
```

---

## 🔍 Advanced Debugging

### Check Database Connection
```bash
docker-compose exec postgres pg_isready
# Should return: accepting connections
```

### Check Redis Connection
```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Check Backend Health
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Check Backend Can Reach Ollama
```bash
docker-compose exec backend curl http://ollama:11434/api/tags
# Should return JSON with models list
```

---

## 🆘 Still Stuck?

If "Processing..." persists after trying all fixes:

### Collect Debug Info:

1. **Browser Console Screenshot**:
   - F12 → Console tab → Screenshot errors

2. **Network Tab Screenshot**:
   - F12 → Network tab → Find `/api/v1/query` → Screenshot

3. **Backend Logs**:
   ```bash
   docker-compose logs backend --tail 100 > backend_logs.txt
   ```

4. **Ollama Logs**:
   ```bash
   docker-compose logs ollama --tail 50 > ollama_logs.txt
   ```

5. **Container Status**:
   ```bash
   docker-compose ps > container_status.txt
   ```

### Try Workaround (API Test):

Skip the UI and test backend directly:
```bash
# Test query endpoint
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "query": "What products does Choles offer?",
    "session_id": "test-session-123",
    "model_name": "qwen2.5:1.5b",
    "use_rag": false
  }'
```

If this works, problem is in frontend. If this fails, problem is in backend.

---

## 📋 Checklist

Before reporting as bug:

- [ ] Hard refreshed browser (`Ctrl+Shift+R`)
- [ ] Checked browser console for errors (F12)
- [ ] Checked network tab shows request sent
- [ ] Verified backend is running: `docker-compose ps backend`
- [ ] Verified Ollama is running: `curl http://localhost:11434/api/tags`
- [ ] Checked backend logs: `docker-compose logs backend --tail 50`
- [ ] Verified model exists in Ollama
- [ ] Tried different model in dropdown
- [ ] Checked if logged in (see username in UI)
- [ ] Waited at least 2 minutes (CPU generation is slow)

---

## 💡 Prevention Tips

To avoid "Processing..." getting stuck:

1. **Use GPU if available**: Much faster generation
2. **Use smaller models**: `qwen2.5:1.5b` instead of 7B+ models
3. **Disable RAG for testing**: Faster responses
4. **Keep session documents small**: <10 files per session
5. **Restart services daily**: Prevents memory leaks
6. **Monitor logs**: Watch for errors before they become problems

---

**Most Common Solution**: Hard refresh browser + verify model loaded in Ollama

**Test URL**: http://localhost:3001

---

**End of Document**
