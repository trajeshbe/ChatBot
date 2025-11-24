# User Session Management Diagnostic Report

**Date**: 2025-11-22
**Issue**: Username not displayed in UI + `created_by` field is NULL in database
**Status**: ❌ **ROOT CAUSE IDENTIFIED**

---

## Executive Summary

The user session management is **completely broken** due to **missing authentication implementation**. This affects:

1. ✅ Username display in UI (not implemented)
2. ✅ User attribution for API credentials (`created_by` = NULL)
3. ✅ Audit logging (user context not tracked)

---

## Root Cause Analysis

### Issue 1: Authentication Placeholder Returns `None`

**File**: `backend/app/api/routes/secrets.py:91-123`

```python
async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Verify that the current user is an admin

    For now, this is a placeholder. In production, you would:
    1. Extract JWT token from Authorization header
    2. Validate token
    3. Fetch user from database
    4. Verify user.role == UserRole.ADMIN
    """
    # PLACEHOLDER: In production, implement proper JWT authentication
    # For now, we'll assume the user is admin for testing

    logger.warning("Using placeholder admin authentication - implement JWT auth in production")

    return None  # ❌ THIS IS THE PROBLEM!
```

**Impact**:
- `current_user` is always `None`
- Line 190: `user_id=current_user.id if current_user else None` → evaluates to `None`
- Database `created_by` field is NULL

---

### Issue 2: Username Not Displayed in UI

**File**: `frontend/src/components/Sidebar.tsx:1-81`

**Current State**: NO username display component

The Sidebar header (lines 22-32) only shows:
- App logo
- "RAG Bot" title
- "Enterprise AI" subtitle

**Missing**: Username display that should show logged-in user

**Evidence**:
```typescript
// frontend/src/pages/index.tsx:13-28
const [currentUser, setCurrentUser] = useState<string>('Anonymous')

useEffect(() => {
  // Username is loaded from localStorage
  const storedUsername = localStorage.getItem('username') || 'Anonymous'
  setCurrentUser(storedUsername)
}, [])
```

**BUT**: `currentUser` state is **NOT passed to Sidebar** and **NOT rendered anywhere**.

---

### Issue 3: No Authentication Headers Sent

**File**: `frontend/src/components/APIKeysManager.tsx:96-99`

When storing API keys, the frontend sends:

```typescript
const payload: StoreAPIKeyRequest = {
  provider: selectedProvider,
  api_key: apiKey
  // ❌ NO user_id
  // ❌ NO Authorization header
  // ❌ NO session token
}

const response = await axios.post(
  `${API_URL}/api/v1/admin/secrets/api-keys`,
  payload
  // ❌ NO headers with auth token
)
```

**Expected**:
```typescript
const response = await axios.post(
  `${API_URL}/api/v1/admin/secrets/api-keys`,
  payload,
  {
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`
    }
  }
)
```

---

## Complete Flow Breakdown

### Current Flow (BROKEN)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Frontend (APIKeysManager.tsx)                                    │
│    - User adds API key via Admin UI                                 │
│    - localStorage has 'username' = "admin" (for display only)       │
│    - axios.post() sends:                                             │
│      {                                                               │
│        "provider": "openai",                                         │
│        "api_key": "sk-test-..."                                      │
│      }                                                               │
│    - ❌ NO Authorization header                                      │
│    - ❌ NO user context                                              │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Backend (secrets.py:142-193)                                      │
│    - Route: POST /api/v1/admin/secrets/api-keys                      │
│    - Dependency: current_user = Depends(require_admin)               │
│                                                                      │
│    async def require_admin():                                        │
│        return None  # ❌ NO REAL AUTHENTICATION                      │
│                                                                      │
│    - current_user = None                                             │
│                                                                      │
│    await secrets_service.store_api_key(                              │
│        provider=payload.provider,                                    │
│        api_key=payload.api_key,                                      │
│        user_id=current_user.id if current_user else None,  # → None │
│        ip_address=ip_address,                                        │
│        user_agent=user_agent                                         │
│    )                                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. SecretsService (secrets_service.py)                               │
│    - Receives user_id = None                                         │
│    - Stores API key with created_by = NULL                           │
│                                                                      │
│    INSERT INTO api_credentials (                                     │
│        provider, api_key_encrypted, created_by, ...                  │
│    ) VALUES (                                                        │
│        'openai', <encrypted_key>, NULL, ...  # ❌ NULL!              │
│    )                                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. Database (api_credentials table)                                  │
│                                                                      │
│  id  | provider  | created_by | created_at                           │
│ -----+-----------+------------+--------------------                  │
│  ... | openai    | NULL       | 2025-11-20 09:18:40  ❌              │
│  ... | anthropic | NULL       | 2025-11-20 09:40:51  ❌              │
└─────────────────────────────────────────────────────────────────────┘
```

