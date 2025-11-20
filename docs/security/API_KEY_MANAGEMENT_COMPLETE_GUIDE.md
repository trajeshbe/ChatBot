# Complete Guide: API Key Management & MASTER_ENCRYPTION_KEY

**Last Updated**: 2025-11-20 (Evening - All fixes applied)
**Status**: ✅ Production System FULLY OPERATIONAL
**Critical Level**: HIGH - Handle with care

---

## Table of Contents

1. [Historical Evolution](#historical-evolution)
2. [Current Architecture](#current-architecture)
3. [MASTER_ENCRYPTION_KEY Management](#master_encryption_key-management)
4. [Migration Path](#migration-path)
5. [Troubleshooting & Recovery](#troubleshooting--recovery)
6. [Emergency Fallback Procedures](#emergency-fallback-procedures)
7. [Best Practices](#best-practices)

---

## Historical Evolution

### Phase 1: Hardcoded Environment Variables (Original Design)

**Timeline**: Initial implementation → 2025-11-20

**How it worked**:
```bash
# .env file
OPENAI_API_KEY=sk-<YOUR_OPENAI_API_KEY_HERE>
HUGGING_FACE_HUB_TOKEN=hf_<YOUR_HF_ACCESS_TOKEN_HERE>

# docker-compose.yml
services:
  backend:
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
```

**Backend code**:
```python
# app/services/llm_service.py
import os

class LLMService:
    def __init__(self):
        # Direct environment variable access
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        # Initialize clients
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
```

**Problems with this approach**:
1. ❌ **Security Risk**: API keys stored in plain text in .env file
2. ❌ **Version Control Risk**: Easy to accidentally commit .env to git
3. ❌ **No Rotation**: Changing keys requires restarting all containers
4. ❌ **No Audit Trail**: No way to track who added/modified keys
5. ❌ **Multi-User Issues**: All users share the same API keys
6. ❌ **No UI Management**: Must edit files and restart services
7. ❌ **Limited Flexibility**: Can't add new API providers without code changes

### Phase 2: Database-Stored Encrypted Keys (Current System)

**Timeline**: 2025-11-20 → Present

**What changed**:

1. **New Database Table** (`backend/migrations/add_api_keys_table.sql`):
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL,              -- 'openai', 'anthropic', etc.
    key_name VARCHAR(100) NOT NULL,             -- User-friendly name
    encrypted_key TEXT NOT NULL,                -- Fernet-encrypted API key
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    last_used TIMESTAMP WITH TIME ZONE,
    UNIQUE(provider, key_name)
);
```

2. **New Service** (`backend/app/services/secrets_service.py`):
```python
from cryptography.fernet import Fernet
import os

class SecretsService:
    def __init__(self):
        # Load encryption key from environment
        master_key = os.getenv("MASTER_ENCRYPTION_KEY")
        if not master_key:
            raise ValueError("MASTER_ENCRYPTION_KEY not set")

        self.cipher = Fernet(master_key.encode())

    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key for storage."""
        return self.cipher.encrypt(api_key.encode()).decode()

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key for use."""
        return self.cipher.decrypt(encrypted_key.encode()).decode()

    async def store_api_key(self, provider: str, key_name: str,
                           api_key: str, user_id: str):
        """Store encrypted API key in database."""
        encrypted = self.encrypt_api_key(api_key)
        # Store in database...
```

3. **Updated LLM Service** (`backend/app/services/llm_service.py`):
```python
from app.services.secrets_service import get_secrets_service

class LLMService:
    def __init__(self, db: Session):
        self.secrets_service = get_secrets_service()
        self.db = db

    async def get_openai_client(self):
        """Get OpenAI client with latest API key from database."""
        # First try database
        api_key = await self.secrets_service.get_active_api_key(
            provider="openai",
            db=self.db
        )

        # Fallback to environment variable if no database key
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")

        if api_key:
            return OpenAI(api_key=api_key)

        raise ValueError("No OpenAI API key found")
```

4. **New API Routes** (`backend/app/api/routes/secrets_routes.py`):
```python
@router.get("/api/v1/admin/secrets/api-keys")
async def list_api_keys():
    """List all configured API keys (masked)."""
    pass

@router.post("/api/v1/admin/secrets/api-keys")
async def add_api_key(request: AddAPIKeyRequest):
    """Add new encrypted API key."""
    pass

@router.delete("/api/v1/admin/secrets/api-keys/{key_id}")
async def delete_api_key(key_id: str):
    """Delete API key."""
    pass
```

5. **Frontend UI** (`frontend/src/pages/admin.tsx`):
```typescript
// New "API Keys" tab in admin dashboard
<Tab>API Keys</Tab>

// UI shows:
// - List of all API keys (with masking: sk-proj-***...***4A)
// - Add new key button
// - Delete/deactivate buttons
// - Last used timestamp
// - Active/Inactive status
```

**Benefits of this approach**:
1. ✅ **Security**: Keys encrypted at rest using Fernet (AES-128)
2. ✅ **Audit Trail**: Track who added keys and when they were last used
3. ✅ **No Restart Required**: Add/remove keys without restarting services
4. ✅ **Multi-User**: Different users can manage different keys
5. ✅ **UI Management**: Easy web interface for key management
6. ✅ **Flexible**: Add new providers without code changes
7. ✅ **Version Control Safe**: No API keys in .env file (except encryption key)
8. ✅ **Key Rotation**: Easy to rotate keys and track old ones

---

## Current Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     .env File (Host)                         │
│  MASTER_ENCRYPTION_KEY=Tv443mxAGRSYNYSs2B_EmNYEIoA_7EQK6...  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               docker-compose.yml                             │
│  backend:                                                    │
│    environment:                                              │
│      MASTER_ENCRYPTION_KEY: ${MASTER_ENCRYPTION_KEY:-}      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            Backend Container Environment                     │
│  MASTER_ENCRYPTION_KEY=Tv443mxAGRSYNYSs2B_EmNYEIoA_7...     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               SecretsService (Python)                        │
│  cipher = Fernet(MASTER_ENCRYPTION_KEY)                     │
│                                                              │
│  encrypt_api_key()  ──────────▶  Database (encrypted)       │
│  decrypt_api_key()  ◀──────────  Database (encrypted)       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                             │
│  api_keys table:                                             │
│  ┌──────────┬──────────┬─────────────────────────┐          │
│  │ provider │ key_name │ encrypted_key           │          │
│  ├──────────┼──────────┼─────────────────────────┤          │
│  │ openai   │ prod-key │ gAAAAABf3q2r3qL4...     │          │
│  │ anthropic│ dev-key  │ gAAAAABf3q2r3qL4...     │          │
│  └──────────┴──────────┴─────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  LLM Service (Python)                        │
│  1. Query api_keys table                                     │
│  2. Decrypt key with SecretsService                          │
│  3. Use decrypted key with OpenAI/Anthropic client           │
│  4. FALLBACK: Use os.getenv("OPENAI_API_KEY") if no DB key  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Example

**Storing a new API key**:
```
1. User enters API key in frontend: "sk-proj-abc123..."
   ↓
2. POST /api/v1/admin/secrets/api-keys
   ↓
3. SecretsService.encrypt_api_key("sk-proj-abc123...")
   ↓
4. Fernet.encrypt() → "gAAAAABf3q2r3qL4..."
   ↓
5. Store encrypted key in PostgreSQL
   ↓
6. Return success to user
```

**Using an API key**:
```
1. LLM request comes in
   ↓
2. LLMService.get_openai_client()
   ↓
3. Query api_keys table for active OpenAI key
   ↓
4. SecretsService.decrypt_api_key("gAAAAABf3q2r3...")
   ↓
5. Fernet.decrypt() → "sk-proj-abc123..."
   ↓
6. OpenAI(api_key="sk-proj-abc123...")
   ↓
7. Make API call
```

---

## MASTER_ENCRYPTION_KEY Management

### What is MASTER_ENCRYPTION_KEY?

The `MASTER_ENCRYPTION_KEY` is a **Fernet symmetric encryption key** used to encrypt/decrypt all API keys stored in the database.

**Technical Details**:
- **Algorithm**: Fernet (AES-128 in CBC mode with HMAC authentication)
- **Key Format**: 44-character base64-encoded string
- **Example**: `Tv443mxAGRSYNYSs2B_EmNYEIoA_7EQK6Ga7w0KwBaM=`
- **Generated by**: Python's `cryptography.fernet.Fernet.generate_key()`

### Current Key Location

**Your current encryption key**:
```bash
# In .env file:
MASTER_ENCRYPTION_KEY=Tv443mxAGRSYNYSs2B_EmNYEIoA_7EQK6Ga7w0KwBaM=
```

### How to Generate a New Key

```bash
# Method 1: Python one-liner
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Method 2: Python script
python3 << 'EOF'
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(f"New MASTER_ENCRYPTION_KEY: {key.decode()}")
EOF

# Example output:
# New MASTER_ENCRYPTION_KEY: zk6fxsTUXzPJBezVGa4_vvMjDQ7iFfQ-GFiaw1LSjNA=
```

### Where to Store the Key

**Current storage (recommended)**:
```bash
# .env file (root of project)
MASTER_ENCRYPTION_KEY=Tv443mxAGRSYNYSs2B_EmNYEIoA_7EQK6Ga7w0KwBaM=
```

**Additional backup locations (for disaster recovery)**:

1. **Password Manager** (e.g., 1Password, LastPass, Bitwarden)
   - Store as secure note
   - Tag: "ChatBot MASTER_ENCRYPTION_KEY"

2. **Encrypted USB Drive** (for air-gapped backup)
   ```
   File: chatbot_encryption_key.txt
   Content:
   MASTER_ENCRYPTION_KEY=Tv443mxAGRSYNYSs2B_EmNYEIoA_7EQK6Ga7w0KwBaM=
   Created: 2025-11-20
   Purpose: Decrypt API keys in PostgreSQL api_keys table
   ```

3. **Encrypted Cloud Backup** (e.g., encrypted S3 bucket)
   - Encrypt with GPG before upload
   - Store in private repository

**DO NOT STORE**:
- ❌ In git repository (even private)
- ❌ In plain text on shared drives
- ❌ In emails or Slack messages
- ❌ In unencrypted cloud storage

### Key Rotation Procedure

**When to rotate**:
- Every 90 days (recommended)
- When team member with access leaves
- After suspected security breach
- When upgrading encryption algorithm

**How to rotate**:

```bash
# Step 1: Backup current key
echo "Old key: $(grep MASTER_ENCRYPTION_KEY .env)" >> .master_key_backup.txt

# Step 2: Generate new key
NEW_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "New key: $NEW_KEY" >> .master_key_backup.txt

# Step 3: Re-encrypt all API keys with new key
docker-compose exec backend python3 << 'EOF'
from app.services.secrets_service import SecretsService
from app.core.database import get_db
from cryptography.fernet import Fernet
import os

# Load old and new keys
old_key = os.getenv("MASTER_ENCRYPTION_KEY")
new_key = "YOUR_NEW_KEY_HERE"

old_cipher = Fernet(old_key.encode())
new_cipher = Fernet(new_key.encode())

db = next(get_db())

# Get all encrypted API keys
api_keys = db.execute("SELECT id, encrypted_key FROM api_keys").fetchall()

for key_id, encrypted_key in api_keys:
    # Decrypt with old key
    decrypted = old_cipher.decrypt(encrypted_key.encode()).decode()

    # Re-encrypt with new key
    re_encrypted = new_cipher.encrypt(decrypted.encode()).decode()

    # Update database
    db.execute(
        "UPDATE api_keys SET encrypted_key = %s WHERE id = %s",
        (re_encrypted, key_id)
    )

db.commit()
print("✅ All API keys re-encrypted successfully")
EOF

# Step 4: Update .env with new key
sed -i "s/MASTER_ENCRYPTION_KEY=.*/MASTER_ENCRYPTION_KEY=$NEW_KEY/" .env

# Step 5: Restart backend
docker-compose up -d backend

# Step 6: Test
curl http://localhost:8000/api/v1/admin/secrets/api-keys
```

---

## Migration Path

### From Hardcoded .env to Encrypted Database

**Current state of your system**:
- ✅ Encryption system fully implemented
- ✅ MASTER_ENCRYPTION_KEY configured in docker-compose.yml
- ✅ Backend can read encryption key
- ⚠️ Still have hardcoded `OPENAI_API_KEY` in .env (for fallback)

**Recommended migration steps**:

#### Step 1: Verify Encryption System Works

```bash
# Test that encryption key is loaded
docker exec rag-backend printenv | grep MASTER_ENCRYPTION_KEY
# Should output: MASTER_ENCRYPTION_KEY=Tv443mxAGRSYNYSs2B_EmNYEIoA_7EQK6Ga7w0KwBaM=

# Test API keys endpoint
curl http://localhost:8000/api/v1/admin/secrets/api-keys
# Should output: [] (empty array, no errors)
```

#### Step 2: Add Your First API Key via UI

```bash
# Navigate to admin dashboard
# http://localhost:3001/admin → Click "API Keys" tab

# Click "Add API Key" button
# Fill in:
#   Provider: openai
#   Key Name: production-key
#   API Key: sk-<YOUR_OPENAI_API_KEY_HERE>

# Or via API:
curl -X POST http://localhost:8000/api/v1/admin/secrets/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "key_name": "production-key",
    "api_key": "sk-<YOUR_OPENAI_API_KEY_HERE>"
  }'
```

#### Step 3: Test LLM Service with Database Key

```bash
# Make a test query
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Hello, test the API key" \
  -F "model_id=gpt-4-turbo"

# Check logs to see which API key was used
docker-compose logs backend | grep -i "openai"
# Should show: "Using OpenAI API key from database: production-key"
```

#### Step 4: Remove Hardcoded Key from .env (Optional)

**CAUTION**: Only do this after confirming database keys work!

```bash
# Backup current .env
cp .env .env.backup.$(date +%Y%m%d)

# Comment out hardcoded API keys
sed -i 's/^OPENAI_API_KEY=/#OPENAI_API_KEY=/' .env
sed -i 's/^HUGGING_FACE_HUB_TOKEN=/#HUGGING_FACE_HUB_TOKEN=/' .env

# .env should now look like:
# #OPENAI_API_KEY=sk-proj-G2vXFsYkNhsSmJk6...
# #HUGGING_FACE_HUB_TOKEN=hf_eelBuutYxJatZ...
# MASTER_ENCRYPTION_KEY=Tv443mxAGRSYNYSs2B_EmNYEIoA_7EQK6Ga7w0KwBaM=

# Restart backend
docker-compose up -d backend

# Test again
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Hello again" \
  -F "model_id=gpt-4-turbo"
```

#### Step 5: Add Other API Keys

```bash
# Add Anthropic key
curl -X POST http://localhost:8000/api/v1/admin/secrets/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "anthropic",
    "key_name": "production-claude",
    "api_key": "sk-ant-api03-your-anthropic-key"
  }'

# Add Hugging Face key
curl -X POST http://localhost:8000/api/v1/admin/secrets/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "huggingface",
    "key_name": "production-hf",
    "api_key": "hf_<YOUR_HF_ACCESS_TOKEN_HERE>"
  }'
```

---

## Troubleshooting & Recovery

### Issue 1: "MASTER_ENCRYPTION_KEY not set" Error

**Symptoms**:
```
ValueError: MASTER_ENCRYPTION_KEY not set. Generate one with:
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

**Diagnosis**:
```bash
# Check if key exists in .env
grep MASTER_ENCRYPTION_KEY .env

# Check if docker-compose.yml has it
grep MASTER_ENCRYPTION_KEY docker-compose.yml

# Check if backend container has it
docker exec rag-backend printenv | grep MASTER_ENCRYPTION_KEY
```

**Solutions**:

**Solution 1: Key missing from .env**
```bash
# Generate and add key
echo "MASTER_ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env

# Recreate backend
docker-compose up -d backend
```

**Solution 2: Key not in docker-compose.yml**
```yaml
# Edit docker-compose.yml, add under backend.environment:
MASTER_ENCRYPTION_KEY: ${MASTER_ENCRYPTION_KEY:-}

# Recreate backend
docker-compose up -d backend
```

**Solution 3: Container not picking up environment variable**
```bash
# Stop and remove container
docker-compose down backend

# Recreate (not just restart)
docker-compose up -d backend

# Verify
docker exec rag-backend printenv | grep MASTER_ENCRYPTION_KEY
```

### Issue 2: API Keys Page Shows "Failed to load API keys"

**Symptoms**:
- Frontend shows error message
- Backend returns 500 Internal Server Error

**Diagnosis**:
```bash
# Check backend logs
docker-compose logs backend | tail -50

# Test API endpoint
curl http://localhost:8000/api/v1/admin/secrets/api-keys

# Check database connection
docker-compose exec backend python3 << 'EOF'
from app.core.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1").fetchone()
        print("✅ Database connected")
except Exception as e:
    print(f"❌ Database error: {e}")
EOF
```

**Solutions**:

**Solution 1: Database table doesn't exist**
```bash
# Run migration to create api_keys table
docker-compose exec backend python3 << 'EOF'
from app.core.database import engine

create_table_sql = """
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL,
    key_name VARCHAR(100) NOT NULL,
    encrypted_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    last_used TIMESTAMP WITH TIME ZONE,
    UNIQUE(provider, key_name)
);
"""

with engine.connect() as conn:
    conn.execute(create_table_sql)
    conn.commit()
    print("✅ api_keys table created")
EOF
```

**Solution 2: SecretsService not initialized**
```bash
# Check if secrets_service.py exists
ls -la backend/app/services/secrets_service.py

# If missing, the file needs to be created (see implementation details in MASTER_ENCRYPTION_KEY_SETUP.md)
```

### Issue 3: Lost or Forgotten MASTER_ENCRYPTION_KEY

**CRITICAL**: Without the encryption key, you CANNOT decrypt existing API keys in the database!

**Recovery Options**:

**Option 1: Find the key from backup**
```bash
# Check .env file
cat .env | grep MASTER_ENCRYPTION_KEY

# Check .env.backup files
ls -la .env.backup.*
cat .env.backup.20251120

# Check password manager
# (manually check 1Password, LastPass, etc.)

# Check encrypted backups
gpg --decrypt master_key_backup.txt.gpg
```

**Option 2: Check running container** (if backend is still running)
```bash
# Extract from running container
docker exec rag-backend printenv | grep MASTER_ENCRYPTION_KEY

# Save immediately
docker exec rag-backend printenv | grep MASTER_ENCRYPTION_KEY >> .master_key_recovered.txt
```

**Option 3: Check git history** (if key was committed by mistake)
```bash
# Search git history
git log -S "MASTER_ENCRYPTION_KEY" --all

# Show content from specific commit
git show <commit-hash>:.env
```

**Option 4: Database dump might contain it** (PostgreSQL backups)
```bash
# Check recent database backups
grep -r "MASTER_ENCRYPTION_KEY" /path/to/backups/
```

**Option 5: WORST CASE - Cannot recover key**

If you absolutely cannot find the key, see [Emergency Fallback Procedures](#emergency-fallback-procedures)

### Issue 4: Decryption Fails After Key Rotation

**Symptoms**:
```
cryptography.fernet.InvalidToken: Token was not valid
```

**Cause**: API keys in database are encrypted with old key, but new key is being used

**Solution**:
```bash
# Rollback to old key
echo "MASTER_ENCRYPTION_KEY=OLD_KEY_HERE" > .env

# Restart backend
docker-compose up -d backend

# Re-run key rotation procedure correctly (see "Key Rotation Procedure" section)
```

---

## Emergency Fallback Procedures

### Scenario: Complete Loss of MASTER_ENCRYPTION_KEY

**Impact**:
- ❌ Cannot decrypt any API keys stored in database
- ❌ All LLM features will fail if relying on database keys
- ✅ Can still use hardcoded environment variables (if configured)

**Emergency Recovery Steps**:

#### Step 1: Immediate Fallback to Environment Variables

```bash
# 1. Edit .env file and add/uncomment API keys
cat >> .env << 'EOF'
# EMERGENCY FALLBACK - DO NOT COMMIT
OPENAI_API_KEY=sk-proj-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-api03-your-anthropic-key-here
HUGGING_FACE_HUB_TOKEN=hf_your-huggingface-token-here
EOF

# 2. Update docker-compose.yml to include these
# Edit docker-compose.yml under backend.environment:
# Add:
#   OPENAI_API_KEY: ${OPENAI_API_KEY:-}
#   ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
#   HUGGING_FACE_HUB_TOKEN: ${HUGGING_FACE_HUB_TOKEN:-}

# 3. Recreate backend
docker-compose up -d backend

# 4. Test
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Emergency test" \
  -F "model_id=gpt-4-turbo"
```

#### Step 2: Verify LLM Service Fallback Logic

Check that `backend/app/services/llm_service.py` has fallback:

```python
async def get_openai_client(self):
    """Get OpenAI client with fallback to environment variable."""
    try:
        # Try database first
        api_key = await self.secrets_service.get_active_api_key(
            provider="openai",
            db=self.db
        )
    except Exception as e:
        logger.warning(f"Failed to get API key from database: {e}")
        api_key = None

    # Fallback to environment variable
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        logger.info("Using OPENAI_API_KEY from environment variable")

    if api_key:
        return OpenAI(api_key=api_key)

    raise ValueError("No OpenAI API key found in database or environment")
```

**If this fallback is NOT in your code**, add it immediately:

```bash
# Edit backend/app/services/llm_service.py
# Add the fallback logic shown above

# Restart backend
docker-compose restart backend
```

#### Step 3: Reset Encryption System

**WARNING**: This will DELETE all API keys from the database!

```bash
# 1. Generate new MASTER_ENCRYPTION_KEY
NEW_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "New MASTER_ENCRYPTION_KEY: $NEW_KEY"

# 2. Update .env
sed -i "s/MASTER_ENCRYPTION_KEY=.*/MASTER_ENCRYPTION_KEY=$NEW_KEY/" .env
# Or manually edit: MASTER_ENCRYPTION_KEY=<new_key>

# 3. Clear old encrypted keys from database
docker-compose exec postgres psql -U postgres -d ragchatbot -c "TRUNCATE TABLE api_keys CASCADE;"

# 4. Restart backend
docker-compose up -d backend

# 5. Re-add API keys via UI or API
curl -X POST http://localhost:8000/api/v1/admin/secrets/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "key_name": "new-production-key",
    "api_key": "sk-proj-your-key-here"
  }'

# 6. Test
curl http://localhost:8000/api/v1/admin/secrets/api-keys
```

#### Step 4: Document What Happened

```bash
# Create incident report
cat > INCIDENT_REPORT_$(date +%Y%m%d).md << 'EOF'
# Encryption Key Loss Incident Report

**Date**: $(date)
**Issue**: Lost MASTER_ENCRYPTION_KEY
**Impact**: Unable to decrypt API keys from database

## Actions Taken:
1. Reverted to environment variable fallback
2. Generated new MASTER_ENCRYPTION_KEY: <redacted>
3. Cleared old encrypted keys from database
4. Re-added API keys via admin UI

## Root Cause:
<describe what happened>

## Prevention Measures:
1. Store MASTER_ENCRYPTION_KEY in password manager
2. Create encrypted backup on USB drive
3. Add to disaster recovery documentation
4. Set calendar reminder for quarterly key rotation

## Lessons Learned:
<document learnings>
EOF
```

### Scenario: Database Corruption

**Impact**:
- ❌ Cannot read api_keys table
- ✅ Can still use environment variable fallback

**Recovery**:

```bash
# 1. Verify database is corrupted
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT * FROM api_keys;"
# If error: table doesn't exist or data corruption

# 2. Restore from backup
# (If you have database backups)
docker-compose exec postgres pg_restore -U postgres -d ragchatbot /backups/latest.dump

# 3. If no backups, recreate table
docker-compose exec postgres psql -U postgres -d ragchatbot << 'EOF'
DROP TABLE IF EXISTS api_keys CASCADE;

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL,
    key_name VARCHAR(100) NOT NULL,
    encrypted_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    last_used TIMESTAMP WITH TIME ZONE,
    UNIQUE(provider, key_name)
);
EOF

# 4. Re-add API keys
# (Via UI or API - see Step 3 of previous scenario)
```

### Scenario: Accidental Key Deletion

**Impact**:
- ❌ Specific API key deleted from database
- ⚠️ LLM requests using that provider will fail
- ✅ Can re-add the key

**Recovery**:

```bash
# 1. Check what was deleted
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT provider, key_name, created_at FROM api_keys WHERE is_active = false ORDER BY created_at DESC LIMIT 5;"

# 2. Re-add the key via UI or API
curl -X POST http://localhost:8000/api/v1/admin/secrets/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "key_name": "recovered-key",
    "api_key": "sk-proj-your-key-here"
  }'

# 3. Verify
curl http://localhost:8000/api/v1/admin/secrets/api-keys
```

---

## Best Practices

### Security Best Practices

1. **Encryption Key Management**
   - ✅ Store MASTER_ENCRYPTION_KEY in password manager
   - ✅ Create encrypted backup on USB drive
   - ✅ Never commit to git (even in private repos)
   - ✅ Rotate every 90 days
   - ✅ Use different keys for dev/staging/prod

2. **Access Control**
   - ✅ Limit admin dashboard access
   - ✅ Implement JWT authentication for API keys endpoint
   - ✅ Log all API key operations
   - ✅ Use RBAC (Role-Based Access Control)

3. **Monitoring**
   - ✅ Alert on failed decryption attempts
   - ✅ Monitor API key usage patterns
   - ✅ Track API key creation/deletion
   - ✅ Set up audit log reviews

4. **Backup Strategy**
   - ✅ Backup PostgreSQL database daily
   - ✅ Test restore procedure monthly
   - ✅ Store backups in encrypted format
   - ✅ Keep backups in multiple locations

### Operational Best Practices

1. **Key Rotation Schedule**
   ```
   Frequency: Every 90 days
   Next rotation: <set date 90 days from now>
   Procedure: See "Key Rotation Procedure" section
   Testing: Verify on staging environment first
   ```

2. **Disaster Recovery Plan**
   ```
   RTO (Recovery Time Objective): 1 hour
   RPO (Recovery Point Objective): 24 hours

   Checklist:
   - [ ] MASTER_ENCRYPTION_KEY backed up in 3 locations
   - [ ] Database backups tested monthly
   - [ ] Fallback to env variables tested
   - [ ] Team trained on recovery procedure
   ```

3. **Change Management**
   ```
   Before making changes:
   1. Test on staging environment
   2. Backup current .env and database
   3. Document what you're changing
   4. Have rollback plan ready
   5. Notify team of maintenance window
   ```

4. **Documentation Maintenance**
   ```
   Update this document when:
   - Adding new API providers
   - Changing encryption algorithm
   - Modifying key storage location
   - After any incident

   Review frequency: Quarterly
   ```

---

## Quick Reference Card

**Common Commands**:

```bash
# Check if encryption key is loaded
docker exec rag-backend printenv | grep MASTER_ENCRYPTION_KEY

# Test API keys endpoint
curl http://localhost:8000/api/v1/admin/secrets/api-keys

# Add new API key
curl -X POST http://localhost:8000/api/v1/admin/secrets/api-keys \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","key_name":"prod","api_key":"sk-proj-..."}'

# Generate new encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d)

# Restart backend
docker-compose up -d backend

# View backend logs
docker-compose logs -f backend
```

**Emergency Contacts**:
```
Primary Admin: <your-email>
Backup Admin: <backup-email>
Password Manager: <location>
Backup Location: <USB drive location>
```

**File Locations**:
```
Encryption Key: .env (MASTER_ENCRYPTION_KEY)
Docker Config: docker-compose.yml
Backend Service: backend/app/services/secrets_service.py
LLM Service: backend/app/services/llm_service.py
Database Backups: /path/to/backups/
Documentation: MASTER_ENCRYPTION_KEY_SETUP.md (this file)
```

---

## Appendix: Migration Timeline

### Original System (Before Encryption)

```
User Request
     ↓
LLM Service
     ↓
os.getenv("OPENAI_API_KEY")  ← Read from .env
     ↓
OpenAI Client
     ↓
API Call
```

**Pros**: Simple, no database dependency
**Cons**: Insecure, no audit trail, requires restarts

### Transition System (Current - FIXED AND WORKING)

```
User Request
     ↓
LLM Service
     ↓
🔐 Attempting to load API key from encrypted database...
     ↓
Try Database First → SecretsService.decrypt() → Use API Key
     ↓                                              ↓
✅ Success?                                       📊 Log source: "ENCRYPTED DATABASE"
     ↓ No                                            ↓
⚠️  Fallback to environment                       API Call
     ↓
os.getenv("OPENAI_API_KEY")  ← Still available!
     ↓
✅ Using environment variable
     ↓
📊 Log source: "ENVIRONMENT VARIABLE"
     ↓
OpenAI Client
     ↓
API Call
```

**Pros**: Secure + graceful fallback + logging + TESTED AND WORKING
**Cons**: Dual system (slight complexity, but provides resilience)

### Future System (Recommended)

```
User Request
     ↓
LLM Service
     ↓
Database ONLY → SecretsService.decrypt() → Use API Key
                                             ↓
                                          API Call

(No environment variable fallback)
```

**Pros**: Single source of truth, fully secure
**Cons**: Database becomes critical dependency

---

**End of Documentation**

**Last Updated**: 2025-11-20 (Evening - All fixes applied and tested)
**Next Review**: 2026-02-20 (90 days)
**Version**: 2.0.0

---

## 📝 Change Log

### Version 2.0.0 (2025-11-20 Evening)

**Critical Fixes Applied**:

1. **HTTP 422 Error When Pulling Ollama Models** ✅ FIXED
   - File: `/backend/app/api/routes/ollama_models.py` line 191
   - Changed `request: PullModelRequest` to `model_name: str = Body(..., embed=True)`
   - Resolved FastAPI parameter naming conflict

2. **"Failed to load API keys" Error** ✅ FIXED
   - File: `docker-compose.yml` line 247
   - Added `MASTER_ENCRYPTION_KEY: ${MASTER_ENCRYPTION_KEY:-}` to backend environment
   - Backend now correctly loads encryption key from .env

3. **Database Error When Saving API Keys** ✅ FIXED
   - Database schema updated:
     ```sql
     ALTER TABLE api_credentials ADD COLUMN IF NOT EXISTS meta_info JSONB DEFAULT '{}'::jsonb;
     ALTER TABLE api_credentials ALTER COLUMN api_key_encrypted TYPE TEXT;
     ```
   - Fixed missing column and data type mismatch issues

4. **No Fallback When Database Fails** ✅ IMPLEMENTED
   - File: `/backend/app/services/llm_service.py`
   - Implemented complete fallback chain (database → environment variable)
   - Added comprehensive logging with emojis to indicate API key source
   - Logs show: "ENCRYPTED DATABASE" or "ENVIRONMENT VARIABLE"

**Testing Results**:
- ✅ API keys can be saved via UI and API
- ✅ API keys can be retrieved and decrypted
- ✅ Encrypted keys stored correctly in database (base64 Fernet encryption)
- ✅ Fallback logic works when database unavailable
- ✅ Logging shows API key source for debugging
- ✅ Ollama model management fully functional

**Database Schema Updates**:
```
Table "public.api_credentials"
      Column       |           Type           | Status
-------------------+--------------------------+----------
 meta_info         | jsonb                    | ✅ ADDED
 api_key_encrypted | text                     | ✅ FIXED (was bytea)
```

**Files Modified**:
- `/backend/app/api/routes/ollama_models.py`
- `/backend/app/services/llm_service.py`
- `docker-compose.yml`
- Database schema (via SQL ALTER TABLE)

---

### Version 1.0.0 (2025-11-20 Morning)

**Initial Documentation**:
- Created comprehensive API key management guide
- Documented historical evolution from hardcoded to encrypted keys
- Added emergency fallback procedures
- Documented key rotation and disaster recovery

---
