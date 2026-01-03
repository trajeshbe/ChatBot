# Tier 2 & Tier 3 Module Security Architecture

**Date**: 2026-01-01
**Version**: 1.0.0
**Status**: Design Ready for Implementation

---

## 🔒 Executive Summary

This document defines the **state-of-the-art, enterprise-grade security architecture** for all Tier 2 (domain vertical) and Tier 3 (customer-specific) modules, ensuring:

- ✅ **Role-Based Access Control (RBAC)** at module level
- ✅ **Organizational Hierarchy Integration** (Department → Team → User)
- ✅ **Project-based Data Isolation**
- ✅ **MinIO Path Security** with organizational structure
- ✅ **Comprehensive Audit Logging**
- ✅ **Scalable to 30+ modules**

---

## 🏢 Organizational Hierarchy Integration

### Current RBAC Structure (Already Implemented)

```
Organization (Company-wide)
├── Department (Finance, Engineering, Construction, etc.)
│   ├── Team (DevOps, Data Science, Planning, etc.)
│   │   ├── User (Assigned to team)
│   │   │   ├── Roles (admin, manager, analyst, viewer)
│   │   │   └── Permissions (150+ granular permissions)
│   │   └── Projects (Team-specific or cross-team)
```

### Module Access Control Model

```sql
-- Existing tables (already in database)
users (id, username, email, role, department_id, team_id)
departments (id, name, parent_id)
teams (id, name, department_id)
projects (id, name, department_id, team_id, owner_id)

-- New tables (from Option B - migration 024)
skill_modules (id, module_id, name, tier, status, dependencies)
module_activations (id, module_id, project_id, user_id, enabled)
document_extractions (id, document_id, module_id, user_id, project_id)
extraction_results (id, extraction_id, [18 fields])
```

---

## 🔐 Multi-Level Access Control

### Level 1: Module Availability by Tier
```python
# Each module specifies which organizational levels can access it

MODULE_ACCESS_TIERS = {
    # Tier 2: Domain Verticals - Available to all departments
    "document-extract": {
        "tier": 2,
        "access_level": "organization",  # All users in organization
        "min_role": "viewer",  # Minimum role required
    },

    # Tier 2: Industry-specific - Restricted to specific departments
    "construction-metrics": {
        "tier": 2,
        "access_level": "department",  # Only Construction department
        "allowed_departments": ["Construction", "Engineering", "Planning"],
        "min_role": "analyst",
    },

    # Tier 3: Customer-specific - Restricted to specific teams
    "british-council-poc": {
        "tier": 3,
        "access_level": "team",  # Only specific teams
        "allowed_teams": ["British Council Project Team"],
        "min_role": "analyst",
    }
}
```

### Level 2: Project-based Module Activation

**Database Schema** (from migration 024):
```sql
CREATE TABLE module_activations (
    id UUID PRIMARY KEY,
    module_id VARCHAR(100) REFERENCES skill_modules(module_id),
    project_id UUID REFERENCES projects(id),  -- NULL = global activation
    user_id UUID REFERENCES users(id),        -- NULL = available to all users
    enabled BOOLEAN DEFAULT TRUE,
    activated_at TIMESTAMP,
    activated_by UUID REFERENCES users(id),
    UNIQUE(module_id, project_id, user_id)
);
```

**Access Control Logic**:
```python
def can_user_access_module(user_id: str, module_id: str, project_id: Optional[str] = None) -> bool:
    """
    Multi-level access control check:
    1. Check if module is enabled (skill_modules.status = 'enabled')
    2. Check user's role meets minimum requirement
    3. Check organizational hierarchy access
    4. Check project-specific activation (if project_id provided)
    """

    # 1. Check module exists and is enabled
    module = db.query(SkillModule).filter(SkillModule.module_id == module_id).first()
    if not module or module.status != 'enabled':
        return False

    # 2. Check user's role
    user = db.query(User).filter(User.id == user_id).first()
    if not has_minimum_role(user.role, module.min_role):
        return False

    # 3. Check organizational hierarchy
    if module.access_level == 'department':
        if user.department_id not in module.allowed_departments:
            return False
    elif module.access_level == 'team':
        if user.team_id not in module.allowed_teams:
            return False

    # 4. Check project-specific activation
    if project_id:
        activation = db.query(ModuleActivation).filter(
            ModuleActivation.module_id == module_id,
            ModuleActivation.project_id == project_id,
            or_(
                ModuleActivation.user_id == user_id,
                ModuleActivation.user_id == None  # Global project activation
            ),
            ModuleActivation.enabled == True
        ).first()

        if not activation:
            return False

    return True
```

