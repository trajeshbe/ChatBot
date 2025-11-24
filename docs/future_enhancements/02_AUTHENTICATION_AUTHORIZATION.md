# Enhancement: Authentication & Authorization

**Priority**: 🔴 High (Production Required)
**Effort**: 3-5 days
**Status**: 📋 Planned
**Owner**: TBD
**Dependencies**: None

---

## Problem Statement

Currently, the Enterprise RAG Chatbot has **no authentication or authorization mechanism**. This means:

- Anyone with network access can use the API endpoints
- No user identity tracking or session management
- No ability to restrict access to sensitive features (admin, scraping, document management)
- Audit logs cannot be attributed to specific users
- Cannot enforce tenant isolation or per-user quotas
- Violates enterprise security requirements for production deployment

**Business Impact**: Without auth, the system is unsuitable for multi-user or production environments where security, compliance, and accountability are required.

---

## Current State

### Backend (`backend/app/main.py`)
```python
@router.post("/api/v1/query")
async def query_documents(
    query: QueryRequest,
    db: Session = Depends(get_db)
):
    # NO authentication check
    # NO authorization check
    # Anyone can query
    result = await rag_service.query(...)
    return result
```

### Authentication Flow
**Current**: None ❌
**Required**: JWT-based authentication with refresh tokens ✅

### Authorization Model
**Current**: None ❌
**Required**: Role-Based Access Control (RBAC) ✅

---

## Proposed Solution

Implement a **JWT-based authentication system** with **role-based authorization** that integrates seamlessly with existing FastAPI patterns.

### Architecture Components

1. **Authentication Service** (`app/services/auth_service.py`)
   - User registration, login, logout
   - JWT token generation and validation
   - Password hashing (bcrypt)
   - Refresh token rotation

2. **Authorization Middleware** (`app/core/auth.py`)
   - FastAPI dependency for `get_current_user`
   - Role checking decorators (`@require_role`)
   - Permission-based access control

3. **User Management API** (`app/api/routes/auth.py`)
   - `/auth/register` - User registration
   - `/auth/login` - Get access token
   - `/auth/refresh` - Refresh access token
   - `/auth/logout` - Invalidate tokens
   - `/auth/me` - Get current user info

4. **Database Schema** (already exists in `database_enhanced.py`)
   - `users` table ✅ (already present)
   - `api_keys` table ✅ (for programmatic access)
   - `refresh_tokens` table (NEW - for token rotation)

---

## Implementation Plan

### Phase 1: Core Authentication (2 days)

- [x] User model exists (`app/models/database_enhanced.py`)
- [ ] Create `AuthService` class (`app/services/auth_service.py`)
  - Implement `register_user(username, email, password)`
  - Implement `authenticate_user(username, password)`
  - Implement `create_access_token(user_id, expires_delta)`
  - Implement `create_refresh_token(user_id)`
  - Implement `verify_token(token)`
- [ ] Add password hashing utility
  - Use `passlib[bcrypt]` for secure hashing
  - Add `hash_password()` and `verify_password()` functions
- [ ] Create refresh_tokens table migration
  ```sql
  CREATE TABLE refresh_tokens (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id UUID REFERENCES users(id) ON DELETE CASCADE,
      token_hash VARCHAR(255) NOT NULL,
      expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      revoked BOOLEAN DEFAULT FALSE
  );
  CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
  CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
  ```

### Phase 2: API Integration (1 day)

