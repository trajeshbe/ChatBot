# Agent FileNotFoundError Troubleshooting Guide

**Issue**: Tasks fail with `[Errno 2] No such file or directory`
**Date**: 2025-11-30
**Status**: Common Issue - Solution Available

---

## Quick Diagnosis

### Error Signature

```json
{
  "error": "[Errno 2] No such file or directory",
  "error_details": {
    "exception": "FileNotFoundError"
  }
}
```

**Task Description Example**:
```
"Analyze the data in /workspace/sales.csv and create a visualization"
```

---

## Root Cause Analysis

### Timeline of Your Failed Tasks

```
11:31:38  ❌ Task created → File doesn't exist → FAILED
11:35:53  ❌ Task created → File doesn't exist → FAILED
11:40:10  ❌ Task created → File doesn't exist → FAILED
11:41:00  ✅ File copied via docker cp /tmp/sales.csv
11:45:01  ❌ Task created → Container restarted → File lost → FAILED
```

### Why Files Disappear

**Problem**: Container restart loop clears ephemeral storage

```
Container Lifecycle:
1. Container starts
2. Volumes mount (/workspace)
3. File copied via `docker cp` → Goes to container filesystem (NOT volume)
4. Task executes
5. Container exits
6. Docker restarts container
7. Container filesystem reset → FILE LOST
8. Volume persists, but file wasn't in volume
```

**Key Insight**: `docker cp` copies to container filesystem, not the mounted volume!

---

## Solutions (4 Options)

### ✅ Option 1: Stop Container, Then Copy (Quickest)

**Best for**: Immediate testing, small files

```bash
# 1. Stop the container
docker-compose stop agent-runtime

# 2. Start it without the restart loop
docker run -d --name rag-agent-runtime-temp \
  -v chatbot_agent_workspace:/workspace \
  chatbot-agent-runtime:llm-enabled \
  tail -f /dev/null

# 3. Copy file
docker cp /tmp/sales.csv rag-agent-runtime-temp:/workspace/sales.csv

# 4. Verify
docker exec rag-agent-runtime-temp ls -la /workspace/

# 5. Stop temp container
docker stop rag-agent-runtime-temp
docker rm rag-agent-runtime-temp

# 6. Start original container
docker-compose start agent-runtime
```

---

### ✅ Option 2: Copy Directly to Volume (Recommended)

**Best for**: Reliable file persistence, production

```bash
# 1. Get volume mountpoint
VOLUME_PATH=$(docker volume inspect chatbot_agent_workspace --format '{{.Mountpoint}}')
echo "Volume path: $VOLUME_PATH"

# Output example: /var/lib/docker/volumes/chatbot_agent_workspace/_data

# 2. Copy file (requires sudo)
sudo cp /tmp/sales.csv $VOLUME_PATH/sales.csv

# 3. Set permissions
sudo chown 1000:1000 $VOLUME_PATH/sales.csv
sudo chmod 644 $VOLUME_PATH/sales.csv

# 4. Verify
sudo ls -la $VOLUME_PATH/

# 5. Test from container
docker exec rag-agent-runtime ls -la /workspace/ 2>/dev/null || echo "Container restarting, wait a moment..."
```

**Verification Script**:
```bash
#!/bin/bash
# verify_workspace_file.sh

VOLUME_PATH=$(docker volume inspect chatbot_agent_workspace --format '{{.Mountpoint}}')

echo "📁 Checking volume contents..."
sudo ls -lah $VOLUME_PATH/

echo -e "\n🐳 Waiting for container..."
while ! docker exec rag-agent-runtime echo "Ready" 2>/dev/null; do
    sleep 2
done

echo -e "\n📂 Container workspace:"
docker exec rag-agent-runtime ls -lah /workspace/

echo -e "\n✅ Verification complete!"
```

---

### ✅ Option 3: Mount Host Directory (Best for Development)

**Best for**: Active development, frequent file changes

**Edit `docker-compose.yml`**:
```yaml
services:
  agent-runtime:
    image: chatbot-agent-runtime:llm-enabled
    container_name: rag-agent-runtime
    volumes:
      - agent_workspace:/workspace
      - agent_artifacts:/artifacts
      - ./sample_data:/workspace/sample_data:ro  # NEW: Host directory mount
    # ... rest of config
```

