"""
Teams and Projects API Routes
Manages organizational hierarchy, projects, and team memberships.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from app.core.database import get_db
from app.api.routes.auth import get_current_user

# Import models from correct modules
try:
    from app.models.database_enhanced import User
except ImportError:
    try:
        from app.models.database import User
    except ImportError:
        User = None

try:
    from app.models.rbac import Department, Team
except ImportError:
    Department = None
    Team = None

try:
    from app.models.database_enhanced import Project, ProjectMember
except ImportError:
    try:
        from app.models.database import Project, ProjectMember
    except ImportError:
        Project = None
        ProjectMember = None

router = APIRouter(prefix="/api/v1", tags=["teams-projects"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class DepartmentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    id: str
    name: str
    code: str
    department_id: str
    department_name: Optional[str] = None
    description: Optional[str] = None
    team_lead_id: Optional[str] = None
    team_lead_username: Optional[str] = None
    member_count: int = 0
    is_active: bool

    class Config:
        from_attributes = True


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    department_id: str
    team_id: str


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|archived|closed)$")


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    owner_username: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    file_count: int = 0
    total_size: int = 0

    class Config:
        from_attributes = True


# ============================================================================
# Departments Endpoints
# ============================================================================

@router.get("/departments", response_model=List[DepartmentResponse])
async def get_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all active departments"""
    result = await db.execute(
        select(Department)
        .where(Department.is_active == True)
        .order_by(Department.name)
    )
    departments = result.scalars().all()

    # Convert to response model
    return [
        DepartmentResponse(
            id=str(dept.id),
            name=dept.name,
            description=dept.description,
            is_active=dept.is_active
        )
        for dept in departments
    ]


# ============================================================================
# Teams Endpoints
# ============================================================================

