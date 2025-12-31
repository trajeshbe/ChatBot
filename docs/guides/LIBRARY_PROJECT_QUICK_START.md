# Library & Project Management - Quick Start Guide

**Last Updated**: 2025-11-28
**Status**: Backend Complete, Frontend Pending

---

## 🚀 Quick Start (5 Minutes)

### **Step 1: Apply Database Migrations**

```bash
# Navigate to project root
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot

# Apply migration 007 (project tracking)
docker-compose exec postgres psql -U postgres -d ragchatbot -f /app/migrations/007_add_project_tracking.sql

# Apply migration 008 (normalization)
docker-compose exec postgres psql -U postgres -d ragchatbot -f /app/migrations/008_normalize_departments_teams.sql

# Verify departments were created
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT name, code FROM departments ORDER BY name;"

# Verify teams were created
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT t.name AS team, d.name AS department FROM teams t JOIN departments d ON t.department_id = d.id LIMIT 10;"
```

**Expected Output**:
```
Departments:
- Data Operations
- Finance
- General
- HR
- Marketing
- Sales
- Technology

Teams:
- Data Team 1-16
- Tech Team 1-12
- Marketing Team
- Sales Team
- HR Team
```

### **Step 2: Test API Endpoints**

```bash
# Get all departments
curl http://localhost:8000/api/v1/departments | jq

# Get teams for Technology department
DEPT_ID=$(curl -s http://localhost:8000/api/v1/departments | jq -r '.[] | select(.code=="TECH") | .id')
curl "http://localhost:8000/api/v1/teams?department_id=$DEPT_ID" | jq

# Check storage stats (requires authenticated user)
curl http://localhost:8000/api/v1/library/storage/stats -H "Authorization: Bearer YOUR_TOKEN" | jq
```

### **Step 3: Test Path Builder**

```bash
# Enter Python shell
docker-compose exec backend python

# Test path generation
>>> from app.services.minio_path_builder import MinIOPathBuilder
>>> path = MinIOPathBuilder.build_document_path(
...     role='admin',
...     department='Technology',
...     team='Tech Team 1',
...     username='john.doe',
...     project_name='ChatBot RAG',
...     filename='requirements.pdf'
... )
>>> print(path)
admin/technology/tech-team-1/john.doe/chatbot-rag/documents/requirements.pdf

# Test path parsing
>>> components = MinIOPathBuilder.parse_path(path)
>>> print(f"Department: {components.department}")
>>> print(f"Team: {components.team}")
>>> print(f"Username: {components.username}")
>>> print(f"Project: {components.project}")
```

---

## 📚 API Reference

### **Departments & Teams**

#### Get All Departments
```bash
GET /api/v1/departments

Response:
[
  {
    "id": "uuid",
    "name": "Technology",
    "code": "TECH",
    "description": "Software engineering and IT teams",
    "is_active": true
  }
]
```

#### Get Teams (Filtered by Department)
```bash
GET /api/v1/teams?department_id={uuid}

Response:
[
  {
    "id": "uuid",
    "name": "Tech Team 1",
    "code": "TECH_TEAM_1",
    "department_id": "dept-uuid",
    "department_name": "Technology",
    "team_lead_id": null,
    "member_count": 5,
    "is_active": true
  }
]
```

### **Projects**

#### Create Project
```bash
POST /api/v1/projects
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "ChatBot RAG",
  "description": "Enterprise RAG chatbot",
  "department_id": "dept-uuid",
  "team_id": "team-uuid"
}

Response:
{
  "id": "project-uuid",
  "name": "ChatBot RAG",
  "owner_id": "user-uuid",
  "owner_username": "john.doe",
  "department_name": "Technology",
  "team_name": "Tech Team 1",
  "status": "active",
  "file_count": 0,
  "total_size": 0
}
```

#### Get User's Projects
```bash
GET /api/v1/projects
Authorization: Bearer {token}

Response: [... array of projects ...]
```

#### Get Project Details
```bash
GET /api/v1/projects/{id}
Authorization: Bearer {token}
```

#### Update Project
```bash
PUT /api/v1/projects/{id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Updated Name",
  "description": "Updated description",
  "status": "active"  // or "archived", "closed"
}
```

#### Delete Project
```bash
DELETE /api/v1/projects/{id}
Authorization: Bearer {token}
```

### **Library**

#### Get Files in Project
```bash
GET /api/v1/library/projects/{project_id}/files?search=requirements&file_type=pdf&limit=50&offset=0
Authorization: Bearer {token}

Response:
[
  {
    "id": "file-uuid",
    "filename": "requirements.pdf",
    "file_type": "application/pdf",
    "file_size": 1024000,
    "upload_date": "2025-11-28T10:00:00Z",
    "processed": true,
    "processing_status": "completed",
    "project_name": "ChatBot RAG",
    "uploaded_by_username": "john.doe",
    "department_name": "Technology",
    "team_name": "Tech Team 1",
    "minio_path": "admin/technology/tech-team-1/john.doe/chatbot-rag/documents/requirements.pdf",
    "chunk_count": 45,
    "has_embeddings": true
  }
]
```

#### Get All User Files (with Filters)
```bash
GET /api/v1/library/files?department_id={uuid}&team_id={uuid}&search=report
Authorization: Bearer {token}
```

#### Get File Details
```bash
GET /api/v1/library/files/{file_id}
Authorization: Bearer {token}
```

#### Get Download URL
```bash
GET /api/v1/library/files/{file_id}/download-url?expires_hours=1
Authorization: Bearer {token}

Response:
{
  "download_url": "https://minio:9000/ragchatbot/admin/technology/...?X-Amz-Signature=...",
  "expires_in_hours": 1
}
```