- [ ] Create auth routes (`app/api/routes/auth.py`)
  ```python
  from app.services.auth_service import AuthService
  from app.core.auth import get_current_user

  @router.post("/auth/register")
  async def register(request: RegisterRequest, db: Session = Depends(get_db)):
      auth_service = AuthService(db)
      user = await auth_service.register_user(...)
      return {"user_id": user.id, "message": "Registration successful"}

  @router.post("/auth/login")
  async def login(request: LoginRequest, db: Session = Depends(get_db)):
      auth_service = AuthService(db)
      tokens = await auth_service.authenticate_user(...)
      return {
          "access_token": tokens.access_token,
          "refresh_token": tokens.refresh_token,
          "token_type": "bearer",
          "expires_in": 3600
      }

  @router.post("/auth/refresh")
  async def refresh(refresh_token: str, db: Session = Depends(get_db)):
      auth_service = AuthService(db)
      new_tokens = await auth_service.refresh_access_token(refresh_token)
      return new_tokens

  @router.post("/auth/logout")
  async def logout(
      refresh_token: str,
      current_user: User = Depends(get_current_user),
      db: Session = Depends(get_db)
  ):
      auth_service = AuthService(db)
      await auth_service.revoke_refresh_token(refresh_token)
      return {"message": "Logged out successfully"}

  @router.get("/auth/me")
  async def get_current_user_info(current_user: User = Depends(get_current_user)):
      return {
          "user_id": current_user.id,
          "username": current_user.username,
          "email": current_user.email,
          "role": current_user.role,
          "is_active": current_user.is_active
      }
  ```

- [ ] Create auth dependency (`app/core/auth.py`)
  ```python
  from fastapi import Depends, HTTPException, status
  from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
  from jose import JWTError, jwt
  from app.models.database_enhanced import User

  security = HTTPBearer()

  async def get_current_user(
      credentials: HTTPAuthorizationCredentials = Depends(security),
      db: Session = Depends(get_db)
  ) -> User:
      token = credentials.credentials
      try:
          payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
          user_id = payload.get("sub")
          if user_id is None:
              raise HTTPException(status_code=401, detail="Invalid token")
      except JWTError:
          raise HTTPException(status_code=401, detail="Invalid token")

      user = db.query(User).filter(User.id == user_id).first()
      if user is None or not user.is_active:
          raise HTTPException(status_code=401, detail="User not found or inactive")

      return user

  def require_role(required_role: str):
      async def role_checker(current_user: User = Depends(get_current_user)):
          if current_user.role != required_role and current_user.role != "admin":
              raise HTTPException(status_code=403, detail="Insufficient permissions")
          return current_user
      return role_checker
  ```

### Phase 3: Protect Existing Endpoints (1-2 days)

- [ ] Add authentication to critical endpoints
  ```python
  # RAG Query
  @router.post("/api/v1/query")
  async def query_documents(
      query: QueryRequest,
      current_user: User = Depends(get_current_user),  # ← ADD
      db: Session = Depends(get_db)
  ):
      result = await rag_service.query(
          query.query,
          session_id=query.session_id,
          user_id=current_user.id  # ← ADD
      )
      return result

  # Document Upload
  @router.post("/api/v1/upload")
  async def upload_document(
      file: UploadFile = File(...),
      current_user: User = Depends(get_current_user),  # ← ADD
      db: Session = Depends(get_db)
  ):
      document = await document_service.process_upload(
          file,
          user_id=current_user.id  # ← ADD
      )
      return document

  # Admin Endpoints
  @router.get("/api/v1/admin/users")
  async def list_users(
      current_user: User = Depends(require_role("admin")),  # ← ADD
      db: Session = Depends(get_db)
  ):
      users = db.query(User).all()
      return users
  ```

- [ ] Update audit logs to include authenticated user
  ```python
  await audit_service.log_action(
      user_id=current_user.id,  # ← Now available
      session_id=session_id,
      action="query",
      details={...}
  )
  ```

---

## Code Examples

### Complete AuthService Implementation

```python
# app/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.database_enhanced import User, RefreshToken
from app.core.config import settings
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.JWT_SECRET_KEY  # From environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None):
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {"sub": str(user_id), "exp": expire, "type": "access"}
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, user_id: str):
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        token_data = {"sub": str(user_id), "exp": expire, "type": "refresh"}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        # Store token hash in database
        token_hash = self.hash_password(token)
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expire
        )
        self.db.add(refresh_token)
        self.db.commit()

        return token

    async def register_user(self, username: str, email: str, password: str, role: str = "user"):
        # Check if user exists
        existing_user = self.db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            raise ValueError("Username or email already exists")

        # Create user
        hashed_password = self.hash_password(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            role=role,
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    async def authenticate_user(self, username: str, password: str):
        user = self.db.query(User).filter(User.username == username).first()

        if not user or not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid username or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        # Generate tokens
        access_token = self.create_access_token(user.id)
        refresh_token = self.create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    async def refresh_access_token(self, refresh_token: str):
        try:
            # Verify refresh token
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            token_type = payload.get("type")

            if token_type != "refresh":
                raise ValueError("Invalid token type")

            # Check if token is revoked
            token_hash = self.hash_password(refresh_token)
            db_token = self.db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False
            ).first()

            if not db_token:
                raise ValueError("Token not found or revoked")

            # Generate new access token
            access_token = self.create_access_token(user_id)

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }

        except JWTError:
            raise ValueError("Invalid refresh token")

    async def revoke_refresh_token(self, refresh_token: str):
        token_hash = self.hash_password(refresh_token)
        db_token = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        if db_token:
            db_token.revoked = True
            self.db.commit()
```

