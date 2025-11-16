# Quick Start Guide - Memory Hierarchy & Audit Logging

## 🚀 Setup (First Time)

### Step 1: Setup Database

Run the automated setup script:

```bash
./setup-database.sh
```

**This will:**
- ✅ Create `rag_chatbot` database if needed
- ✅ Enable required extensions (uuid-ossp, vector)
- ✅ Create base tables (documents, chunks, etc.)
- ✅ Apply RBAC and audit migrations
- ✅ Create default admin user

**Expected Output:**
```
✓ Database 'rag_chatbot' ready
✓ Extensions enabled
✓ Base tables created
✓ RBAC and audit tables created
✓ Default users created

Default credentials:
  Username: admin
  Password: admin123
```

### Step 2: Update Backend Code (Optional for Testing)

**Option A - Quick Test**:
```bash
cd backend/app
cp main_enhanced.py main.py
cd ../..
```

**Option B - Manual Integration**:
Use `backend/app/main_enhanced.py` as reference

### Step 3: Restart Backend

```bash
docker compose restart backend

# Watch logs
docker compose logs -f backend | head -50
```

**Look for:**
```
✓ Using Enhanced RAG Service with memory hierarchy
```

---

## 🧪 Test It Works

### Upload with Session

```bash
SESSION_ID="test-$(date +%s)"

curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@test.pdf" \
  -F "session_id=$SESSION_ID"
```

### Query with Session

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Summarize" \
  -F "session_id=$SESSION_ID" | jq
```

Look for: `"num_short_term_sources": 1`

---

## 📊 Diagnostic Tools

```bash
./check-documents.sh      # Check document processing
./validate-services.sh    # Check all services
```

---

## 📚 Full Documentation

See `MEMORY_HIERARCHY_GUIDE.md` for complete details.
