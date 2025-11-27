# Enhancement 1-4: RBAC System Implementation Plan

**Status**: 📋 READY TO START
**Priority**: P0
**Estimated Effort**: 2 weeks
**Dependencies**: ✅ Enhancement 0 (Theme) Complete

---

## 🎯 Overview

Implement a comprehensive Role-Based Access Control (RBAC) system with:
- Hierarchical organizational structure
- Module-based permissions
- User role assignments
- Department management
- Admin UI for management

---

## 📊 Implementation Phases

### **Phase 1: Database Schema** (Days 1-2)
Create RBAC database tables and relationships

#### Tasks:
1. Create migration files
2. Define tables: roles, departments, modules, permissions, user_roles
3. Add foreign key relationships
4. Create indexes for performance
5. Seed initial data

#### Deliverables:
- [ ] `backend/migrations/006_add_rbac_tables.sql`
- [ ] `backend/migrations/007_seed_rbac_data.sql`
- [ ] Migration scripts tested

---

### **Phase 2: Backend Models** (Days 3-4)
Create SQLAlchemy ORM models

#### Tasks:
1. Create Role model
2. Create Department model
3. Create Module model
4. Create RoleModulePermission model
5. Create UserRole model
6. Add relationships between models

#### Deliverables:
- [ ] `backend/app/models/rbac.py`
- [ ] Models tested with queries
- [ ] Relationships working

---

### **Phase 3: RBAC Service** (Days 5-6)
Business logic for permissions and access control

#### Tasks:
1. Create RBAC service class
2. Implement permission checking
3. Implement role hierarchy
4. Implement module access control
5. Add caching for performance

#### Deliverables:
- [ ] `backend/app/services/rbac_service.py`
- [ ] Permission check functions
- [ ] Role hierarchy logic
- [ ] Unit tests

---

### **Phase 4: API Endpoints** (Days 7-8)
REST API for RBAC management

#### Tasks:
1. Roles CRUD endpoints
2. Departments CRUD endpoints
3. Modules CRUD endpoints
4. Permission management endpoints
5. User role assignment endpoints

#### Deliverables:
- [ ] `backend/app/api/routes/rbac_routes.py`
- [ ] API documentation
- [ ] API tests

---

### **Phase 5: Authentication Middleware** (Days 9-10)
Protect routes with permission checks

#### Tasks:
1. Create permission decorator
2. Implement JWT token validation
3. Add user context to requests
4. Create route protection middleware
5. Handle unauthorized access

#### Deliverables:
- [ ] `backend/app/middleware/auth_middleware.py`
- [ ] `backend/app/decorators/permissions.py`
- [ ] Protected routes tested

---

### **Phase 6: Frontend - Admin UI** (Days 11-12)
Admin panel for RBAC management

#### Tasks:
1. Create RoleManager component
2. Create DepartmentManager component
3. Create PermissionMatrix component
4. Create UserRoleAssignment component
5. Add forms for CRUD operations

#### Deliverables:
- [ ] `frontend/src/components/admin/RoleManager.tsx`
- [ ] `frontend/src/components/admin/DepartmentManager.tsx`
- [ ] `frontend/src/components/admin/PermissionMatrix.tsx`
- [ ] Admin page integrated

---

### **Phase 7: Integration & Testing** (Days 13-14)
End-to-end testing and integration

#### Tasks:
1. Integration testing
2. Permission flow testing
3. UI/UX testing
4. Security testing
5. Documentation

#### Deliverables:
- [ ] Integration tests passing
- [ ] Security audit complete
- [ ] Documentation updated

---

## 🗄️ Database Schema Details

### Tables to Create:

