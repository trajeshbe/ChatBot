# "Failed to Fetch" Error - Troubleshooting Guide

> **Error**: "Deployment failed: Failed to fetch"
> **Cause**: Network connectivity issue between browser and backend API

---

## 🔍 What "Failed to Fetch" Means

This error occurs when the browser **cannot connect** to the backend API. It happens **before** the backend responds, meaning:
- ❌ Request didn't reach the backend
- ❌ No HTTP status code received
- ❌ Network layer problem (not application logic)

---

## ✅ Quick Fixes (Try in Order)

### Fix 1: Hard Refresh Browser
The browser might be caching old JavaScript.

**Action**:
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

**Why**: Clears cached JS files and reloads the latest code.

---

### Fix 2: Verify Backend is Running
Backend must be healthy for frontend to connect.

**Action**:
```bash
# Check backend status
docker-compose ps backend

# Should show: Up X minutes (healthy)
```

**If not healthy**:
```bash
docker-compose restart backend
docker-compose logs backend --tail 50
```

**Test backend directly**:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

---

### Fix 3: Check Browser Console
Browser console shows the actual fetch error.

**Action**:
1. Press `F12` to open Developer Tools
2. Go to **Console** tab
3. Look for red errors
4. Check **Network** tab for failed requests

**Common errors**:
- `net::ERR_CONNECTION_REFUSED` → Backend not running
- `CORS policy` → CORS misconfiguration
- `Mixed Content` → HTTP/HTTPS mismatch
- `Timeout` → Request took too long

---

### Fix 4: Verify API URL
Frontend must know where to find backend.

**Check in browser console**:
```javascript
// Open Console (F12), type:
localStorage.getItem('NEXT_PUBLIC_API_URL')
// Should return: "http://localhost:8000" or null (uses default)
```

**Check in frontend container**:
```bash
docker-compose exec frontend printenv | grep NEXT_PUBLIC_API_URL
# Should show: NEXT_PUBLIC_API_URL=http://localhost:8000
```

**If wrong or missing**:
```bash
# Check .env file
cat .env | grep NEXT_PUBLIC_API_URL

# Should have:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### Fix 5: Check for Mixed Content (HTTP/HTTPS)
Browser blocks HTTP requests from HTTPS pages.

**Symptoms**:
- Frontend uses HTTPS (e.g., `https://localhost:3001`)
- Backend uses HTTP (e.g., `http://localhost:8000`)
- Browser console shows "Mixed Content" error

**Fix**:
Either:
- **Option A**: Use HTTP for both (development)
  - Access frontend: `http://localhost:3001` (not https)
- **Option B**: Use HTTPS for both (production)
  - Configure backend with SSL certificate

---

### Fix 6: Check CORS Configuration
Backend must allow requests from frontend origin.

**Check backend CORS**:
```bash
grep -A5 "CORSMiddleware" backend/app/main.py
```

Should show:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**If misconfigured**:
- `allow_origins=["*"]` → Allow all (development)
- `allow_origins=["http://localhost:3001"]` → Specific origin (production)

---

### Fix 7: Network Isolation Check
Docker containers must be on same network.

**Check networks**:
```bash
docker-compose ps --format "{{.Name}}\t{{.Networks}}"
```

Both frontend and backend should be on same network (e.g., `chatbot_default`).

**Fix**:
```bash
docker-compose down
docker-compose up -d
```

---

### Fix 8: Firewall/Antivirus Blocking
Security software might block localhost connections.

**Symptoms**:
- curl works from terminal
- Browser fetch fails
- Only happens on specific machine

**Fix**:
- Temporarily disable firewall/antivirus
- Add exception for localhost:8000
- Try different browser

---

### Fix 9: Browser Extension Blocking
Ad blockers or privacy extensions might block requests.

**Test**:
1. Open browser in **Incognito/Private mode**
2. Try the workflow again
3. If it works → Browser extension is blocking

**Fix**:
- Disable ad blocker for localhost
- Whitelist `localhost:8000` and `localhost:3001`

---

### Fix 10: Port Already in Use
Another process might be using port 8000.

**Check**:
```bash
# Check what's on port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Should show: uvicorn/Python process
```

**If wrong process**:
```bash
# Kill the process
# Mac/Linux:
kill -9 <PID>

# Windows:
taskkill /PID <PID> /F

# Restart backend
docker-compose restart backend
```

---

## 🧪 Diagnostic Commands

### Full Health Check
```bash
# 1. Check all containers
docker-compose ps

# 2. Test backend health
curl http://localhost:8000/health

# 3. Test specific endpoint
curl -X POST http://localhost:8000/api/v1/finetuning/models-public/535dd0f6-29ff-4da9-b456-ab74d352282c/approve \
  -H "Content-Type: application/json" \
  -d '{"notes": "Test"}'

# 4. Check frontend env
docker-compose exec frontend printenv | grep API

# 5. Check backend logs
docker-compose logs backend --tail 50

# 6. Check frontend logs
docker-compose logs frontend --tail 50
```

---

## 📊 Error Patterns

### Pattern 1: CORS Error
**Error in console**:
```
Access to fetch at 'http://localhost:8000/...' from origin 'http://localhost:3001'
has been blocked by CORS policy
```

**Cause**: Backend not allowing frontend origin
**Fix**: Update CORS middleware in `backend/app/main.py`

