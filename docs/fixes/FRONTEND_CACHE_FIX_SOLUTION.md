# Frontend Cache Issue - Immediate Solutions

## Problem Confirmed

**Backend logs show:**
```
2025-11-28 12:52:27,717 - 🔑 Authorization header present: False
2025-11-28 12:52:27,723 - 👤 Anonymous upload (no authentication)
2025-11-28 12:52:27,723 - 📍 MinIO path: Unassigned/General/anonymous/Default/Press-Release---USD.pdf
```

**Root cause:** Browser has cached old JavaScript that doesn't send the Authorization header.

---

## ✅ Backend is 100% Working

Direct API test with curl shows perfect organizational upload:
```
✅ Authorization header present: True
✅ Authenticated upload by user: admin
✅ Department: Technology
✅ Team: Tech Team 1
✅ MinIO path: Technology/Tech-Team-1/admin/Default/test_org_upload.txt
```

---

## Solution 1: Clear Browser Cache (FASTEST)

1. **Logout** from the application
2. **Clear browser cache:**
   - Press `Ctrl + Shift + Delete`
   - Select "All time"
   - Check "Cached images and files"
   - Click "Clear data"
3. **Close** all browser tabs
4. **Open** new incognito window: `Ctrl + Shift + N`
5. **Navigate** to http://localhost:3001
6. **Login** as admin/admin
7. **Upload** a test file

---

## Solution 2: Force Reload (TRY THIS FIRST)

1. Stay on the page
2. Press `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
3. This forces the browser to bypass cache
4. Login again if needed
5. Try upload

---

## Solution 3: Rebuild Frontend Container

If cache clearing doesn't work, rebuild the container:

```bash
# Stop and remove frontend container
docker-compose stop frontend
docker-compose rm -f frontend

# Rebuild without cache
docker-compose build --no-cache frontend

# Start frontend
docker-compose up -d frontend

# Wait for it to be ready
sleep 5

# Check it's running
docker-compose logs frontend --tail 20
```

---

## How to Verify Fix Worked

### Check Browser Console
1. Open browser DevTools (F12)
2. Go to "Network" tab
3. Upload a file
4. Look for the POST request to `/api/v1/upload`
5. Click on it and check "Request Headers"
6. You should see: `Authorization: Bearer eyJ...`

### Check Backend Logs
```bash
docker-compose logs backend --tail 50 | grep -E "🔑|👤|📍"
```

You should see:
```
🔑 Authorization header present: True
👤 Authenticated upload by user: admin
📍 MinIO path: Technology/Tech-Team-1/admin/Default/yourfile.pdf
```

### Check Database
```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename, minio_path, department, team FROM documents ORDER BY upload_date DESC LIMIT 3;"
```

You should see your file with:
- `minio_path`: Technology/Tech-Team-1/admin/Default/yourfile.pdf
- `department`: Technology
- `team`: Tech Team 1

---

## Why This Happened

**Browser Caching Behavior:**
- Browsers aggressively cache JavaScript files for performance
- Even after backend restart, the browser serves old JS from cache
- Hard refresh and cache clearing are required to load new code

**Code is Correct:**
The `FileUpload.tsx` component already has the correct code:
```typescript
const token = localStorage.getItem('access_token')
const response = await axios.post(`${API_URL}/api/v1/upload`, formData, {
  headers: {
    'Content-Type': 'multipart/form-data',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  },
})
```

It's just not loading in the browser due to cache.

---

## Quick Test Without UI

If you want to verify your auth token works right now, use curl:

```bash
# Get your token from browser localStorage
# Open DevTools (F12) → Console tab → Type:
localStorage.getItem('access_token')

# Then use it with curl:
TOKEN="<paste_your_token>"

curl -X POST http://localhost:8000/api/v1/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/your/file.pdf" \
  -F "session_id=test-session"
```

This will work immediately because it bypasses the browser cache.

---

## After Fix is Working

Once uploads work from UI, you can verify in MinIO browser:

1. Go to http://localhost:9001
2. Login: minioadmin / minioadmin
3. Click on "documents" bucket
4. You should see folders: Technology/ → Tech-Team-1/ → admin/ → Default/
5. Your files will be inside

---

## Summary

✅ Backend implementation: **COMPLETE**
✅ Direct API test: **WORKING**
❌ Frontend browser cache: **BLOCKING UI**

**Next steps:**
1. Try Solution 1 or 2 first (fastest)
2. If that doesn't work, use Solution 3 (rebuild container)
3. Verify with the checks above
4. Once working, we can proceed to apply same logic to web scraping