#### Delete File
```bash
DELETE /api/v1/library/files/{file_id}
Authorization: Bearer {token}
```

#### Get Storage Statistics
```bash
GET /api/v1/library/storage/stats
Authorization: Bearer {token}

Response:
{
  "total_files": 150,
  "total_size": 1048576000,
  "total_chunks": 3500,
  "by_project": [
    {
      "project_id": "uuid",
      "project_name": "ChatBot RAG",
      "file_count": 50,
      "total_size": 524288000
    }
  ],
  "by_team": [
    {
      "team_id": "uuid",
      "team_name": "Tech Team 1",
      "file_count": 100,
      "total_size": 838860800
    }
  ]
}
```

---

## 🔧 Integration Example

### **Python: Upload File with Project**

```python
from app.services.document_service_enhanced import enhanced_document_service

# User dict (from authentication)
user_dict = {
    'id': 'user-uuid',
    'username': 'john.doe',
    'role': 'admin',
    'department_id': 'dept-uuid',
    'team_id': 'team-uuid'
}

# Project dict (from project API)
project_dict = {
    'id': 'project-uuid',
    'name': 'ChatBot RAG',
    'department_id': 'dept-uuid',
    'team_id': 'team-uuid'
}

# Upload file
with open('requirements.pdf', 'rb') as f:
    file_data = f.read()

document = await enhanced_document_service.upload_file_with_project(
    file_data=file_data,
    filename='requirements.pdf',
    file_type='application/pdf',
    user_dict=user_dict,
    project_dict=project_dict,
    db=db_session
)

print(f"Uploaded to: {document.minio_path}")
# Output: admin/technology/tech-team-1/john.doe/chatbot-rag/documents/requirements.pdf
```

### **JavaScript: Create Project & Upload File**

```javascript
// 1. Get user's department and team
const departments = await fetch('/api/v1/departments').then(r => r.json())
const userDept = departments.find(d => d.code === 'TECH')

const teams = await fetch(`/api/v1/teams?department_id=${userDept.id}`).then(r => r.json())
const userTeam = teams[0]  // Tech Team 1

// 2. Create project
const project = await fetch('/api/v1/projects', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    name: 'My New Project',
    description: 'Project description',
    department_id: userDept.id,
    team_id: userTeam.id
  })
}).then(r => r.json())

// 3. Upload file to project
const formData = new FormData()
formData.append('file', fileInput.files[0])
formData.append('project_id', project.id)

await fetch('/api/v1/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
})

// 4. Browse files in project
const files = await fetch(`/api/v1/library/projects/${project.id}/files`).then(r => r.json())
console.log('Files in project:', files)
```

---

## 🗂️ MinIO Directory Structure

After uploading files, your MinIO bucket will look like:

```
ragchatbot/
├── admin/
│   ├── technology/
│   │   ├── tech-team-1/
│   │   │   ├── john.doe/
│   │   │   │   ├── chatbot-rag/
│   │   │   │   │   ├── documents/
│   │   │   │   │   │   ├── requirements.pdf
│   │   │   │   │   │   └── design.docx
│   │   │   │   │   ├── exports/
│   │   │   │   │   │   └── conversation.pdf
│   │   │   │   │   └── extractions/
│   │   │   │   │       └── data.json
│   │   │   │   └── ml-pipeline/
│   │   │   │       └── documents/
│   │   │   │           └── dataset.csv
│   │   │   └── jane.smith/
│   │   │       └── ...
│   │   └── tech-team-2/
│   │       └── ...
│   └── marketing/
│       └── ...
└── user/
    └── data-operations/
        └── data-team-1/
            └── ...
```

---

## 🐛 Troubleshooting

### **Migrations fail**

```bash
# Check if migrations already applied
docker-compose exec postgres psql -U postgres -d ragchatbot -c "\dt departments"

# If table exists, migration already applied
# Otherwise, check logs:
docker-compose logs postgres
```

### **API returns 404**

```bash
# Check if routes are registered
docker-compose logs backend | grep "teams_projects_routes"

# If not found, need to update main.py to include routes
```

### **Path builder not found**

```bash
# Verify service exists
docker-compose exec backend ls -la /app/app/services/minio_path_builder.py

# If not found, need to copy file to container
docker-compose restart backend
```

### **No departments in database**

```bash
# Re-run migration 008 which seeds departments
docker-compose exec postgres psql -U postgres -d ragchatbot -f /app/migrations/008_normalize_departments_teams.sql
```

---

## 📖 Additional Documentation

- **ERD**: `docs/architecture/DATABASE_SCHEMA_ERD.md`
- **Implementation Guide**: `docs/features/LIBRARY_AND_PROJECT_MANAGEMENT_IMPLEMENTATION.md`
- **Complete Summary**: `docs/features/LIBRARY_PROJECT_COMPLETE_IMPLEMENTATION_SUMMARY.md`
- **Progress Tracking**: `docs/features/LIBRARY_PROJECT_IMPLEMENTATION_PROGRESS.md`

---

## ✅ Verification Checklist

- [ ] Migrations 007 & 008 applied successfully
- [ ] Departments table populated (7 departments)
- [ ] Teams table populated (32 teams)
- [ ] `/api/v1/departments` endpoint returns data
- [ ] `/api/v1/teams` endpoint returns data
- [ ] Path builder generates correct paths
- [ ] Can create a project via API
- [ ] Can list projects via API
- [ ] Ready for frontend integration

---

**Backend Complete! Frontend components coming next.** 🚀