---

## 📂 MinIO Path Security Architecture

### Unified Path Structure (Already Implemented)

```
minio://chatbot-bucket/
└── {username}/                          # User isolation
    └── {department_name}/               # Department isolation
        └── {team_name}/                 # Team isolation
            └── {project_name}/          # Project isolation
                ├── uploads/             # Original files
                ├── processed/           # Processed documents
                ├── embeddings/          # Vector embeddings
                ├── extractions/         # Module extraction results
                │   ├── docu-extract/    # 18-field extractions
                │   ├── construction-metrics/  # Building metrics
                │   └── {module_id}/     # Other tier 2/3 modules
                └── exports/             # Exported results
```

### Module-specific MinIO Storage

**Per-module Extraction Results Storage**:
```python
def get_module_storage_path(user_id: str, module_id: str, project_id: str, extraction_id: str) -> str:
    """
    Generate secure, isolated storage path for module extraction results
    """
    user = db.query(User).filter(User.id == user_id).first()
    project = db.query(Project).filter(Project.id == project_id).first()
    department = db.query(Department).filter(Department.id == user.department_id).first()
    team = db.query(Team).filter(Team.id == user.team_id).first()

    path = f"{user.username.lower()}/{department.name.lower()}/{team.name.lower()}/{project.name.lower()}/extractions/{module_id}/{extraction_id}.json"

    return path

# Example paths:
# john.doe/construction/planning/downtown-tower/extractions/docu-extract/abc-123.json
# jane.smith/procurement/sourcing/vendor-analysis/extractions/matcher/def-456.json
```

---

## 🔒 Data Isolation Strategies

### 1. **Database-Level Isolation**

**Row-Level Security (RLS)** for all extraction tables:
```sql
-- Enable RLS on extraction_results table
ALTER TABLE extraction_results ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own extractions
CREATE POLICY user_extraction_isolation ON extraction_results
    FOR SELECT
    USING (
        extraction_id IN (
            SELECT id FROM document_extractions
            WHERE user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- Policy: Users can only see extractions for their projects
CREATE POLICY project_extraction_isolation ON extraction_results
    FOR SELECT
    USING (
        extraction_id IN (
            SELECT de.id FROM document_extractions de
            JOIN projects p ON de.project_id = p.id
            JOIN users u ON u.id = current_setting('app.current_user_id')::uuid
            WHERE
                p.id = de.project_id
                AND (
                    p.owner_id = u.id OR
                    p.team_id = u.team_id OR
                    p.department_id = u.department_id
                )
        )
    );

-- Policy: Managers can see all extractions in their department
CREATE POLICY manager_extraction_access ON extraction_results
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.id = current_setting('app.current_user_id')::uuid
            AND u.role IN ('manager', 'admin')
            AND u.department_id IN (
                SELECT DISTINCT de2.project_id
                FROM document_extractions de2
                JOIN projects p2 ON de2.project_id = p2.id
                WHERE de2.id = extraction_results.extraction_id
            )
        )
    );
```

### 2. **API-Level Isolation**

**Middleware for Module Access Control**:
```python
from fastapi import Request, HTTPException, Depends
from app.core.security import get_current_user

async def check_module_access(
    request: Request,
    module_id: str,
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Middleware to check module access before processing request
    """
    # 1. Check module availability
    if not can_user_access_module(current_user.id, module_id, project_id):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: User does not have permission for module '{module_id}'"
        )

    # 2. Check project access (if project_id provided)
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check user's relationship to project
        if not (
            project.owner_id == current_user.id or
            project.team_id == current_user.team_id or
            project.department_id == current_user.department_id or
            current_user.role in ['admin', 'manager']
        ):
            raise HTTPException(
                status_code=403,
                detail="Access denied: User does not have access to this project"
            )

    # 3. Log access attempt for audit
    await log_module_access(
        user_id=current_user.id,
        module_id=module_id,
        project_id=project_id,
        action="access_check",
        status="granted"
    )

    return True

# Apply to all module endpoints
@router.post("/api/v1/modules/{module_id}/extract")
async def extract_module_data(
    module_id: str,
    request: ExtractionRequest,
    current_user: User = Depends(get_current_user),
    _access: bool = Depends(check_module_access)
):
    """Module extraction endpoint with access control"""
    # Access already verified by middleware
    result = await extraction_service.extract(request, module_id, current_user.id)
    return result
```