#### 1. **roles**
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    parent_role_id UUID REFERENCES roles(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 2. **departments**
```sql
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    parent_department_id UUID REFERENCES departments(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3. **modules**
```sql
CREATE TABLE modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    route VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 4. **role_module_permissions**
```sql
CREATE TABLE role_module_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    module_id UUID REFERENCES modules(id) ON DELETE CASCADE,
    can_read BOOLEAN DEFAULT FALSE,
    can_write BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    can_share BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(role_id, module_id)
);
```

#### 5. **user_roles**
```sql
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    UNIQUE(user_id, role_id, department_id)
);
```

---

## 🏢 Organizational Structure

### Seed Data to Create:

#### Roles:
- Admin (full access)
- CxO (executive access)
- Manager
- User
- Read-only

#### Departments:
- Data Operations
  - Data Team 1-16
- Technology
  - Tech Team 1-12
- Support Functions
  - Marketing
  - Sales
  - HR

#### Modules:
1. RAG Chat
2. Web Scraping
3. Data Extraction
4. Project Estimator
5. File Management
6. Admin Panel
7. Audit Logs
8. Evaluation Metrics
9. Tool Usage Dashboard

---

## 🔒 Permission Model

### Permission Types:
- **can_read**: View module
- **can_write**: Create/edit in module
- **can_delete**: Delete from module
- **can_share**: Share resources

### Default Permissions:

**Admin Role:**
- All modules: read, write, delete, share ✅

**Manager Role:**
- All modules: read, write, share ✅
- No delete permission ❌

**User Role:**
- Chat, Upload, Scrape: read, write ✅
- Admin, Audit: no access ❌

**Read-only Role:**
- All modules: read only ✅

---

## 🛠️ Technical Stack

### Backend:
- SQLAlchemy ORM models
- FastAPI endpoints
- JWT authentication
- Permission decorators
- Caching (Redis)

### Frontend:
- React components
- TypeScript interfaces
- Tailwind CSS (with theme)
- React hooks for auth context

---

## 📝 API Endpoints to Implement

### Roles:
- `GET /api/v1/rbac/roles` - List all roles
- `POST /api/v1/rbac/roles` - Create role
- `GET /api/v1/rbac/roles/{id}` - Get role
- `PUT /api/v1/rbac/roles/{id}` - Update role
- `DELETE /api/v1/rbac/roles/{id}` - Delete role

### Departments:
- `GET /api/v1/rbac/departments` - List departments
- `POST /api/v1/rbac/departments` - Create department
- Similar CRUD operations...

### Modules:
- `GET /api/v1/rbac/modules` - List modules
- `POST /api/v1/rbac/modules` - Register module
- Similar CRUD operations...

### Permissions:
- `GET /api/v1/rbac/permissions/{role_id}` - Get role permissions
- `PUT /api/v1/rbac/permissions/{role_id}` - Update permissions
- `GET /api/v1/rbac/user-permissions/{user_id}` - Get user permissions

### User Roles:
- `POST /api/v1/rbac/assign-role` - Assign role to user
- `DELETE /api/v1/rbac/revoke-role` - Revoke role
- `GET /api/v1/rbac/user-roles/{user_id}` - Get user roles

---

## 🎨 UI Components to Build

### 1. **Admin Dashboard**
Main admin page with tabs:
- Users
- Roles
- Departments
- Permissions
- Modules

### 2. **Role Manager**
- Create/edit roles
- Set role hierarchy
- Delete roles
- View role members

### 3. **Permission Matrix**
Interactive grid:
- Rows: Roles
- Columns: Modules
- Cells: Permission checkboxes (R, W, D, S)

### 4. **User Role Assignment**
- Search users
- Assign roles
- Select department
- View user permissions

### 5. **Department Tree**
- Hierarchical department view
- Add/edit/delete departments
- Move teams between departments

---

## 🔐 Security Considerations

### 1. **Authentication**
- JWT tokens with expiration
- Refresh token mechanism
- Secure password hashing (bcrypt)

### 2. **Authorization**
- Check permissions on every request
- Validate user roles
- Prevent privilege escalation

### 3. **Audit Logging**
- Log all role/permission changes
- Track who assigned roles
- Record access attempts

### 4. **Data Protection**
- Row-level security (users see own department data)
- Column-level masking
- Encrypted sensitive fields

---

## ✅ Testing Strategy

### Unit Tests:
- [ ] RBAC service methods
- [ ] Permission checking logic
- [ ] Role hierarchy resolution

### Integration Tests:
- [ ] API endpoints
- [ ] Permission middleware
- [ ] Database queries

### E2E Tests:
- [ ] User login flow
- [ ] Role assignment workflow
- [ ] Permission denial scenarios

### Security Tests:
- [ ] Authorization bypass attempts
- [ ] SQL injection prevention
- [ ] XSS prevention

---

## 📚 Documentation to Create

1. **Admin Guide**
   - How to create roles
   - How to assign permissions
   - How to manage users

2. **Developer Guide**
   - How to protect routes
   - How to check permissions
   - How to add new modules

3. **API Documentation**
   - Endpoint specifications
   - Request/response examples
   - Error codes

---

## 🎯 Success Criteria

- [ ] All database tables created
- [ ] Seed data loaded
- [ ] API endpoints functional
- [ ] Admin UI working
- [ ] Permission checks enforced
- [ ] Tests passing (>80% coverage)
- [ ] Documentation complete
- [ ] Security audit passed

---

## 🚀 Next Steps

### Step 1: Review This Plan
- Confirm requirements
- Adjust timeline if needed
- Clarify any questions

### Step 2: Start Phase 1
- Create database migrations
- Test migrations locally
- Seed initial data

### Step 3: Iterate Through Phases
- Complete each phase
- Test thoroughly
- Document as you go

---

## ⏱️ Timeline

| Phase | Days | Status |
|-------|------|--------|
| 1. Database Schema | 1-2 | 📋 Planned |
| 2. Backend Models | 3-4 | 📋 Planned |
| 3. RBAC Service | 5-6 | 📋 Planned |
| 4. API Endpoints | 7-8 | 📋 Planned |
| 5. Auth Middleware | 9-10 | 📋 Planned |
| 6. Frontend UI | 11-12 | 📋 Planned |
| 7. Testing | 13-14 | 📋 Planned |

**Total**: 2 weeks (14 days)

---

## 📞 Questions Before Starting?

Consider:
1. Authentication method (JWT? OAuth? SAML?)
2. Default admin credentials
3. Department structure (confirm org chart)
4. Module list (any additions?)
5. Permission granularity (enough with R/W/D/S?)

---

**Ready to begin Phase 1: Database Schema!**

Let me know when to proceed with creating the migration files.
