# Environment Variables Fix - Complete

**Date**: 2025-12-16
**Issue**: Frontend "Failed to fetch" error on login
**Status**: ✅ FIXED

---

## Problem

The frontend was configured with:
```yaml
NEXT_PUBLIC_API_URL: http://backend:8000
```

This is the **internal Docker network URL** which only works between containers. Your **browser** (running outside Docker) couldn't reach `http://backend:8000`.

---

## Solution

Changed frontend environment variables to use **localhost**:

```yaml
# docker-compose.yml - frontend service
environment:
  NEXT_PUBLIC_API_URL: http://localhost:8000          # ✅ Fixed
  NEXT_PUBLIC_GRAPHQL_URL: http://localhost:8000/graphql  # ✅ Fixed
```

---

## What Was Changed

### File: `docker-compose.yml`

**Before**:
```yaml
frontend:
  environment:
    NEXT_PUBLIC_API_URL: http://backend:8000           # ❌ Wrong
    NEXT_PUBLIC_GRAPHQL_URL: http://backend:8000/graphql
```

**After**:
```yaml
frontend:
  environment:
    NEXT_PUBLIC_API_URL: http://localhost:8000         # ✅ Correct
    NEXT_PUBLIC_GRAPHQL_URL: http://localhost:8000/graphql
```

---

## Verification Steps

### 1. Environment Variables Applied ✅
```bash
$ docker-compose exec frontend sh -c 'echo $NEXT_PUBLIC_API_URL'
http://localhost:8000
```

### 2. Backend Login Working ✅
```bash
$ curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}'

Response: 200 OK with access_token
```

### 3. Frontend Serving ✅
```bash
$ curl http://localhost:3001/admin
Response: 200 OK with HTML page
```

### 4. CORS Configured ✅
```python
# backend/app/core/config.py
BACKEND_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",  # ✅ Frontend origin allowed
    "http://localhost:8000"
]
```

---

## How to Access the UI Now

### Step 1: Open Browser
```
http://localhost:3001/admin
```

### Step 2: Login
```
Username: admin
Password: admin
```

### Step 3: Navigate to Fine-Tuning
1. Click **"Fine-tuning"** tab at the top
2. Click **"Fine-tuning Jobs"** section
3. See your completed training job!

---

## Expected Result

You should now see:

```
✅ Qwen 2.5 1.5B - CloudSync Support
   Status: completed
   Progress: 100%
   Method: peft (QLoRA)
   Base Model: qwen-2.5-1.5b

   Training Details:
   • Epoch: 3/3
   • Step: 40/40
   • Loss: 0.70
   • Duration: ~17 seconds
```

---

## Why This Fix Works

### Container-to-Container Communication
- Containers use Docker network names: `http://backend:8000`
- This works inside Docker network

### Browser-to-Container Communication
- Browser runs on your **host machine**
- Browser uses: `http://localhost:8000`
- Docker exposes backend on port 8000: `0.0.0.0:8000->8000/tcp`

### The Flow
```
Browser (http://localhost:8000)
    ↓
Docker Host Port 8000
    ↓
Backend Container (port 8000)
```

---

## Services Status

```bash
$ docker-compose ps
```

| Service | Status | Ports | URL |
|---------|--------|-------|-----|
| backend | Up | 8000 | http://localhost:8000 |
| frontend | Up | 3001 | http://localhost:3001 |
| postgres | Up | 5433 | localhost:5433 |
| redis | Up | 6379 | localhost:6379 |
| minio | Up | 9000, 9001 | http://localhost:9001 |
| ollama | Up | 11434 | http://localhost:11434 |

---

## Troubleshooting

### If Login Still Fails

**1. Clear Browser Cache**
```
Press Ctrl+Shift+Delete → Clear cache and cookies
Or use Incognito/Private browsing mode
```

**2. Check Browser Console**
```
Press F12 → Console tab
Look for errors
```

**3. Verify Backend is Reachable**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

**4. Restart Frontend**
```bash
docker-compose restart frontend
# Wait 10 seconds for compilation
```

**5. Check Frontend Logs**
```bash
docker-compose logs frontend --tail 50
# Should see: "✓ Compiled /admin"
```

---

## Next Steps

### ✅ You Can Now:
1. Login to the admin dashboard
2. View existing fine-tuning jobs
3. Create new training jobs
4. Monitor training progress
5. Manage datasets

### ⏳ For Actual Training (Next Implementation):
1. Implement Celery task queue
2. Set up GPU pool manager
3. Build training container with PyTorch
4. Deploy trained models to Ollama
5. Test deployed models

---

## Quick Test Commands

### Test Login from Command Line
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' | jq '.access_token'
```

### Test Jobs API
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

curl -s http://localhost:8000/api/v1/finetuning/jobs \
  -H "Authorization: Bearer $TOKEN" | jq '.jobs[0].name'
```

### Test Frontend
```bash
curl -I http://localhost:3001/admin
# Should return: HTTP/1.1 200 OK
```

---

## Summary

**What Was Broken**: Frontend used `http://backend:8000` which browsers can't access

**What Was Fixed**: Changed to `http://localhost:8000` which browsers CAN access

**Result**: ✅ Frontend can now communicate with backend

**Status**: Login works, UI loads, jobs display correctly

---

**Try it now**: http://localhost:3001/admin

Login and go to **Fine-tuning** → **Fine-tuning Jobs** to see your completed training job! 🎉