### Expected Flow (CORRECT)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Frontend                                                          │
│    - User logs in → receives JWT token                               │
│    - Token stored in localStorage                                    │
│    - axios.post() sends:                                             │
│      Headers: { Authorization: "Bearer <jwt_token>" }                │
│      Body: { provider: "openai", api_key: "sk-..." }                │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Backend                                                           │
│    - require_admin() extracts JWT from Authorization header          │
│    - Validates JWT signature                                         │
│    - Fetches user from database                                      │
│    - Verifies user.role == 'admin'                                   │
│    - Returns User object with id, username, role                     │
│                                                                      │
│    current_user = User(id=uuid(...), username="admin", ...)          │
│                                                                      │
│    await secrets_service.store_api_key(                              │
│        user_id=current_user.id,  # ✅ Real UUID                      │
│        ...                                                           │
│    )                                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. Database                                                          │
│                                                                      │
│  id  | provider  | created_by               | created_at            │
│ -----+-----------+--------------------------+--------------------   │
│  ... | openai    | 123e4567-e89b-12d3-...   | 2025-11-20 09:18:40   │
│  ... | anthropic | 123e4567-e89b-12d3-...   | 2025-11-20 09:40:51   │
│                    ✅ Real user UUID                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Investigation Findings

### 1. Database Evidence

```sql
SELECT id, provider, created_by, created_at
FROM api_credentials
ORDER BY created_at DESC;
```

**Result**:
```
id    | provider  | created_by | created_at
------+-----------+------------+--------------------
uuid1 | openai    | NULL       | 2025-11-20 09:18:40
uuid2 | anthropic | NULL       | 2025-11-20 09:40:51
```

✅ Confirms: Both credentials have `created_by` = NULL

---

### 2. Frontend Username Storage

**File**: `frontend/src/pages/index.tsx:24-26`

```typescript
const storedUsername = localStorage.getItem('username') || 'Anonymous'
setCurrentUser(storedUsername)
```

✅ Username IS stored in localStorage
❌ Username is NOT displayed in UI
❌ Username is NOT sent to backend API calls

---

### 3. Backend Authentication Stub

**Two placeholder implementations found**:

1. `backend/app/api/routes/ollama_models.py:69-71`
```python
async def require_admin():
    """Placeholder for admin authentication (replace with JWT)."""
    pass
```

2. `backend/app/api/routes/secrets.py:91-123`
```python
async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Placeholder - implement JWT auth in production"""
    logger.warning("Using placeholder admin authentication - implement JWT auth in production")
    return None  # ❌ RETURNS NONE
```

---

### 4. Code Locations