### Environment Configuration

```bash
# .env
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
```

---

## Success Criteria

- ✅ Users can register and login via `/auth/register` and `/auth/login`
- ✅ JWT access tokens are issued and validated correctly
- ✅ Refresh tokens enable token rotation without re-authentication
- ✅ Protected endpoints return 401 Unauthorized without valid token
- ✅ Protected endpoints return 403 Forbidden without required role
- ✅ Admin endpoints only accessible by users with `role="admin"`
- ✅ Audit logs include authenticated `user_id`
- ✅ Token expiration and revocation work correctly
- ✅ Password hashing uses bcrypt with appropriate cost factor
- ✅ All sensitive routes protected with `Depends(get_current_user)`

---

## Testing Strategy

### Unit Tests
```python
# tests/test_auth_service.py
def test_register_user(auth_service):
    user = auth_service.register_user("testuser", "test@example.com", "password123")
    assert user.username == "testuser"
    assert user.password_hash != "password123"  # Hashed

def test_authenticate_user_success(auth_service):
    # Setup: register user
    auth_service.register_user("testuser", "test@example.com", "password123")

    # Test: authenticate
    tokens = auth_service.authenticate_user("testuser", "password123")
    assert "access_token" in tokens
    assert "refresh_token" in tokens

def test_authenticate_user_wrong_password(auth_service):
    auth_service.register_user("testuser", "test@example.com", "password123")

    with pytest.raises(ValueError):
        auth_service.authenticate_user("testuser", "wrongpassword")
```

### Integration Tests
```python
# tests/test_auth_integration.py
def test_protected_endpoint_without_token(client):
    response = client.post("/api/v1/query", json={"query": "test"})
    assert response.status_code == 401

def test_protected_endpoint_with_token(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/api/v1/query", json={"query": "test"}, headers=headers)
    assert response.status_code == 200

def test_admin_endpoint_requires_admin_role(client, user_token, admin_token):
    # User token should fail
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 403

    # Admin token should succeed
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
```

### Manual Testing
```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# Login
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}' | jq -r .access_token)

# Query with token
curl -X POST http://localhost:8000/api/v1/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who is Aadhan?"}'
```

---

## Rollback Plan

If authentication causes issues:

1. **Disable auth temporarily** by removing `Depends(get_current_user)` from endpoints
2. **Rollback database migration** if refresh_tokens table causes issues:
   ```bash
   cd backend
   alembic downgrade -1
   ```
3. **Remove auth routes** from `main.py` router registration
4. **Restore previous state** from git:
   ```bash
   git checkout HEAD~1 backend/app/services/auth_service.py
   git checkout HEAD~1 backend/app/core/auth.py
   ```

---

## Dependencies

- **Python Packages** (add to `requirements.txt`):
  ```
  python-jose[cryptography]==3.3.0  # JWT encoding/decoding
  passlib[bcrypt]==1.7.4            # Password hashing
  python-multipart==0.0.6           # Form data parsing
  ```

- **Database**: Requires `users` table (already exists) + new `refresh_tokens` table

- **Environment Variables**: `JWT_SECRET_KEY` must be set in production

---

## References

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io Introduction](https://jwt.io/introduction)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- Existing implementation: `backend/app/models/database_enhanced.py` (User model)

---

**Last Updated**: 2025-11-24
**Next Review**: After implementation completion

---

**End of Authentication & Authorization Enhancement**