**Create directory and add files**:
```bash
# 1. Create directory
mkdir -p sample_data

# 2. Copy files
cp /tmp/sales.csv sample_data/sales.csv

# 3. Restart container
docker-compose restart agent-runtime

# 4. Verify
docker exec rag-agent-runtime ls -la /workspace/sample_data/
```

**Update task descriptions**:
```
OLD: "Analyze /workspace/sales.csv"
NEW: "Analyze /workspace/sample_data/sales.csv"
```

**Advantages**:
- ✅ Files persist automatically
- ✅ Can edit files on host, changes reflect immediately
- ✅ Easy to add/remove files
- ✅ Version control friendly (git add sample_data/)

**Disadvantages**:
- ⚠️ Read-only mount (`:ro`) prevents agent from writing to this directory
- ⚠️ Remove `:ro` if agent needs to write files

---

### ✅ Option 4: Upload API Endpoint (Production-Ready)

**Best for**: Production, multi-user environments, security

**Backend Implementation** (create new endpoint):

```python
# backend/app/api/routes/agent_routes.py

from fastapi import UploadFile, File
import shutil

@router.post("/api/v1/agent/upload-workspace-file")
async def upload_workspace_file(
    file: UploadFile = File(...),
    description: str = None
):
    """
    Upload a file to agent workspace for use in tasks
    """
    try:
        # Define workspace path (volume mount)
        workspace_path = "/workspace"  # Container path
        file_path = f"{workspace_path}/{file.filename}"

        # Save file to volume
        # Note: Backend container needs volume mount to same workspace
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "status": "success",
            "filename": file.filename,
            "path": file_path,
            "size": file.size,
            "message": f"File uploaded to {file_path}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )
```

**Update docker-compose.yml** (backend needs same volume):
```yaml
services:
  backend:
    volumes:
      - agent_workspace:/workspace  # NEW: Share workspace volume

  agent-runtime:
    volumes:
      - agent_workspace:/workspace
      - agent_artifacts:/artifacts

volumes:
  agent_workspace:
  agent_artifacts:
```

**Frontend Integration**:
```typescript
// Upload file before creating task
const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(
    'http://localhost:8000/api/v1/agent/upload-workspace-file',
    formData
  );

  return response.data;
};

// Then create task
const createTask = async (filePath: string) => {
  await axios.post('http://localhost:8000/api/v1/agent/tasks', {
    task_description: `Analyze ${filePath} and create a visualization`,
    model: 'qwen2.5-coder:7b'
  });
};
```

**Usage Flow**:
```
1. User uploads file via UI
2. File saved to /workspace (shared volume)
3. Backend returns file path
4. User creates task with file path in description
5. Agent executes task → File is available
```

**Advantages**:
- ✅ Secure (file validation, virus scanning)
- ✅ User-friendly
- ✅ Audit trail (who uploaded what)
- ✅ File management (list, delete)

---

## Immediate Fix for Current Issue

**To fix your existing sales.csv issue right now**:

```bash
#!/bin/bash
# fix_sales_csv.sh

echo "🔧 Fixing sales.csv in agent workspace..."

# Get volume path
VOLUME_PATH=$(docker volume inspect chatbot_agent_workspace --format '{{.Mountpoint}}')

# Create sales.csv
cat > /tmp/sales.csv << 'EOF'
date,product,category,quantity,unit_price,revenue,region
2024-01-01,Widget A,Electronics,100,15.00,1500.00,North
2024-01-01,Widget B,Electronics,50,20.00,1000.00,South
2024-01-02,Widget A,Electronics,75,15.00,1125.00,East
2024-01-02,Widget C,Furniture,30,50.00,1500.00,West
2024-01-03,Widget B,Electronics,80,20.00,1600.00,North
2024-01-03,Widget D,Furniture,25,60.00,1500.00,South
2024-01-04,Widget A,Electronics,120,15.00,1800.00,East
2024-01-04,Widget C,Furniture,40,50.00,2000.00,West
2024-01-05,Widget B,Electronics,90,20.00,1800.00,North
2024-01-05,Widget D,Furniture,35,60.00,2100.00,South
EOF

# Copy to volume
sudo cp /tmp/sales.csv $VOLUME_PATH/sales.csv
sudo chown 1000:1000 $VOLUME_PATH/sales.csv
sudo chmod 644 $VOLUME_PATH/sales.csv

# Verify
echo "✅ File copied to volume"
echo "📁 Volume contents:"
sudo ls -lah $VOLUME_PATH/

# Wait for container
echo "⏳ Waiting for container to be ready..."
sleep 3

# Verify from container
echo "🐳 Verifying from container:"
docker exec rag-agent-runtime ls -lah /workspace/ 2>/dev/null || \
  echo "⚠️  Container is restarting, file will be available when it starts"

echo "✅ Fix complete! Create a new task to test."
```