| Component | File | Line | Status |
|-----------|------|------|--------|
| **Frontend Username State** | `frontend/src/pages/index.tsx` | 13, 25 | ✅ Working |
| **Frontend Username Display** | `frontend/src/components/Sidebar.tsx` | - | ❌ Missing |
| **Frontend API Call** | `frontend/src/components/APIKeysManager.tsx` | 96-99 | ❌ No auth header |
| **Backend Auth Dependency** | `backend/app/api/routes/secrets.py` | 91-123 | ❌ Returns None |
| **Backend Store API Key** | `backend/app/api/routes/secrets.py` | 186-193 | ⚠️ Expects user_id |
| **Backend Secrets Service** | `backend/app/services/secrets_service.py` | - | ✅ Accepts user_id |
| **Database Schema** | `backend/migrations/004_add_api_credentials.sql` | - | ✅ Supports created_by |

---

## Why This Happened

### Timeline of Events

1. **2025-11-20 09:18:40** - User added OpenAI API key via Admin UI
   - Frontend sent request WITHOUT authentication
   - Backend `require_admin()` returned `None`
   - Database stored `created_by` = NULL

2. **2025-11-20 09:40:51** - User added Anthropic API key via Admin UI
   - Same broken flow
   - Database stored `created_by` = NULL

3. **User noticed**: "username at the top right is not working"
   - Correct observation - username display is missing
   - This is a symptom of incomplete authentication implementation

---

## Test Key Mystery Solved

**User's question**: "how did something like test key happen?"

**Answer**: The test key (`sk-test-********************************wxyz`) was **manually entered via the Admin UI** on 2025-11-20. This was NOT hardcoded:

✅ No hardcoded test keys found in:
- Python source files
- Migration scripts
- Testing scripts
- Environment files

The user likely:
1. Opened Admin UI → API Keys Manager
2. Selected "OpenAI" provider
3. Accidentally entered a test/invalid key instead of the real key
4. Clicked "Save"
5. System stored it with `created_by` = NULL (due to broken auth)

**Valid key exists in `.env`**:
```bash
OPENAI_API_KEY=sk-proj-G2vX...
```

But database keys take precedence, so the invalid test key is being used.

---

## Impact Assessment

### ❌ Broken Features

1. **User Attribution**
   - API credentials: `created_by` = NULL
   - Audit logs: No user tracking
   - Sessions: Not linked to users

2. **Security**
   - No authentication required for admin endpoints
   - Anyone can call `/api/v1/admin/secrets/api-keys`
   - No JWT validation

3. **UI/UX**
   - Username not displayed
   - No user profile/settings
   - No logout functionality

### ✅ Working Features (Despite Broken Auth)

1. **API Key Encryption**
   - Fernet encryption working
   - Keys stored securely in database
   - Decryption working correctly

2. **API Key Usage**
   - LLM service reads keys from database
   - Fallback to .env working
   - OpenAI/Anthropic clients functional

3. **Core Functionality**
   - RAG pipeline working (with local LLM)
   - Document upload working
   - Web scraping working

---

## Recommended Fixes

### Priority 1: Fix Authentication (Backend)

**File**: `backend/app/api/routes/secrets.py:91-123`

Replace placeholder with real authentication:

```python
async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Verify that the current user is an admin"""

    # Extract Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]

    # Validate JWT token (using your JWT library)
    try:
        payload = decode_jwt_token(token)  # Implement this
        user_id = payload.get("user_id")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user
```

### Priority 2: Add Username Display (Frontend)

**File**: `frontend/src/components/Sidebar.tsx`

Add username display in the header section:

```typescript
export default function Sidebar({ activeTab, setActiveTab, currentUser }: Props) {
  // ...

  return (
    <div className="w-64 bg-white dark:bg-slate-900 border-r ...">
      <div className="p-4 border-b ...">
        <div className="flex items-center gap-3">
          {/* Logo */}
          <div className="w-9 h-9 bg-gradient-to-br ...">
            <MessageSquare className="w-5 h-5 text-white" />
          </div>

          <div className="flex-1">
            <h2 className="font-semibold text-slate-900 dark:text-white text-sm">
              RAG Bot
            </h2>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">
              Enterprise AI
            </p>
          </div>
        </div>

        {/* ADD USERNAME DISPLAY HERE */}
        <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
            <User className="w-3.5 h-3.5" />
            <span className="font-medium">{currentUser}</span>
          </div>
        </div>
      </div>

      {/* Rest of sidebar */}
    </div>
  )
}
```

