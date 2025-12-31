"""
Library API Routes
ChatGPT-style file library for browsing, searching, and managing uploaded files.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.tier_1.infrastructure.database import get_db
from app.api.routes.auth import get_current_user
from app.models.database import Document
from app.tier_1.document_processing.document_service import document_service

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

router = APIRouter(prefix="/api/v1/library", tags=["library"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class FileResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    processed: bool
    processing_status: str

    # Hierarchical organization
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    uploaded_by_id: Optional[str] = None
    uploaded_by_username: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    user_role: Optional[str] = None

    # MinIO path
    minio_path: Optional[str] = None

    # Chunk stats
    chunk_count: int = 0
    has_embeddings: bool = False

    class Config:
        from_attributes = True


class StorageStatsResponse(BaseModel):
    total_files: int
    total_size: int
    total_chunks: int
    by_project: List[dict]
    by_team: List[dict]


# ============================================================================
# Library Endpoints
# ============================================================================

@router.get("/projects/{project_id}/files", response_model=List[FileResponse])
async def get_project_files(
    project_id: str,
    search: Optional[str] = Query(None, description="Search filename"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all files in a project with optional search and filtering.

    Used by Library UI to display files in selected project.
    """
    # Verify project access
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build query
    query = select(Document).where(Document.project_id == project_id)

    # Apply search filter
    if search:
        query = query.where(Document.filename.ilike(f"%{search}%"))

    # Apply file type filter
    if file_type and file_type != 'all':
        query = query.where(Document.file_type == file_type)

    # Order and paginate
    query = query.order_by(desc(Document.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    documents = result.scalars().all()

    # Enrich responses
    enriched = []
    for doc in documents:
        enriched.append(await _enrich_file_response(doc, db))

    return enriched


@router.get("/files", response_model=List[FileResponse])
async def get_user_files(
    search: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all files accessible by current user across all projects.

    Filters:
    - search: Filename search
    - file_type: MIME type filter
    - department_id, team_id, project_id: Hierarchical filters
    """
    # Build query - user's files or files in user's projects
    query = select(Document).where(
        or_(
            Document.uploaded_by == current_user.id,
            Document.project_id.in_(
                select(Project.id).where(
                    or_(
                        Project.owner_id == current_user.id,
                        Project.id.in_(
                            select(ProjectMember.project_id)
                            .where(ProjectMember.user_id == current_user.id)
                        )
                    )
                )
            )
        )
    )

    # Apply filters
    if search:
        query = query.where(Document.filename.ilike(f"%{search}%"))
    if file_type and file_type != 'all':
        query = query.where(Document.file_type == file_type)
    if department_id:
        query = query.where(Document.department_id == department_id)
    if team_id:
        query = query.where(Document.team_id == team_id)
    if project_id:
        query = query.where(Document.project_id == project_id)

    # Order and paginate
    query = query.order_by(desc(Document.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    documents = result.scalars().all()

    # Enrich responses
    enriched = []
    for doc in documents:
        enriched.append(await _enrich_file_response(doc, db))

    return enriched


@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file_details(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific file"""
    result = await db.execute(
        select(Document).where(Document.id == file_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="File not found")

    # Check access
    if not await _has_file_access(document, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied")

    return await _enrich_file_response(document, db)


@router.get("/files/{file_id}/download-url")
async def get_file_download_url(
    file_id: str,
    expires_hours: int = Query(1, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate presigned download URL for a file.

    Returns temporary URL valid for specified hours.
    """
    result = await db.execute(
        select(Document).where(Document.id == file_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="File not found")

    # Check access
    if not await _has_file_access(document, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied")

    # Generate presigned URL
    try:
        url = await document_service.get_file_download_url(
            document_id=file_id,
            db=db,
            expires_hours=expires_hours
        )
        return {"download_url": url, "expires_in_hours": expires_hours}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete file from both MinIO and database.

    Only file uploader or admin can delete.
    """
    result = await db.execute(
        select(Document).where(Document.id == file_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permission (uploader or admin)
    if str(document.uploaded_by) != str(current_user.id) and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only file uploader or admin can delete")

    # Delete file
    try:
        await document_service.delete_file(
            document_id=file_id,
            db=db
        )
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get("/storage/stats", response_model=StorageStatsResponse)
async def get_storage_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get storage statistics for current user.

    Returns:
    - Total files and size
    - Breakdown by project
    - Breakdown by team
    """
    # Total files
    total_files_result = await db.execute(
        select(func.count(Document.id))
        .where(Document.uploaded_by == current_user.id)
    )
    total_files = total_files_result.scalar() or 0

    # Total size
    total_size_result = await db.execute(
        select(func.sum(Document.file_size))
        .where(Document.uploaded_by == current_user.id)
    )
    total_size = total_size_result.scalar() or 0

    # Total chunks
    from app.models.database import DocumentChunk
    total_chunks_result = await db.execute(
        select(func.count(DocumentChunk.id))
        .where(DocumentChunk.uploaded_by == current_user.id)
    )
    total_chunks = total_chunks_result.scalar() or 0

    # By project
    by_project_result = await db.execute(
        select(
            Project.id,
            Project.name,
            func.count(Document.id).label('file_count'),
            func.sum(Document.file_size).label('total_size')
        )
        .join(Document, Document.project_id == Project.id)
        .where(Document.uploaded_by == current_user.id)
        .group_by(Project.id, Project.name)
    )
    by_project = [
        {
            'project_id': str(row.id),
            'project_name': row.name,
            'file_count': row.file_count,
            'total_size': row.total_size
        }
        for row in by_project_result
    ]

    # By team
    by_team_result = await db.execute(
        select(
            Team.id,
            Team.name,
            func.count(Document.id).label('file_count'),
            func.sum(Document.file_size).label('total_size')
        )
        .join(Document, Document.team_id == Team.id)
        .where(Document.uploaded_by == current_user.id)
        .group_by(Team.id, Team.name)
    )
    by_team = [
        {
            'team_id': str(row.id),
            'team_name': row.name,
            'file_count': row.file_count,
            'total_size': row.total_size
        }
        for row in by_team_result
    ]

    return StorageStatsResponse(
        total_files=total_files,
        total_size=total_size,
        total_chunks=total_chunks,
        by_project=by_project,
        by_team=by_team
    )


# ============================================================================
# Helper Functions
# ============================================================================

async def _enrich_file_response(document: Document, db: AsyncSession) -> FileResponse:
    """Enrich file with related metadata"""
    # Get project name
    project_name = None
    if document.project_id:
        project_result = await db.execute(
            select(Project).where(Project.id == document.project_id)
        )
        project = project_result.scalar_one_or_none()
        if project:
            project_name = project.name

    # Get uploader username
    uploader_username = None
    if document.uploaded_by:
        user_result = await db.execute(
            select(User).where(User.id == document.uploaded_by)
        )
        user = user_result.scalar_one_or_none()
        if user:
            uploader_username = user.username

    # Get department name (stored as string in document)
    dept_name = document.department if document.department else None

    # Get team name (stored as string in document)
    team_name = document.team if document.team else None

    # Get chunk stats
    from app.models.database import DocumentChunk
    chunk_count_result = await db.execute(
        select(func.count(DocumentChunk.id))
        .where(DocumentChunk.document_id == document.id)
    )
    chunk_count = chunk_count_result.scalar() or 0

    has_embeddings_result = await db.execute(
        select(func.count(DocumentChunk.id))
        .where(
            and_(
                DocumentChunk.document_id == document.id,
                DocumentChunk.embedding.isnot(None)
            )
        )
    )
    has_embeddings = (has_embeddings_result.scalar() or 0) > 0

    # Determine processing status
    # Document has processing_status field directly ('pending', 'processing', 'completed', 'failed')
    if document.error_message:
        processing_status = 'failed'
    elif document.processing_status:
        processing_status = document.processing_status
    elif chunk_count > 0:
        processing_status = 'completed'
    else:
        processing_status = 'pending'

    # Derive processed boolean from processing_status
    processed = (processing_status == 'completed')

    return FileResponse(
        id=str(document.id),
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        upload_date=document.created_at,  # Document has created_at, not upload_date
        processed=processed,
        processing_status=processing_status,
        project_id=str(document.project_id) if document.project_id else None,
        project_name=project_name,
        uploaded_by_id=str(document.uploaded_by) if document.uploaded_by else None,
        uploaded_by_username=uploader_username,
        department_id=None,  # Not stored as ID, only as string name
        department_name=dept_name,
        team_id=None,  # Not stored as ID, only as string name
        team_name=team_name,
        user_role=document.user_role,
        minio_path=document.minio_path,
        chunk_count=chunk_count,
        has_embeddings=has_embeddings
    )


async def _has_file_access(document: Document, user: User, db: AsyncSession) -> bool:
    """Check if user has access to file"""
    # Uploader always has access
    if str(document.uploaded_by) == str(user.id):
        return True

    # Admin always has access
    if user.role == 'admin':
        return True

    # Check if user has access to the project
    if document.project_id:
        from app.models.database_enhanced import ProjectMember

        project_result = await db.execute(
            select(Project).where(Project.id == document.project_id)
        )
        project = project_result.scalar_one_or_none()

        if project:
            # Check if owner
            if str(project.owner_id) == str(user.id):
                return True

            # Check if member
            member_result = await db.execute(
                select(ProjectMember).where(
                    and_(
                        ProjectMember.project_id == project.id,
                        ProjectMember.user_id == user.id
                    )
                )
            )
            if member_result.scalar_one_or_none():
                return True

    return False
