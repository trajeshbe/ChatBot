# MASTER_ENCRYPTION_KEY Setup Guide

**Date**: 2025-11-20
**Feature**: Secure API Key Storage
**Status**: ✅ **CONFIGURED**

---

## 📋 Overview

The `MASTER_ENCRYPTION_KEY` is a critical security component that encrypts API keys stored in the database. This ensures that sensitive credentials (OpenAI API keys, Anthropic API keys, etc.) are never stored in plain text.

### What It Does
- **Encrypts** API keys before storing them in PostgreSQL
- **Decrypts** API keys when retrieving them for use
- Uses **Fernet symmetric encryption** (AES-128 in CBC mode)
- Prevents credential theft if database is compromised

### Where It's Used
- **Backend Service**: `/backend/app/services/secrets_service.py`
- **API Endpoints**: `/api/v1/admin/secrets/*`
- **Frontend UI**: Admin Dashboard → API Keys tab

---

## 🔑 Current Configuration

### Existing Key
Your `.env` file already contains a valid encryption key:

```bash
MASTER_ENCRYPTION_KEY=Tv443mxAGRSYNYSs2B_EmNYEIoA_7EQK6Ga7w0KwBaM=
```

✅ **This key is valid and ready to use.**

### Key Format
- **Length**: 44 characters (base64-encoded 32-byte key)
- **Algorithm**: Fernet (symmetric encryption)
- **Encoding**: Base64 with URL-safe alphabet

---

## 🚀 Setup Instructions

### Option 1: Use Existing Key (Recommended)

Your encryption key is already configured in `.env`. Simply restart the backend container:

```bash
# Restart backend to load environment variable
docker-compose restart backend

# Verify backend loaded the key
docker-compose exec backend env | grep MASTER_ENCRYPTION_KEY

# Test the API keys endpoint
curl http://localhost:8000/api/v1/admin/secrets/api-keys
```

### Option 2: Generate a New Key (Only if needed)

⚠️ **WARNING**: Changing this key will invalidate all previously encrypted API keys in the database.

```bash
# Generate a new key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Example output:
# zk6fxsTUXzPJBezVGa4_vvMjDQ7iFfQ-GFiaw1LSjNA=
```

Then update `.env`:

```bash
MASTER_ENCRYPTION_KEY=your-newly-generated-key-here
```

---

## 🔧 Troubleshooting

### Issue: "MASTER_ENCRYPTION_KEY not set" Error

**Symptom**: Backend logs show:
```
ValueError: MASTER_ENCRYPTION_KEY not set. Generate one with:
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

**Root Cause**: Backend container doesn't have access to the environment variable.

**Solutions**:

#### Solution 1: Restart Backend Container
```bash
docker-compose restart backend
```

#### Solution 2: Rebuild Backend (if restart doesn't work)
```bash
docker-compose build backend --no-cache
docker-compose up -d backend
```

#### Solution 3: Verify docker-compose.yml Configuration

Check that `docker-compose.yml` loads the `.env` file for the backend service:

```yaml
services:
  backend:
    env_file:
      - .env  # Ensure this line exists
    environment:
      - MASTER_ENCRYPTION_KEY=${MASTER_ENCRYPTION_KEY}  # Or this
```

#### Solution 4: Manually Set in docker-compose.yml (Not recommended)

```yaml
services:
  backend:
    environment:
      - MASTER_ENCRYPTION_KEY=Tv443mxAGRSYNYSs2B_EmNYEIoA_7EQK6Ga7w0KwBaM=
```

⚠️ This exposes the key in version control. Use `.env` file instead.

---

## 🧪 Verification Steps

### 1. Check Environment Variable in Container

```bash
# Enter backend container
docker-compose exec backend bash

# Check if key is loaded
echo $MASTER_ENCRYPTION_KEY

# Should output:
# Tv443mxAGRSYNYSs2B_EmNYEIoA_7EQK6Ga7w0KwBaM=
```

### 2. Test API Endpoint

```bash
# List API keys (should return empty array initially)
curl http://localhost:8000/api/v1/admin/secrets/api-keys

# Should return:
# {"api_keys": []}
```

### 3. Test Frontend UI

1. Navigate to: http://localhost:3001/admin
2. Click "API Keys" tab
3. Should see "No API keys configured" instead of an error

---

## 🔐 Security Best Practices

### DO:
✅ Store the key in `.env` file (excluded from git via `.gitignore`)
✅ Use a strong, randomly generated key
✅ Back up the key securely (encrypted password manager, vault)
✅ Rotate the key periodically (requires re-encrypting all API keys)

### DON'T:
❌ Commit the key to version control
❌ Share the key in plain text (email, chat, etc.)
❌ Use a weak or predictable key
❌ Change the key without re-encrypting existing data

---

## 📊 How Encryption Works

### Storing an API Key

```
User Input: "sk-proj-abc123..."
    ↓
Fernet.encrypt(api_key, MASTER_ENCRYPTION_KEY)
    ↓
Database: "gAAAAABf3q2r3..." (encrypted blob)
```

### Retrieving an API Key

```
Database: "gAAAAABf3q2r3..." (encrypted blob)
    ↓
Fernet.decrypt(encrypted_key, MASTER_ENCRYPTION_KEY)
    ↓