**Update index.tsx to pass currentUser**:

```typescript
<Sidebar
  activeTab={activeTab}
  setActiveTab={setActiveTab}
  currentUser={currentUser}  // ADD THIS
  onRAGSettingsChange={handleRAGSettingsChange}
/>
```

### Priority 3: Send Auth Headers (Frontend)

**File**: `frontend/src/components/APIKeysManager.tsx`

Add authentication headers to all API calls:

```typescript
// Add helper to get auth token
const getAuthToken = (): string | null => {
  return localStorage.getItem('authToken')
}

// Update handleStoreKey
const handleStoreKey = async (e: React.FormEvent) => {
  // ...

  const token = getAuthToken()
  if (!token) {
    setError('Authentication required. Please log in.')
    return
  }

  const response = await axios.post(
    `${API_URL}/api/v1/admin/secrets/api-keys`,
    payload,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  )

  // ...
}
```

### Priority 4: Fix Invalid API Key

**Immediate Action**: Delete invalid test key and re-add valid key

```sql
-- Check current keys
SELECT provider, created_at FROM api_credentials;

-- Delete invalid keys
DELETE FROM api_credentials WHERE provider = 'openai';
DELETE FROM api_credentials WHERE provider = 'anthropic';

-- Re-add via Admin UI after authentication is fixed
-- OR manually insert with proper user_id:
-- INSERT INTO api_credentials (provider, api_key_encrypted, created_by, ...)
-- VALUES ('openai', <encrypted_valid_key>, <admin_user_id>, ...);
```

**User Action**: After deleting, use Admin UI to re-add valid keys (from `.env`)

---

## Verification Steps

After implementing fixes:

### 1. Verify Username Display
```
✓ Open application
✓ Check top-right of sidebar
✓ Should see: "👤 admin" or similar
```

### 2. Verify Authentication
```bash
# Should fail without token
curl -X POST http://localhost:8000/api/v1/admin/secrets/api-keys \
  -d '{"provider":"test","api_key":"test"}'
# Expected: 401 Unauthorized

# Should succeed with valid token
curl -X POST http://localhost:8000/api/v1/admin/secrets/api-keys \
  -H "Authorization: Bearer <valid_jwt>" \
  -d '{"provider":"test","api_key":"test"}'
# Expected: 200 OK
```

### 3. Verify User Attribution
```sql
-- Add a test key via Admin UI
-- Then check database:
SELECT provider, created_by FROM api_credentials ORDER BY created_at DESC LIMIT 1;

-- Should see:
-- provider | created_by (UUID of logged-in user)
-- Expected: created_by is NOT NULL
```

### 4. Verify API Key Fix
```bash
# Test OpenAI chat
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Hello" \
  -F "model_id=gpt-3.5-turbo"

# Should NOT see: AuthenticationError: Incorrect API key
# Should see: Valid response with answer
```

---

## Summary

| Issue | Cause | Impact | Priority | Fix Complexity |
|-------|-------|--------|----------|---------------|
| `created_by` = NULL | `require_admin()` returns `None` | No user attribution | P1 | Medium |
| Username not displayed | Missing UI component | Poor UX | P2 | Easy |
| No auth headers | Frontend doesn't send token | Security risk | P1 | Easy |
| Invalid API key | User manually entered test key | OpenAI chat broken | P3 | Easy |

**Next Steps**:
1. Delete invalid API keys from database
2. Re-add valid keys via Admin UI
3. Implement proper JWT authentication (P1)
4. Add username display to Sidebar (P2)
5. Update frontend to send auth headers (P1)

---

**Report Generated**: 2025-11-22
**Analyzed Files**: 8
**Root Causes Found**: 3
**Recommendations**: 4 priority fixes
