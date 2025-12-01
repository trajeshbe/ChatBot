"""
RBAC Models - Role-Based Access Control
SQLAlchemy ORM models for roles, departments, modules, and permissions
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Role(Base):
    """User roles for RBAC system"""
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text)
    is_system_role = Column(Boolean, default=False)  # Cannot be deleted
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent_role = relationship("Role", remote_side=[id], backref="child_roles")
    permissions = relationship("RoleModulePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role(name='{self.name}', id='{self.id}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "parent_role_id": str(self.parent_role_id) if self.parent_role_id else None,
            "description": self.description,
            "is_system_role": self.is_system_role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Department(Base):
    """Organizational departments and teams"""
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    parent_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    meta_info = Column('meta_info', Text, nullable=True)  # JSONB column in DB

    # Relationships
    parent_department = relationship("Department", remote_side=[id], backref="child_departments")
    user_roles = relationship("UserRole", back_populates="department")

    def __repr__(self):
        return f"<Department(name='{self.name}', id='{self.id}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "parent_department_id": str(self.parent_department_id) if self.parent_department_id else None,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Team(Base):
    """Teams within departments"""
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    team_lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = relationship("Department", backref="teams")

    __table_args__ = (
        UniqueConstraint('department_id', 'name', name='uq_team_department_name'),
    )

    def __repr__(self):
        return f"<Team(name='{self.name}', department_id='{self.department_id}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "code": self.code,
            "department_id": str(self.department_id),
            "team_lead_id": str(self.team_lead_id) if self.team_lead_id else None,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Module(Base):
    """Application modules/features"""
    __tablename__ = "modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column('module_name', String(255), nullable=False)  # Maps to module_name in DB
    code = Column('module_key', String(100), unique=True, nullable=False, index=True)  # Maps to module_key in DB
    description = Column(Text)
    icon = Column(String(50))  # Lucide icon name
    # route = Column(String(100))  # Frontend route (not in current DB - commented out until migration added)
    is_active = Column(Boolean, default=True, index=True)
    display_order = Column(Integer, default=0, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    meta_info = Column('meta_info', Text, nullable=True)  # JSONB column in DB

    # Relationships
    permissions = relationship("RoleModulePermission", back_populates="module", cascade="all, delete-orphan")

    @property
    def route(self):
        """Property to provide route attribute for Pydantic schemas (column not yet in DB)"""
        return None

    def __repr__(self):
        return f"<Module(name='{self.name}', code='{self.code}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "icon": self.icon,
            "route": getattr(self, 'route', None),  # Safely access route (may not exist in DB yet)
            "is_active": self.is_active,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RoleModulePermission(Base):
    """Permissions mapping roles to modules"""
    __tablename__ = "role_module_permissions"
    __table_args__ = (
        UniqueConstraint('role_id', 'module_id', name='uq_role_module'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    can_read = Column(Boolean, default=False, index=True)
    can_write = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    role = relationship("Role", back_populates="permissions")
    module = relationship("Module", back_populates="permissions")

    def __repr__(self):
        return f"<RoleModulePermission(role_id='{self.role_id}', module_id='{self.module_id}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "role_id": str(self.role_id),
            "module_id": str(self.module_id),
            "can_read": self.can_read,
            "can_write": self.can_write,
            "can_delete": self.can_delete,
            "can_share": self.can_share,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserRole(Base):
    """User role assignments"""
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', 'department_id', name='uq_user_role_dept'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    # Note: user relationship defined in User model
    role = relationship("Role", back_populates="user_roles")
    department = relationship("Department", back_populates="user_roles")

    def __repr__(self):
        return f"<UserRole(user_id='{self.user_id}', role_id='{self.role_id}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "role_id": str(self.role_id),
            "department_id": str(self.department_id) if self.department_id else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "assigned_by": str(self.assigned_by) if self.assigned_by else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
        }


# Helper functions for common queries
def get_role_by_name(db, role_name: str) -> Optional[Role]:
    """Get role by name"""
    return db.query(Role).filter(Role.name == role_name).first()


def get_module_by_code(db, module_code: str) -> Optional[Module]:
    """Get module by code"""
    return db.query(Module).filter(Module.code == module_code).first()


def get_user_roles(db, user_id: uuid.UUID) -> List[Role]:
    """Get all active roles for a user"""
    return (
        db.query(Role)
        .join(UserRole)
        .filter(
            UserRole.user_id == user_id,
            UserRole.is_active == True
        )
        .all()
    )


def get_user_permissions(db, user_id: uuid.UUID) -> List[RoleModulePermission]:
    """Get all permissions for a user across all their roles"""
    return (
        db.query(RoleModulePermission)
        .join(Role)
        .join(UserRole)
        .filter(
            UserRole.user_id == user_id,
            UserRole.is_active == True
        )
        .all()
    )


def has_permission(db, user_id: uuid.UUID, module_code: str, permission_type: str = "read") -> bool:
    """
    Check if user has a specific permission for a module

    Args:
        db: Database session
        user_id: User UUID
        module_code: Module code (e.g., 'rag_chat')
        permission_type: Type of permission ('read', 'write', 'delete', 'share')

    Returns:
        bool: True if user has the permission
    """
    module = get_module_by_code(db, module_code)
    if not module:
        return False

    permission_column = f"can_{permission_type}"

    permissions = (
        db.query(RoleModulePermission)
        .join(Role)
        .join(UserRole)
        .filter(
            UserRole.user_id == user_id,
            UserRole.is_active == True,
            RoleModulePermission.module_id == module.id
        )
        .all()
    )

    # User has permission if ANY of their roles grants it
    return any(getattr(perm, permission_column, False) for perm in permissions)
