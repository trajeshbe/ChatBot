# Upload Authentication Fix

## Problem
Files uploading to `documents/Unassigned/General/anonymous/Default` instead of organizational path.

## Root Cause
Authorization header not being sent from FileUpload component.

Backend logs show:
```
🔑 Authorization header present: False
👤 Anonymous upload (no authentication)
```

## Solution
The token needs to be retrieved fresh on each upload, not cached.

## Files to Update
1. frontend/src/components/FileUpload.tsx - line 95

Current code retrieves token once per file:
```typescript
const token = localStorage.getItem('access_token')
```

This might be getting null if checked before login completes.

## Testing
After fix, backend logs should show:
```
🔑 Authorization header present: True  
🔑 Authorization header value: Bearer eyJhbGc...
👤 Authenticated upload by user: admin
📁 Department: Technology
👥 Team: Tech Team 1
📍 MinIO path: Technology/Tech-Team-1/admin/Default/filename
```
