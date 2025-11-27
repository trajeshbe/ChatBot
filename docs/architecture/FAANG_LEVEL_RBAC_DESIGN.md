# FAANG-Level RBAC Architecture Analysis

**Date**: 2025-11-27
**Purpose**: Evaluate our RBAC design against industry best practices
**Comparison**: Current vs. State-of-the-Art (Google, Meta, Netflix, etc.)

---

## 🏢 Current Situation Analysis

### Our Current Design:

**Problem: Dual User Systems**
```
users table (database_enhanced.py)
├── role ENUM (admin, user, viewer, api_user)  ← Legacy
└── user_roles table (RBAC) ← New system
```

**Issues:**
- ❌ Two sources of truth for roles
- ❌ Enum is inflexible (can't add roles without code change)
- ❌ Potential sync issues between enum and RBAC
- ❌ Maintenance burden (two systems to update)
- ❌ Confusing for developers (which to use?)

---

## 🌟 FAANG-Level Design Patterns

### 1. **Google's IAM Approach**

**Principle**: Everything is a permission, roles are just permission bundles

```sql
-- Clean separation of concerns
users (id, email, name, status)
  ↓
user_principals (user_id, principal_id)  -- Can be users, service accounts, groups
  ↓
principal_roles (principal_id, role_id, scope_id)  -- Roles at different scopes
  ↓
role_permissions (role_id, permission_id)  -- Roles bundle permissions
  ↓
permissions (id, resource_type, action, conditions)  -- Fine-grained
```

**Benefits:**
- ✅ No hardcoded roles
- ✅ Hierarchical (project, org, global scopes)
- ✅ Service accounts = Users (same table)
- ✅ Groups as first-class citizens
- ✅ Policy-based (not just role-based)

### 2. **AWS IAM Pattern**

**Principle**: Policies attached to principals (users, roles, groups)

```sql
-- Flexible policy attachment
principals (id, type, name)  -- Users, Roles, Groups
  ↓
principal_policies (principal_id, policy_id)
  ↓
policies (id, name, document_json)  -- JSON policy documents
  ↓
policy_statements (policy_id, effect, action, resource, condition)
```

**Benefits:**
- ✅ JSON policies (flexible, versionable)
- ✅ Inline vs. managed policies
- ✅ Effect (Allow/Deny) for explicit denials
- ✅ Conditions (time, IP, MFA, etc.)
- ✅ Resource-level permissions

### 3. **Auth0/Okta Pattern**

**Principle**: Claims-based with JWT tokens

```sql
-- Modern identity-first approach
users (id, email, identity_provider)
  ↓
user_claims (user_id, claim_type, claim_value)  -- Flexible attributes
  ↓
role_claims (role_id, claim_type, claim_value)  -- Roles inherit claims
  ↓
application_permissions (app_id, permission, required_claims)
```

**Benefits:**
- ✅ OAuth 2.0 / OIDC compliant
- ✅ JWT tokens contain everything
- ✅ No database lookup per request
- ✅ Federation support
- ✅ Attribute-based access control (ABAC)

### 4. **Netflix's Zuul Pattern**

**Principle**: Edge service with centralized auth

```sql
-- Microservices-ready
users (id, email, metadata_json)
  ↓
user_service_permissions (user_id, service_id, permission_set_json)
  ↓
services (id, name, required_permissions)
  ↓
permission_cache (user_id, service_id, permissions, expires_at)  -- Redis
```

**Benefits:**
- ✅ Service-level isolation
- ✅ Cached permissions (fast)
- ✅ Microservices-friendly
- ✅ GraphQL gateway compatible

---

## 🎯 Recommended Consolidation Strategy

### Option A: **Modern Unified RBAC** (Recommended)

**Consolidate to single, flexible system:**

```sql
-- ============================================================================
-- CONSOLIDATED SCHEMA (FAANG-Level)
-- ============================================================================

-- 1. USERS (Clean, no embedded roles)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255),
    identity_provider VARCHAR(50) DEFAULT 'local',  -- local, google, azure, etc.
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    metadata JSONB,  -- Flexible attributes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- NO role column! Roles come from user_roles table only

-- 2. PRINCIPALS (Users, Service Accounts, Groups)
CREATE TABLE principals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    principal_type VARCHAR(50) NOT NULL,  -- 'user', 'service_account', 'group'
    principal_id UUID NOT NULL,  -- References users.id, service_accounts.id, or groups.id
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(principal_type, principal_id)
);

-- 3. GROUPS (For team-based permissions)
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_group_id UUID REFERENCES groups(id),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. GROUP MEMBERS
CREATE TABLE group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',  -- member, owner, admin
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(group_id, user_id)
);

-- 5. ROLES (Dynamic, no hardcoding)
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    scope VARCHAR(50) DEFAULT 'global',  -- global, org, project, resource
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. PERMISSIONS (Fine-grained)
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_type VARCHAR(100) NOT NULL,  -- 'module', 'document', 'project', etc.
    action VARCHAR(50) NOT NULL,  -- 'read', 'write', 'delete', 'admin', etc.
    scope VARCHAR(50) DEFAULT 'global',
    conditions JSONB,  -- Time-based, IP-based, etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(resource_type, action, scope)
);

-- 7. ROLE PERMISSIONS (Many-to-Many)
CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    grant_option BOOLEAN DEFAULT FALSE,  -- Can delegate permission
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(role_id, permission_id)
);

-- 8. PRINCIPAL ROLES (Flexible assignment)
CREATE TABLE principal_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    principal_id UUID REFERENCES principals(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    scope_type VARCHAR(50) DEFAULT 'global',  -- global, department, project, resource
    scope_id UUID,  -- References departments.id, projects.id, etc.
    granted_by UUID REFERENCES users(id),
    expires_at TIMESTAMPTZ,
    conditions JSONB,  -- Time windows, IP ranges, MFA required, etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(principal_id, role_id, scope_type, scope_id)
);

-- 9. DIRECT PERMISSIONS (For exceptions)
CREATE TABLE principal_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    principal_id UUID REFERENCES principals(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    effect VARCHAR(10) NOT NULL,  -- 'allow' or 'deny'
    scope_type VARCHAR(50),
    scope_id UUID,
    granted_by UUID REFERENCES users(id),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- Explicit denies override role permissions

-- 10. PERMISSION CACHE (Performance)
CREATE TABLE permission_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    principal_id UUID NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    allowed_actions TEXT[],  -- Array of allowed actions
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    UNIQUE(principal_id, resource_type, resource_id)
);
CREATE INDEX idx_permission_cache_expires ON permission_cache(expires_at);

-- 11. AUDIT LOG (Immutable)
CREATE TABLE rbac_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    principal_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    permission_checked VARCHAR(100),
    result VARCHAR(20),  -- 'granted', 'denied'
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_rbac_audit_principal ON rbac_audit_log(principal_id, created_at DESC);
```

**Why This is Better:**

| Feature | Old Design | New Design |
|---------|-----------|------------|
| User roles | Hardcoded enum ❌ | Dynamic table ✅ |
| Flexibility | Limited ❌ | Unlimited ✅ |
| Groups | Not supported ❌ | First-class ✅ |
| Scope | Global only ❌ | Multi-level ✅ |
| Conditions | None ❌ | Time, IP, MFA ✅ |
| Deny rules | Not supported ❌ | Explicit denies ✅ |
| Cache | None ❌ | Built-in ✅ |
| Service accounts | Separate table ❌ | Same as users ✅ |
| Federation | Not supported ❌ | Ready ✅ |

---

## 📊 Migration Path

### Phase 1: Add New Tables (Parallel)
```sql
-- Add modern RBAC tables
-- Keep old users.role enum temporarily
-- Dual-write to both systems
```

### Phase 2: Migrate Data
```sql
-- Migrate existing users
INSERT INTO principals (principal_type, principal_id)
SELECT 'user', id FROM users;

-- Migrate enum roles to role assignments
INSERT INTO principal_roles (principal_id, role_id)
SELECT p.id, r.id
FROM users u
JOIN principals p ON p.principal_id = u.id
JOIN roles r ON LOWER(r.name) = LOWER(u.role::text);
```

### Phase 3: Update Code
```python
# Old way (deprecated)
if user.role == UserRole.ADMIN:
    # ...

# New way
if rbac.has_permission(user.id, 'admin_panel', 'read'):
    # ...
```

### Phase 4: Remove Enum
```sql
-- After all code migrated
ALTER TABLE users DROP COLUMN role;
```

---

## 🎯 State-of-the-Art Features

### 1. **Attribute-Based Access Control (ABAC)**

```sql
-- Permissions based on attributes, not just roles
CREATE TABLE attribute_policies (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    resource_type VARCHAR(100),
    action VARCHAR(50),
    required_attributes JSONB,  -- {user.department: 'engineering', user.level: '>= 3'}
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. **Time-Based Permissions**

```sql
-- Temporary elevated access
INSERT INTO principal_roles (principal_id, role_id, expires_at)
VALUES (user_id, admin_role_id, NOW() + INTERVAL '2 hours');
```

### 3. **Conditional Access**

```json
{
  "conditions": {
    "ip_range": ["10.0.0.0/8", "172.16.0.0/12"],
    "time_window": {
      "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
      "hours": "09:00-17:00"
    },
    "mfa_required": true,
    "geo_location": ["US", "CA", "UK"]
  }
}
```

### 4. **Permission Inheritance**

```sql
-- Hierarchical permissions
Department: Engineering
  ├── Team: Backend
  │   └── User: John (inherits Engineering + Backend permissions)
  └── Team: Frontend
      └── User: Jane (inherits Engineering + Frontend permissions)
```

### 5. **Just-In-Time Access (JIT)**

```python
# Request temporary elevated access
rbac.request_temporary_access(
    user_id=user.id,
    role_id=admin_role_id,
    duration='2h',
    reason='Production incident #1234',
    approver_id=manager.id
)
```

### 6. **Break-Glass Access**

```python
# Emergency access with audit trail
rbac.break_glass_access(
    user_id=user.id,
    resource_id=critical_system_id,
    reason='Critical production issue',
    severity='P0'
)
# Auto-notifies security team
# Auto-expires after incident
```

---

## 🏆 FAANG Comparison Table

| Feature | Our Current | Our RBAC | Google IAM | AWS IAM | Auth0 | Netflix |
|---------|-------------|----------|------------|---------|-------|---------|
| Dynamic roles | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Groups | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Fine-grained | ❌ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| Conditions | ❌ | ❌ | ✅ | ✅ | ✅ | ⚠️ |
| Deny rules | ❌ | ❌ | ✅ | ✅ | ⚠️ | ❌ |
| Time-based | ❌ | ❌ | ✅ | ✅ | ✅ | ⚠️ |
| Hierarchical | ❌ | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| Service accounts | ⚠️ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Federation | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Caching | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Audit | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ✅ |

**Legend:**
- ✅ Fully supported
- ⚠️ Partially supported
- ❌ Not supported

---

## 💡 Recommendation

### For Long-Term Maintenance:

**YES, consolidate!** Here's the optimal path:

**Short-Term (Next 2 weeks):**
1. ✅ Deploy current RBAC (backward compatible)
2. ✅ Start using it for new features
3. ✅ Keep enum for now (safety)

**Medium-Term (Next 2 months):**
1. 🔄 Add Groups support
2. 🔄 Add Permission caching
3. 🔄 Add Conditions (time, IP)
4. 🔄 Migrate all code to use RBAC
5. 🔄 Remove enum column

**Long-Term (6+ months):**
1. 🔮 Add ABAC (attribute-based)
2. 🔮 Add JIT access
3. 🔮 Add Federation (SSO)
4. 🔮 Add Service accounts
5. 🔮 Add Break-glass access

---

## 📈 Complexity vs. Value Analysis

| Approach | Complexity | Maintenance | Scalability | Value |
|----------|------------|-------------|-------------|-------|
| Current (enum) | 🟢 Low | 🔴 High | 🔴 Low | 🔴 Low |
| Our RBAC | 🟡 Medium | 🟡 Medium | 🟢 High | 🟢 High |
| FAANG-level | 🔴 High | 🟢 Low | 🟢 Very High | 🟢 Very High |

**Recommendation:**
- **Start with our RBAC** (good balance)
- **Add FAANG features incrementally** (as needed)
- **Consolidate enum eventually** (remove dual systems)

---

## ✅ Action Plan

### Immediate (This Week):
- [x] Deploy current RBAC (backward compatible)
- [ ] Test thoroughly
- [ ] Document for team

### Next Sprint (2 weeks):
- [ ] Add Groups table
- [ ] Add Permission caching (Redis)
- [ ] Start using RBAC in new code

### Next Month:
- [ ] Migrate existing routes to RBAC
- [ ] Add time-based permissions
- [ ] Add condition support

### Quarter 2:
- [ ] Remove users.role enum
- [ ] Add Federation (SSO)
- [ ] Add Service accounts
- [ ] Full FAANG parity

---

## 🎯 Final Verdict

**YES, consolidate for long-term maintenance!**

**But do it gradually:**
1. Deploy current RBAC ✅ (this week)
2. Parallel systems ⚡ (2 months)
3. Full migration 🎯 (6 months)
4. FAANG-level 🚀 (1 year)

**This gives you:**
- ✅ Safety (can rollback)
- ✅ Flexibility (add features incrementally)
- ✅ Future-proof (FAANG-level ready)
- ✅ Maintainable (single source of truth)

---

**The code is already written and ready to deploy. Want to proceed? 🚀**