@router.get("/teams", response_model=List[TeamResponse])
async def get_teams(
    department_id: Optional[str] = Query(None, description="Filter by department"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all teams, optionally filtered by department.

    Used by frontend to populate team dropdown when user selects department.
    """
    query = select(Team).where(Team.is_active == True)

    if department_id:
        query = query.where(Team.department_id == department_id)

    query = query.order_by(Team.name)

    result = await db.execute(query)
    teams = result.scalars().all()

    # Enrich with department names and member counts
    enriched_teams = []
    for team in teams:
        # Get department name
        dept_result = await db.execute(
            select(Department).where(Department.id == team.department_id)
        )
        dept = dept_result.scalar_one_or_none()

        # Get team lead username
        team_lead_username = None
        if team.team_lead_id:
            lead_result = await db.execute(
                select(User).where(User.id == team.team_lead_id)
            )
            lead = lead_result.scalar_one_or_none()
            if lead:
                team_lead_username = lead.username

        # Get project count for this team (users don't have team_id, projects do)
        project_count_result = await db.execute(
            select(func.count(Project.id))
            .where(Project.team_id == team.id)
        )
        project_count = project_count_result.scalar() or 0

        enriched_teams.append(TeamResponse(
            id=str(team.id),
            name=team.name,
            code=team.code,
            department_id=str(team.department_id),
            department_name=dept.name if dept else None,
            description=team.description,
            team_lead_id=str(team.team_lead_id) if team.team_lead_id else None,
            team_lead_username=team_lead_username,
            member_count=project_count,  # Changed to project_count
            is_active=team.is_active
        ))

    return enriched_teams


# ============================================================================
# Projects Endpoints
# ============================================================================

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project.

    Department and team are auto-populated from user profile in frontend,
    but can be overridden if user has permissions.
    """
    # Verify department and team exist
    dept_result = await db.execute(
        select(Department).where(Department.id == request.department_id)
    )
    dept = dept_result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    team_result = await db.execute(
        select(Team).where(Team.id == request.team_id)
    )
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Verify team belongs to department
    if str(team.department_id) != request.department_id:
        raise HTTPException(
            status_code=400,
            detail="Team does not belong to the selected department"
        )

    # Create project
    project = Project(
        id=uuid.uuid4(),
        name=request.name,
        description=request.description,
        owner_id=current_user.id,
        department_id=request.department_id,
        team_id=request.team_id,
        status='active'
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Add creator as project member
    member = ProjectMember(
        id=uuid.uuid4(),
        project_id=project.id,
        user_id=current_user.id,
        role='owner'
    )
    db.add(member)
    await db.commit()

    # Return enriched response
    return await _enrich_project_response(project, db)


@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(
    status: Optional[str] = Query(None, pattern="^(active|archived|closed)$"),
    department_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all projects accessible by current user.

    Returns projects where user is:
    - Owner
    - Member
    - In same department (if role allows)
    """
    query = select(Project)

    # Filter by user access (owner or member)
    query = query.where(
        or_(
            Project.owner_id == current_user.id,
            Project.id.in_(
                select(ProjectMember.project_id)
                .where(ProjectMember.user_id == current_user.id)
            )
        )
    )

    # Apply filters
    if status:
        query = query.where(Project.status == status)
    if department_id:
        query = query.where(Project.department_id == department_id)
    if team_id:
        query = query.where(Project.team_id == team_id)

    query = query.order_by(Project.updated_at.desc())

    result = await db.execute(query)
    projects = result.scalars().all()

    # Enrich responses
    enriched = []
    for project in projects:
        enriched.append(await _enrich_project_response(project, db))

    return enriched


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project by ID"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check access
    if not await _has_project_access(project, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied")

    return await _enrich_project_response(project, db)


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project (owner or admin only)"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check permission (owner or admin)
    if str(project.owner_id) != str(current_user.id) and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only project owner or admin can update")

    # Update fields
    if request.name is not None:
        project.name = request.name
    if request.description is not None:
        project.description = request.description
    if request.status is not None:
        project.status = request.status

    project.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(project)

    return await _enrich_project_response(project, db)


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete project (owner or admin only)"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check permission
    if str(project.owner_id) != str(current_user.id) and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only project owner or admin can delete")

    await db.delete(project)
    await db.commit()

    return {"message": "Project deleted successfully"}


# ============================================================================
# Helper Functions
# ============================================================================

async def _enrich_project_response(project: Project, db: AsyncSession) -> ProjectResponse:
    """Enrich project with related data"""
    # Get owner username
    owner_result = await db.execute(
        select(User).where(User.id == project.owner_id)
    )
    owner = owner_result.scalar_one_or_none()

    # Get department name (only if department_id is not NULL)
    dept = None
    if project.department_id:
        dept_result = await db.execute(
            select(Department).where(Department.id == project.department_id)
        )
        dept = dept_result.scalar_one_or_none()

    # Get team name (only if team_id is not NULL)
    team = None
    if project.team_id:
        team_result = await db.execute(
            select(Team).where(Team.id == project.team_id)
        )
        team = team_result.scalar_one_or_none()

    # Get file stats
    from app.models.database import Document
    file_count_result = await db.execute(
        select(func.count(Document.id))
        .where(Document.project_id == project.id)
    )
    file_count = file_count_result.scalar() or 0

    file_size_result = await db.execute(
        select(func.sum(Document.file_size))
        .where(Document.project_id == project.id)
    )
    total_size = file_size_result.scalar() or 0

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        owner_id=str(project.owner_id) if project.owner_id else None,
        owner_username=owner.username if owner else None,
        department_id=str(project.department_id) if project.department_id else None,
        department_name=dept.name if dept else None,
        team_id=str(project.team_id) if project.team_id else None,
        team_name=team.name if team else None,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        file_count=file_count,
        total_size=total_size
    )


async def _has_project_access(project: Project, user: User, db: AsyncSession) -> bool:
    """Check if user has access to project"""
    # Owner always has access
    if str(project.owner_id) == str(user.id):
        return True

    # Admin always has access
    if user.role == 'admin':
        return True

    # Check if user is a member
    member_result = await db.execute(
        select(ProjectMember)
        .where(
            and_(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == user.id
            )
        )
    )
    member = member_result.scalar_one_or_none()

    return member is not None


# Chat Session Response Model
class ChatSessionResponse(BaseModel):
    id: str
    session_id: str
    title: Optional[str]
    message_count: int
    last_activity: datetime
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/api/v1/projects/{project_id}/chats", response_model=List[ChatSessionResponse])
async def get_project_chats(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all chat sessions for a specific project
    Returns sessions with message count and last activity
    """
    from app.models.database_enhanced import ChatSession, ConversationMessage

    # Check if project exists
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all sessions for this project with message counts
    query = (
        select(
            ChatSession,
            func.count(ConversationMessage.id).label("message_count")
        )
        .outerjoin(ConversationMessage, ConversationMessage.session_id == ChatSession.id)
        .where(ChatSession.project_id == project_id)
        .group_by(ChatSession.id)
        .order_by(ChatSession.last_activity.desc())
    )

    result = await db.execute(query)
    sessions_with_counts = result.all()

    # Build response
    chats = []
    for session, message_count in sessions_with_counts:
        chats.append(ChatSessionResponse(
            id=str(session.id),
            session_id=session.session_id,
            title=session.title or "Untitled Chat",
            message_count=message_count,
            last_activity=session.last_activity,
            created_at=session.created_at
        ))

    return chats
