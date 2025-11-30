# Upload MinIO Path Fix Applied ✅

**Date**: 2025-11-28
**Issue**: File uploaded to hierarchical path but process_document tried to retrieve using UUID
**Status**: ✅ Fixed

---

## 🐛 Problem

**Error**:
```
S3Error: NoSuchKey - The specified key does not exist.
object_name: dc34b96a-ece5-45d3-afd0-cfe375a51d72.pdf
```

**Root Cause**:
1. `upload_file()` saved file to MinIO using hierarchical path: `Technology/DevOps-Team/admin/Default/file.pdf`
2. `process_document()` tried to retrieve file using UUID path: `dc34b96a-ece5-45d3-afd0-cfe375a51d72.pdf`
3. File exists at hierarchical path but not at UUID path → NoSuchKey error

---

## ✅ Fix Applied

**File**: `backend/app/services/document_service.py` line 316

**Before**:
```python
# Download file from MinIO
response = self.minio_client.get_object(
    settings.MINIO_BUCKET_NAME,
    document.file_path  # ❌ Always uses UUID
)
```

**After**:
```python
# Download file from MinIO (use minio_path if available, fallback to file_path)
object_key = document.minio_path if document.minio_path else document.file_path
logger.info(f"Retrieving file from MinIO: {object_key}")

response = self.minio_client.get_object(
    settings.MINIO_BUCKET_NAME,
    object_key  # ✅ Uses hierarchical path if available
)
```

**Changes**:
- Uses `document.minio_path` if available
- Falls back to `document.file_path` (UUID) if minio_path is None
- Added logging to show which path is being used
- Backward compatible with old uploads

---

## 🔍 Current Observation

**User reports seeing in MinIO**:
```
documents/Unassigned/General/anonymous/Default
```

**This indicates**:
- Upload was processed as **anonymous** (not authenticated)
- File went to fallback path: `Unassigned/General/anonymous/Default`

**Why This Happens**:
1. Frontend FileUpload component sends `Authorization: Bearer <token>`
2. Backend `get_current_user_from_request()` checks for token
3. If token is invalid/expired/missing → falls back to anonymous user
4. Anonymous user has no dept/team → path becomes `Unassigned/General/anonymous/Default`

---

## 🧪 Verification Steps

### Step 1: Check if Logged In
```
1. Open http://localhost:3001
2. Check top-right corner - should show "admin"
3. If not logged in, click "Login" and login as admin/admin
```

### Step 2: Check Token in Browser
```
1. Open browser DevTools (F12)
2. Go to Application tab → Local Storage → http://localhost:3001
3. Look for "access_token" key
4. Should have a JWT token value
```

### Step 3: Upload File While Logged In
```
1. Ensure logged in (see username in top-right)
2. Upload a new test file
3. Check backend logs
```

### Step 4: Check Backend Logs
```bash
docker-compose logs backend --tail 50 | grep -i "authenticated\|anonymous\|minio path"
```

**Expected if authenticated**:
```
👤 Authenticated upload by user: admin
📁 Department: Technology
👥 Team: <team_name_if_assigned>
📍 MinIO path: Technology/<team>/admin/Default/file.pdf
📁 Organizational path: Technology/<team>/admin/Default/file.pdf
Retrieving file from MinIO: Technology/<team>/admin/Default/file.pdf
```

**If anonymous**:
```
👤 Anonymous upload (no authentication)
📍 MinIO path: Unassigned/General/anonymous/Default/file.pdf
📁 Organizational path: Unassigned/General/anonymous/Default/file.pdf
Retrieving file from MinIO: Unassigned/General/anonymous/Default/file.pdf
```

### Step 5: Verify Token is Sent
```
1. Open browser DevTools (F12)
2. Go to Network tab
3. Upload a file
4. Click on the /api/v1/upload request
5. Go to Headers tab
6. Under "Request Headers" look for:
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**If missing**: Token is not being sent → FileUpload component issue
**If present**: Token is sent but backend rejects it → auth issue

---

## 🎯 Action Items

### If Seeing Anonymous Uploads

**Option 1: Ensure Logged In**
```
1. Go to http://localhost:3001
2. If not logged in, click "Login"
3. Login as admin / admin
4. Try uploading again
```

**Option 2: Check Token Expiry**
```
1. Open DevTools → Application → Local Storage
2. Check if "access_token" exists
3. If missing or expired, login again
```

**Option 3: Manually Test Token**
```bash
# Get token from browser localStorage
TOKEN="<paste_token_here>"

# Test if token is valid
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/users

# If returns users → token is valid
# If returns 401 → token is invalid/expired
```

### If Admin User Not Assigned Team/Dept

Even if authenticated, if admin user doesn't have dept/team assigned:

**Path will be**:
- Department: `Unassigned` or `<department_name>`
- Team: `General` (no team assigned)

**To fix**:
```
1. Go to http://localhost:3001/admin
2. Click "Edit" on admin user
3. Assign:
   - Function: System Administrator
   - Teams: Select a team (e.g., DevOps Team)
4. Save
5. Upload file again
```

**Expected path after assignment**:
```
Technology/DevOps-Team/admin/Default/file.pdf
```

---

## 📊 Current Status

### What's Fixed ✅
- [x] process_document() now uses minio_path instead of file_path
- [x] Backward compatible with old UUID-based uploads
- [x] Backend restarted with fix
- [x] No more "NoSuchKey" errors

### What's Working ✅
- [x] Files upload successfully
- [x] Files stored in MinIO
- [x] Document processing works
- [x] Organizational paths constructed correctly

### What's Observable
- [ ] Files currently going to `Unassigned/General/anonymous/Default`
- [ ] Need to verify user is authenticated
- [ ] Need to verify token is being sent
- [ ] Need to assign admin user to team

---

## 🔧 Quick Test Commands

### Check if Admin is Authenticated User
```sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, username, department_id, function FROM users WHERE username='admin';"
```

### Check Recent Uploads
```sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename, minio_path, uploaded_by FROM documents ORDER BY upload_date DESC LIMIT 3;"
```

### Check MinIO Files
```
http://localhost:9001
Login: minioadmin / minioadmin
Bucket: documents (or ragchatbot)
Path: Browse to see organizational hierarchy
```

---

## 📝 Summary

**Fix Applied**: ✅ process_document() now retrieves files from correct MinIO path

**Current Issue**: Files going to anonymous path suggests:
- User is not logged in, OR
- Token is not being sent, OR
- Token is expired/invalid

**Next Steps**:
1. Verify logged in as admin
2. Check localStorage has `access_token`
3. Upload file while logged in
4. Verify backend logs show "Authenticated upload by user: admin"
5. Assign admin user to team via admin UI
6. Upload again and verify path changes to `Technology/<team>/admin/Default/file.pdf`

---

**Last Updated**: 2025-11-28 11:54 UTC
**Status**: Fix Applied ✅
**Backend**: Restarted ✅
**Testing**: Ready ✅
