# Secrets Management Analysis - API Keys Configuration

**Date**: 2025-11-20  
**Objective**: Analyze current secrets management and recommend AWS Secrets Manager equivalent

---

## 🔍 Current State

### How API Keys Are Currently Managed

**1. Environment Variables (.env file)**
```bash
# .env.example
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here  # For Claude
HUGGING_FACE_HUB_TOKEN=your-hf-token-here
```

**2. Pydantic Settings (backend/app/core/config.py)**
```python
class Settings(BaseSettings):
    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

**Current Flow**:
1. User creates `.env` file from `.env.example`
2. User manually adds their API keys
3. Backend reads from environment variables
4. Keys are loaded at startup

### ❌ Current Limitations

1. **No Centralized Management**: Keys scattered across `.env` files
2. **No Encryption at Rest**: Keys stored in plain text
3. **No Rotation**: Manual key rotation required
4. **No Access Control**: Anyone with file access can see keys
5. **No Audit Trail**: No logging of who accessed what key
6. **Container Restart Required**: Changes require restart

---

## 💡 Recommended Solutions

### Option 1: **Database-Backed Secrets Management** (Best for Self-Hosted)

**AWS Secrets Manager Equivalent**: PostgreSQL encrypted storage

#### Architecture

```
┌─────────────┐
│   Admin UI  │ ← User adds/updates API keys via frontend
└──────┬──────┘
       │
       v
┌─────────────────────────────────┐
│  Secrets Management Service     │
│  - Encrypt/decrypt keys         │
│  - Store in PostgreSQL          │
│  - Audit access logs            │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────────────────┐
│     PostgreSQL Database         │
│  Table: api_credentials         │
│  ┌────────────────────────────┐ │
│  │ provider | encrypted_key   │ │
│  │ openai   | <encrypted>     │ │
│  │ anthropic| <encrypted>     │ │
│  └────────────────────────────┘ │
└─────────────────────────────────┘
```

#### Implementation

**Database Schema**:
```sql
CREATE TABLE api_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) UNIQUE NOT NULL,  -- 'openai', 'anthropic', 'huggingface'
    api_key_encrypted BYTEA NOT NULL,      -- Encrypted API key
    encryption_key_id VARCHAR(100),         -- For key rotation
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE api_key_access_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,  -- 'created', 'updated', 'accessed', 'deleted'
    ip_address VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Python Service** (`backend/app/services/secrets_service.py`):
```python
from cryptography.fernet import Fernet
import base64

class SecretsService:
    def __init__(self, master_key: str):
        # Master key stored as environment variable (once)
        self.cipher = Fernet(master_key.encode())
    
    async def store_api_key(self, provider: str, api_key: str, user_id: UUID):
        """Store encrypted API key"""
        encrypted_key = self.cipher.encrypt(api_key.encode())
        
        # Store in database
        await db.execute("""
            INSERT INTO api_credentials (provider, api_key_encrypted, created_by)
            VALUES ($1, $2, $3)
            ON CONFLICT (provider) DO UPDATE
            SET api_key_encrypted = $2, updated_at = NOW()
        """, provider, encrypted_key, user_id)
        
        # Log access
        await self._log_access(provider, user_id, 'created')
    
    async def get_api_key(self, provider: str) -> Optional[str]:
        """Retrieve and decrypt API key"""
        row = await db.fetchrow("""
            SELECT api_key_encrypted FROM api_credentials
            WHERE provider = $1 AND is_active = TRUE
        """, provider)
        
        if not row:
            return None
        
        # Decrypt
        decrypted = self.cipher.decrypt(row['api_key_encrypted'])
        
        # Update last used
        await db.execute("""
            UPDATE api_credentials 
            SET last_used_at = NOW()
            WHERE provider = $1
        """, provider)
        
        return decrypted.decode()
```

**Admin API Endpoint**:
```python
@router.post("/api/v1/admin/secrets/api-keys")
async def store_api_key(
    provider: str,
    api_key: str,
    user: User = Depends(require_admin)
):
    """Store encrypted API key"""
    secrets_service = SecretsService(settings.MASTER_ENCRYPTION_KEY)
    await secrets_service.store_api_key(provider, api_key, user.id)
    return {"success": True, "message": f"API key for {provider} stored"}

@router.get("/api/v1/admin/secrets/api-keys/{provider}")
async def get_api_key(
    provider: str,
    user: User = Depends(require_admin)
):
    """Get API key status (NOT the key itself - security)"""
    row = await db.fetchrow("""
        SELECT provider, created_at, updated_at, last_used_at
        FROM api_credentials WHERE provider = $1
    """, provider)
    return row
```

**Usage in LLM Service**:
```python
class LLMService:
    async def get_openai_client(self):
        # Try database first
        api_key = await secrets_service.get_api_key('openai')
        
        # Fallback to environment variable
        if not api_key:
            api_key = settings.OPENAI_API_KEY
        
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        return OpenAI(api_key=api_key)
```

#### Benefits
- ✅ **Encrypted at Rest**: Keys encrypted in database
- ✅ **No Container Restart**: Update keys via API
- ✅ **Access Control**: Admin-only access
- ✅ **Audit Trail**: Full logging of access
- ✅ **User-Friendly**: Update via admin UI
- ✅ **Self-Hosted**: No external dependencies

---

### Option 2: **HashiCorp Vault** (Enterprise-Grade)

For Kubernetes deployments, integrate HashiCorp Vault.

