# Complete Organizational Upload Test

## Test performed: 2025-11-28

### Upload Success ✅
- File: test_org_upload.txt
- User: admin (authenticated)
- Session: test-session-2

### Organizational Path in MinIO ✅
Technology/Tech-Team-1/admin/Default/test_org_upload.txt

### Database - documents table ✅
- filename: test_org_upload.txt
- minio_path: Technology/Tech-Team-1/admin/Default/test_org_upload.txt
- department: Technology
- team: Tech Team 1
- uploaded_by: f754df7e-71d2-477a-ba94-1ed44fa37291

### Database - document_chunks table ✅
- department: Technology
- team: Tech Team 1
- uploaded_by: f754df7e-71d2-477a-ba94-1ed44fa37291