Application: "sk-proj-abc123..." (plain text)
```

---

## 🔄 Key Rotation Procedure

If you need to rotate the encryption key:

### Step 1: Backup Current Data

```bash
# Export all API keys (while old key is still active)
docker-compose exec postgres pg_dump -U postgres ragchatbot -t api_keys > backup.sql
```

### Step 2: Generate New Key

```python
from cryptography.fernet import Fernet
new_key = Fernet.generate_key().decode()
print(new_key)
```

### Step 3: Re-encrypt All API Keys

```python
# This script would need to be created
# Pseudocode:
# - Load all encrypted keys from database
# - Decrypt with old key
# - Encrypt with new key
# - Update database
```

### Step 4: Update .env and Restart

```bash
# Update .env with new key
vim .env

# Restart backend
docker-compose restart backend
```

---

## 📝 Related Documentation

- **SecretsService**: `/backend/app/services/secrets_service.py`
- **API Routes**: `/backend/app/api/routes/secrets_routes.py`
- **Environment Setup**: `.env.example`
- **Security Guide**: `CONTRIBUTING.md` (Security section)

---

## ✅ Current Status

- ✅ Encryption key exists in `.env` file
- ✅ Key is valid and properly formatted
- ✅ Backend container loads the key from docker-compose.yml (line 247)
- ✅ Database schema fixed (meta_info column added, api_key_encrypted is TEXT)
- ✅ Fallback logic implemented (tries database first, falls back to .env)
- ✅ Logging added to show API key source (database or environment)
- ✅ API keys can be saved and retrieved via UI and API
- ✅ All fixes tested and verified working

---

## 🎯 Recent Fixes (2025-11-20)

### Issue 1: HTTP 422 Error When Pulling Ollama Models
**Fixed**: `/backend/app/api/routes/ollama_models.py` line 191
- Changed `request: PullModelRequest` to `model_name: str = Body(..., embed=True)`
- FastAPI parameter naming conflict resolved

### Issue 2: "Failed to load API keys" Error
**Fixed**: `docker-compose.yml` line 247
- Added `MASTER_ENCRYPTION_KEY: ${MASTER_ENCRYPTION_KEY:-}` to backend environment
- Backend now loads encryption key correctly

### Issue 3: Database Error When Saving API Keys
**Fixed**: Database schema updated
```sql
-- Added missing column
ALTER TABLE api_credentials ADD COLUMN IF NOT EXISTS meta_info JSONB DEFAULT '{}'::jsonb;

-- Fixed data type mismatch
ALTER TABLE api_credentials ALTER COLUMN api_key_encrypted TYPE TEXT;
```

### Issue 4: No Fallback When Database Fails
**Fixed**: `/backend/app/services/llm_service.py`
- Implemented complete fallback chain:
  1. Try encrypted database first (SecretsService)
  2. Fall back to environment variable (.env file)
- Added comprehensive logging with emojis:
  ```
  🔐 Attempting to load OpenAI API key from encrypted database...
  ✅ Successfully loaded OpenAI API key from ENCRYPTED DATABASE
  📊 API Key Source: ENCRYPTED DATABASE
  ```
  OR
  ```
  ⚠️  Failed to retrieve API key from database: <error>
  ✅ Using OpenAI API key from ENVIRONMENT VARIABLE (.env file)
  📊 API Key Source: ENVIRONMENT VARIABLE
  ```

---

## 🧪 Verification Steps (Updated)

### 1. Check Environment Variable in Container

```bash
# Check if key is loaded
docker-compose exec backend env | grep MASTER_ENCRYPTION_KEY

# Should output:
# MASTER_ENCRYPTION_KEY=Tv443mxAGRSYNYSs2B_EmNYEIoA_7EQK6Ga7w0KwBaM=
```

### 2. Test API Endpoint

```bash
# List API keys (should return empty array initially)
curl http://localhost:8000/api/v1/admin/secrets/api-keys

# Should return:
# []
```

### 3. Test Saving an API Key

```bash
# Save a test API key
curl -s -X POST http://localhost:8000/api/v1/admin/secrets/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-test-1234567890abcdefghijklmnopqrstuvwxyz"
  }'

# Should return:
# {"success": true, "message": "API key for openai created successfully", "provider": "openai", "action": "created"}
```

### 4. Verify Encrypted Key in Database

```bash
# Check that key is encrypted in database
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT provider, LEFT(api_key_encrypted, 50) as encrypted_preview, is_active FROM api_credentials;"

# Should show something like:
# provider |                 encrypted_preview                  | is_active
# ---------+----------------------------------------------------+-----------
# openai   | Z0FBQUFBQnBIdHp3eWQ3SlFuTEtwWnNvQVA1ZWQ5ckdsZ1JDd1... | t
```

### 5. Test Frontend UI

1. Navigate to: http://localhost:3001/admin
2. Click "API Keys" tab
3. Should see the test API key you just created
4. Try adding a new key via the UI
5. Should see success message and updated list

---

## 🆘 Need Help?

If the API keys feature still doesn't work after following this guide:

1. **Check backend logs**:
   ```bash
   docker-compose logs backend | grep -E "API key|encryption|ENCRYPTED"
   ```

2. **Verify environment variable**:
   ```bash
   docker-compose exec backend env | grep MASTER_ENCRYPTION_KEY
   ```

3. **Check database schema**:
   ```bash
   docker-compose exec postgres psql -U postgres -d ragchatbot -c "\d api_credentials"
   ```

4. **Test database connection**:
   ```bash
   docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM api_credentials;"
   ```

5. **Restart backend** (clears cached prepared statements):
   ```bash
   docker-compose restart backend
   ```

---

**Last Updated**: 2025-11-20 (Evening - All fixes applied and tested)
**Tested With**: Backend v1.0.0, Docker Compose v2.x
**Status**: ✅ FULLY OPERATIONAL