**Run it**:
```bash
chmod +x fix_sales_csv.sh
./fix_sales_csv.sh
```

**Then create a new task in UI**:
```
Task Description: "List all files in /workspace and show the first 5 lines of sales.csv"
```

---

## Prevention Checklist

Before creating tasks that reference files:

- [ ] Verify file exists in volume (not just container)
- [ ] Use absolute paths (`/workspace/file.csv`, not `./file.csv`)
- [ ] Check file permissions (readable by container user)
- [ ] Test with simple task first ("list files")
- [ ] Monitor container restart behavior

---

## Testing File Availability

**Test Script**:
```bash
#!/bin/bash
# test_file_availability.sh

FILE_PATH="/workspace/sales.csv"

echo "Testing file availability..."

# Wait for container
while ! docker exec rag-agent-runtime echo "Ready" 2>/dev/null; do
    echo "Waiting for container..."
    sleep 2
done

# Check if file exists
if docker exec rag-agent-runtime test -f $FILE_PATH; then
    echo "✅ File exists: $FILE_PATH"

    # Check if readable
    if docker exec rag-agent-runtime cat $FILE_PATH > /dev/null 2>&1; then
        echo "✅ File is readable"

        # Show first few lines
        echo -e "\n📄 File contents (first 3 lines):"
        docker exec rag-agent-runtime head -3 $FILE_PATH
    else
        echo "❌ File exists but is not readable (permission issue)"
    fi
else
    echo "❌ File does not exist: $FILE_PATH"
    echo "📂 Current workspace contents:"
    docker exec rag-agent-runtime ls -la /workspace/
fi
```

---

## Common Pitfalls

### ❌ Mistake 1: Using `docker cp` during restart loop
```bash
# BAD: File will be lost on next restart
docker cp /tmp/file.csv rag-agent-runtime:/workspace/
```

### ✅ Correct Approach
```bash
# GOOD: Copy to volume directly
VOLUME_PATH=$(docker volume inspect chatbot_agent_workspace --format '{{.Mountpoint}}')
sudo cp /tmp/file.csv $VOLUME_PATH/
```

---

### ❌ Mistake 2: Wrong path in task description
```bash
# BAD: Relative path
"Analyze the file sales.csv"

# BAD: Wrong directory
"Analyze /app/sales.csv"

# BAD: Windows path
"Analyze C:\Data\sales.csv"
```

### ✅ Correct Approach
```bash
# GOOD: Absolute path in container
"Analyze the data in /workspace/sales.csv"
```

---

### ❌ Mistake 3: File permissions
```bash
# BAD: File not readable by container user
sudo cp /tmp/file.csv $VOLUME_PATH/
sudo chmod 600 $VOLUME_PATH/file.csv  # Only root can read
```

### ✅ Correct Approach
```bash
# GOOD: Readable by container user (UID 1000)
sudo cp /tmp/file.csv $VOLUME_PATH/
sudo chown 1000:1000 $VOLUME_PATH/file.csv
sudo chmod 644 $VOLUME_PATH/file.csv  # Everyone can read
```

---

## Summary

### Why Tasks Failed

1. ❌ **11:31, 11:35, 11:40**: File didn't exist yet
2. ❌ **11:45**: File copied to container (not volume), lost on restart

### How to Fix

✅ **Quick**: Run `fix_sales_csv.sh` script above
✅ **Proper**: Implement Option 2 or 4 (volume or API)
✅ **Development**: Use Option 3 (mount host directory)

### Best Practice

**For production**, implement Option 4 (Upload API):
- Secure
- User-friendly
- Audit trail
- Persistent across restarts

**For development**, use Option 3 (Host mount):
- Fast iteration
- Easy file management
- Git-friendly

---

**Status**: ✅ Solutions Available
**Recommended**: Option 2 (Volume) or Option 4 (API)
**Priority**: Medium (workaround available)