---

## 📊 Audit Logging for Modules

### Comprehensive Audit Trail

**Audit Events** (extends existing `audit_logs` table):
```python
MODULE_AUDIT_EVENTS = [
    # Module access
    "module.access.granted",
    "module.access.denied",
    "module.activation.created",
    "module.activation.revoked",

    # Extraction events
    "module.extraction.started",
    "module.extraction.completed",
    "module.extraction.failed",
    "module.extraction.exported",

    # Data access
    "module.results.viewed",
    "module.results.downloaded",
    "module.results.shared",

    # Administrative
    "module.enabled",
    "module.disabled",
    "module.permissions.updated"
]
```

**Audit Logging Implementation**:
```python
async def log_module_access(
    user_id: str,
    module_id: str,
    project_id: Optional[str],
    action: str,
    status: str,
    metadata: Optional[dict] = None
):
    """
    Log all module access and operations for compliance and security
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=f"module.{module_id}.{action}",
        resource_type="tier2_module",
        resource_id=module_id,
        status=status,
        metadata={
            "module_id": module_id,
            "project_id": project_id,
            "tier": get_module_tier(module_id),
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {})
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    db.add(audit_log)
    await db.commit()
```

---

## 🔐 Permission System for Modules

### Granular Permissions (Extends Existing RBAC)

**Module-specific Permissions**:
```python
TIER2_PERMISSIONS = {
    # Document Intelligence
    "module.document-extract.view": "View document extraction module",
    "module.document-extract.extract": "Perform 18-field extraction",
    "module.document-extract.export": "Export extraction results",
    "module.document-extract.manage": "Manage module settings",

    # Construction
    "module.construction-metrics.view": "View construction metrics module",
    "module.construction-metrics.extract": "Extract building metrics",
    "module.construction-metrics.export": "Export metrics results",

    # Generic module permissions (apply to all)
    "module.*.view": "View all tier 2 modules",
    "module.*.extract": "Use all tier 2 modules",
    "module.*.manage": "Manage all tier 2 modules",

    # Tier 3 admin
    "module.tier3.manage": "Manage tier 3 customer modules"
}

# Permission-based access check
def check_module_permission(user: User, module_id: str, action: str) -> bool:
    """
    Check if user has specific permission for module action
    """
    required_permission = f"module.{module_id}.{action}"
    wildcard_permission = f"module.*.{action}"

    user_permissions = get_user_permissions(user.id)

    return (
        required_permission in user_permissions or
        wildcard_permission in user_permissions or
        user.role == 'admin'  # Admins have all permissions
    )
```

---

## 🏗️ Implementation Roadmap

### Phase 1: Security Foundation (Week 1)
- ✅ Database tables already created (migration 024)
- ✅ MinIO path structure already implemented
- 📋 Implement `can_user_access_module()` function
- 📋 Implement `check_module_access()` middleware
- 📋 Add module-specific permissions to RBAC

### Phase 2: Data Isolation (Week 2)
- 📋 Implement Row-Level Security policies
- 📋 Add project-based filtering to all queries
- 📋 Implement MinIO access validation
- 📋 Test cross-project data isolation

### Phase 3: Audit & Compliance (Week 3)
- 📋 Implement comprehensive audit logging
- 📋 Add audit dashboard for module access
- 📋 Create compliance reports
- 📋 Test audit trail completeness

### Phase 4: Testing & Validation (Week 4)
- 📋 Security penetration testing
- 📋 Cross-tenant isolation testing
- 📋 Permission boundary testing
- 📋 Performance testing with RLS enabled

---

## 🎯 Security Best Practices

### 1. **Principle of Least Privilege**
- Users only get access to modules they need
- Default deny, explicit grant
- Time-limited access for temporary projects

### 2. **Defense in Depth**
- Multiple layers: API → Database → Storage
- Each layer validates access independently
- No single point of failure

### 3. **Audit Everything**
- Every module access logged
- Every extraction tracked
- Every export recorded
- Compliance-ready audit trails