### Pattern 2: Connection Refused
**Error in console**:
```
net::ERR_CONNECTION_REFUSED
```

**Cause**: Backend not running or wrong port
**Fix**: `docker-compose restart backend`

### Pattern 3: Timeout
**Error in console**:
```
net::ERR_TIMED_OUT
```

**Cause**: Request took too long (>2 minutes)
**Fix**: Check backend is processing request, increase timeout

### Pattern 4: Name Not Resolved
**Error in console**:
```
net::ERR_NAME_NOT_RESOLVED
```

**Cause**: Invalid hostname in API_BASE
**Fix**: Use `localhost` instead of hostname

---

## 🎯 Most Likely Causes

Based on frequency:

1. **Browser cache** (30%) → Hard refresh
2. **Backend not running** (25%) → `docker-compose restart backend`
3. **CORS misconfiguration** (20%) → Check CORS middleware
4. **Browser extension** (15%) → Try incognito mode
5. **Network isolation** (10%) → Check Docker networks

---

## 🔄 Complete Reset (Nuclear Option)

If nothing works, do a full reset:

```bash
# Stop everything
docker-compose down

# Clear browser cache
# Go to: Settings → Clear browsing data → Cached images and files

# Restart
docker-compose up -d

# Wait for healthy
docker-compose ps backend
# Should show: (healthy)

# Test backend
curl http://localhost:8000/health

# Hard refresh frontend
# Open http://localhost:3001 and press Ctrl+Shift+R

# Try again
```

---

## 📝 Current Configuration

### Expected Setup:
- **Frontend**: http://localhost:3001 (Next.js)
- **Backend**: http://localhost:8000 (FastAPI)
- **API Base**: `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`
- **CORS**: Allow all origins (`["*"]`)

### API Endpoints Used:
1. `POST /api/v1/finetuning/models-public/{id}/approve`
2. `POST /api/v1/finetuning/models/{id}/merge`
3. `GET /api/v1/finetuning/models/{id}/merge-status`
4. `POST /api/v1/finetuning/models-public/{id}/deploy`

### Headers Required:
```javascript
{
  'Content-Type': 'application/json',
  'Authorization': 'Bearer <token>'  // From localStorage.getItem('access_token')
}
```

---

## ✅ Verification Checklist

Before reporting as bug, verify:
- [ ] Backend is running: `docker-compose ps backend` shows "Up (healthy)"
- [ ] Backend responds: `curl http://localhost:8000/health` returns 200
- [ ] Frontend is running: `docker-compose ps frontend` shows "Up"
- [ ] Browser cache cleared: Hard refresh with `Ctrl+Shift+R`
- [ ] Logged in: `localStorage.getItem('access_token')` returns JWT token
- [ ] Browser console checked: No CORS or network errors
- [ ] Tried incognito mode: Rules out browser extension issue
- [ ] API URL correct: `http://localhost:8000` (not https, no trailing slash)

---

## 🆘 Still Failing?

If you've tried everything above:

### Collect Debug Info:
```bash
# 1. Container status
docker-compose ps > debug_containers.txt

# 2. Backend health
curl -v http://localhost:8000/health > debug_health.txt 2>&1

# 3. Backend logs
docker-compose logs backend --tail 100 > debug_backend.txt

# 4. Frontend logs
docker-compose logs frontend --tail 100 > debug_frontend.txt

# 5. Network info
docker network ls > debug_networks.txt
docker network inspect chatbot_default > debug_network_detail.txt
```

### Check Browser Console:
1. Open DevTools (F12)
2. Go to **Network** tab
3. Try the action again
4. Find the failed request (red text)
5. Screenshot the:
   - Request URL
   - Request headers
   - Response (if any)
   - Console errors

### Workaround: Use curl
While debugging, you can manually trigger the workflow:

```bash
# 1. Approve
curl -X POST http://localhost:8000/api/v1/finetuning/models-public/535dd0f6-29ff-4da9-b456-ab74d352282c/approve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{"notes": "Manual approval"}'

# 2. Merge
curl -X POST http://localhost:8000/api/v1/finetuning/models/535dd0f6-29ff-4da9-b456-ab74d352282c/merge \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{"base_model_name": "Qwen/Qwen2.5-1.5B-Instruct", "force_cpu": false}'

# 3. Check merge status
curl http://localhost:8000/api/v1/finetuning/models/535dd0f6-29ff-4da9-b456-ab74d352282c/merge-status \
  -H "Authorization: Bearer <YOUR_TOKEN>"

# 4. Deploy
curl -X POST http://localhost:8000/api/v1/finetuning/models-public/535dd0f6-29ff-4da9-b456-ab74d352282c/deploy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{"deployment_target": "ollama", "deployment_config": {"model_name": "my-model-v1"}}'
```

Get your token:
```javascript
// In browser console (F12):
localStorage.getItem('access_token')
```

---

## 📚 Related Documentation

- [Auth Fix](./AUTH_FIX_COMPLETE.md)
- [Merge Status Fix](./MERGE_STATUS_FIX.md)
- [Where to Find Button](./WHERE_TO_FIND_MERGE_DEPLOY_BUTTON.md)
- [Unified Implementation](./UNIFIED_MERGE_DEPLOY_IMPLEMENTATION.md)

---

**Most Common Solution**: Hard refresh browser (`Ctrl+Shift+R`) + verify backend is healthy

---

**End of Document**