**docker-compose.yml addition**:
```yaml
services:
  vault:
    image: vault:latest
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: myroot
      VAULT_DEV_LISTEN_ADDRESS: 0.0.0.0:8200
    cap_add:
      - IPC_LOCK
```

**Python Integration** (`requirements.txt`):
```
hvac==2.0.0  # HashiCorp Vault client
```

**Usage**:
```python
import hvac

class VaultSecretsService:
    def __init__(self):
        self.client = hvac.Client(url='http://vault:8200')
        self.client.token = os.getenv('VAULT_TOKEN')
    
    def get_api_key(self, provider: str) -> str:
        secret = self.client.secrets.kv.v2.read_secret_version(
            path=f'api-keys/{provider}'
        )
        return secret['data']['data']['key']
```

#### Benefits
- ✅ Industry standard for secrets management
- ✅ Built-in encryption, rotation, access control
- ✅ Kubernetes integration
- ✅ Audit logging
- ❌ Additional infrastructure complexity
- ❌ Learning curve

---

### Option 3: **Kubernetes Secrets** (For K8s Deployments)

For production Kubernetes deployments.

**secrets.yaml**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: llm-api-keys
type: Opaque
stringData:
  openai-api-key: "sk-..."
  anthropic-api-key: "sk-ant-..."
```

**Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  template:
    spec:
      containers:
      - name: backend
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-api-keys
              key: openai-api-key
```

**Update without restart**:
```bash
kubectl create secret generic llm-api-keys \
  --from-literal=openai-api-key=sk-new-key \
  --dry-run=client -o yaml | kubectl apply -f -

# Optionally restart pods
kubectl rollout restart deployment/backend
```

#### Benefits
- ✅ Native Kubernetes integration
- ✅ RBAC controls
- ✅ Can use External Secrets Operator for AWS Secrets Manager
- ❌ Still requires pod restart for updates
- ❌ Not suitable for Docker Compose deployments

---

## 🎯 Recommendation for Your Use Case

**Best Choice: Option 1 - Database-Backed Secrets Management**

### Why?

1. **Your Goal**: "if we give this app to anyone, they should be able to add their own API keys"
   - ✅ Admin UI for easy key management
   - ✅ No need to edit .env files
   - ✅ No container restarts

2. **Self-Hosted Friendly**:
   - ✅ No external dependencies (Vault, AWS)
   - ✅ Works with existing PostgreSQL
   - ✅ Simple encryption with Python cryptography

3. **Security**:
   - ✅ Encrypted at rest
   - ✅ Audit logging
   - ✅ Admin-only access

4. **User Experience**:
   - ✅ Add keys via Admin UI
   - ✅ See key status (not the key itself)
   - ✅ Rotate keys easily

---

## 📋 Implementation Plan

### Phase 1: Database Schema
1. Create `api_credentials` table
2. Create `api_key_access_log` table
3. Add migration script

### Phase 2: Backend Service
1. Create `SecretsService` class
2. Add encryption/decryption methods
3. Add admin API endpoints

### Phase 3: LLM Service Integration
1. Modify `LLMService` to check database first
2. Fallback to environment variables
3. Test with all providers

### Phase 4: Frontend Admin UI
1. Add "API Keys" section to admin dashboard
2. Form to add/update keys
3. Display key status (last used, created date)

### Phase 5: Migration Path
1. Keep `.env` support for backwards compatibility
2. Database keys take precedence
3. Show warning in UI if using .env keys

---

## 🔒 Security Best Practices

1. **Master Encryption Key**:
   - Store as environment variable (NOT in database)
   - Rotate periodically
   - Use strong key generation: `Fernet.generate_key()`

2. **Access Control**:
   - Only admin users can view/update keys
   - Log all access attempts
   - Rate limit API key endpoints

3. **Never Log Decrypted Keys**:
   - Always log `provider` only
   - Mask keys in any output
   - Secure audit logs

4. **API Key Validation**:
   - Test key validity before storing
   - Show last successful use
   - Alert on repeated failures

---

## 📝 Example User Flow

1. **Admin logs in** → Admin dashboard
2. **Clicks "API Keys"** → Shows current status
   ```
   Provider     Status      Last Used        Actions
   ────────────────────────────────────────────────
   OpenAI       ✅ Active   2 hours ago      [Update]
   Anthropic    ❌ Missing  Never            [Add]
   ```
3. **Clicks "Add" for Anthropic**:
   ```
   Add Anthropic API Key
   ─────────────────────
   API Key: [sk-ant-...] (masked input)
   
   [Test Key]  [Save]  [Cancel]
   ```
4. **Saves** → Key encrypted & stored
5. **Users can now use Claude models** without backend restart!

---

## ⚖️ Comparison Table

| Feature | Current (.env) | Database | Vault | K8s Secrets |
|---------|---------------|----------|-------|-------------|
| Encryption at Rest | ❌ | ✅ | ✅ | ✅ |
| UI Management | ❌ | ✅ | ⚠️ | ❌ |
| No Restart Needed | ❌ | ✅ | ✅ | ❌ |
| Audit Logging | ❌ | ✅ | ✅ | ⚠️ |
| Self-Hosted | ✅ | ✅ | ✅ | ✅ |
| Easy Setup | ✅ | ✅ | ❌ | ⚠️ |
| Works with Docker Compose | ✅ | ✅ | ✅ | ❌ |

---

**Recommended**: Implement Database-Backed Secrets Management for best balance of security, usability, and self-hosting friendliness.