### 4. **Data Classification**
- Tier 2 modules: Organization-wide (with department filters)
- Tier 3 modules: Customer-specific (strict isolation)
- Sensitive fields: Additional encryption at rest

### 5. **Zero Trust Architecture**
- Verify every request
- Never assume trust based on network
- Continuous validation

---

## 📋 Security Checklist for Each New Module

When implementing a new Tier 2 or Tier 3 module:

**Required Security Controls**:
- [ ] Define `access_level` (organization/department/team)
- [ ] Define `min_role` requirement
- [ ] Implement `check_module_access()` middleware on all endpoints
- [ ] Add Row-Level Security policies for module tables
- [ ] Configure MinIO path structure (`{username}/{dept}/{team}/{project}/extractions/{module_id}/`)
- [ ] Add module-specific permissions to RBAC
- [ ] Implement comprehensive audit logging
- [ ] Add unit tests for access control
- [ ] Add integration tests for data isolation
- [ ] Document security model in module README

---

## 🚀 Example: Secure Module Implementation

```python
# backend/app/tier_2/procurement/matcher_service.py

from app.core.security import check_module_access, get_current_user
from app.services.audit_service import log_module_access

class VendorMatcherService:
    """
    Tier 2 Module: Vendor-Requirement Matching
    Security: Department-level access, project-based isolation
    """

    MODULE_ID = "matcher"
    ACCESS_LEVEL = "department"
    ALLOWED_DEPARTMENTS = ["Procurement", "Finance", "Operations"]
    MIN_ROLE = "analyst"

    async def match_vendors(
        self,
        requirements: dict,
        project_id: str,
        current_user: User = Depends(get_current_user)
    ):
        """
        Match vendors to requirements with full security
        """

        # 1. Access control check
        if not can_user_access_module(
            user_id=current_user.id,
            module_id=self.MODULE_ID,
            project_id=project_id
        ):
            await log_module_access(
                user_id=current_user.id,
                module_id=self.MODULE_ID,
                project_id=project_id,
                action="match_vendors",
                status="denied"
            )
            raise HTTPException(status_code=403, detail="Access denied")

        # 2. Verify project access
        project = await self._get_authorized_project(project_id, current_user.id)

        # 3. Perform matching (with project-scoped data)
        matches = await self._execute_matching(requirements, project.id)

        # 4. Store results with proper isolation
        storage_path = get_module_storage_path(
            user_id=current_user.id,
            module_id=self.MODULE_ID,
            project_id=project.id,
            extraction_id=str(uuid.uuid4())
        )

        await minio_client.put_object(
            bucket="chatbot-bucket",
            object_name=storage_path,
            data=json.dumps(matches)
        )

        # 5. Audit log
        await log_module_access(
            user_id=current_user.id,
            module_id=self.MODULE_ID,
            project_id=project.id,
            action="match_vendors",
            status="completed",
            metadata={
                "requirements_count": len(requirements),
                "matches_found": len(matches),
                "storage_path": storage_path
            }
        )

        return {
            "success": True,
            "matches": matches,
            "storage_path": storage_path
        }

    async def _get_authorized_project(self, project_id: str, user_id: str) -> Project:
        """
        Get project only if user has access (with RLS)
        """
        query = select(Project).where(
            Project.id == project_id,
            or_(
                Project.owner_id == user_id,
                Project.team_id.in_(
                    select(User.team_id).where(User.id == user_id)
                ),
                Project.department_id.in_(
                    select(User.department_id).where(User.id == user_id)
                )
            )
        )

        result = await db.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found or access denied"
            )

        return project
```

---

## ✅ Conclusion

This security architecture provides **enterprise-grade, state-of-the-art protection** for all 30 Tier 2 and Tier 3 modules:

- ✅ **Multi-level Access Control** - Organization → Department → Team → Project
- ✅ **Data Isolation** - Database RLS + MinIO paths + API filters
- ✅ **Comprehensive Auditing** - Every action logged for compliance
- ✅ **Scalable Design** - Ready for 30+ modules without changes
- ✅ **Zero Trust** - Every request verified at multiple layers

**Security is baked into the architecture from day one**, not bolted on later.

---

**Document Version**: 1.0.0
**Last Updated**: 2026-01-01
**Status**: ✅ **READY FOR IMPLEMENTATION**

