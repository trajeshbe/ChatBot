"""
Export Wizard API Routes

FastAPI endpoints for POC Export Wizard functionality.

Endpoints:
- POST /api/v1/export/initiate - Start export process
- GET /api/v1/export/jobs/{job_id} - Get job status
- GET /api/v1/export/jobs - List all jobs
- POST /api/v1/export/jobs/{job_id}/cancel - Cancel job
- GET /api/v1/export/packages - List packages
- GET /api/v1/export/packages/{package_id} - Get package details
- GET /api/v1/export/packages/{package_id}/download - Download package
- GET /api/v1/export/templates - List export templates
- GET /api/v1/export/health - Health check

Author: Claude Code
Date: 2026-01-03
Phase: 1 - Core Export Engine
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.tier_1.infrastructure.database import get_db
from app.models.export_wizard import (
    ExportJob,
    ExportPackage,
    ExportTemplate,
    ExportStatus,
    DeploymentType,
    LicenseTier
)
from app.services.export import PackageBuilder
from sqlalchemy import select, desc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/export", tags=["Export Wizard"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class ExportInitiateRequest(BaseModel):
    """Request to initiate POC export."""
    module_name: str = Field(
        description="Module to export (e.g., 'british_council')",
        examples=["british_council", "cru_mining", "grant_thornton"]
    )
    customer_name: str = Field(
        description="Customer name for licensing",
        examples=["Acme Corporation", "GlobalTech Inc"]
    )
    customer_email: Optional[str] = Field(
        default=None,
        description="Customer contact email"
    )
    deployment_type: DeploymentType = Field(
        default=DeploymentType.DOCKER_COMPOSE,
        description="Type of deployment infrastructure to generate"
    )
    license_tier: LicenseTier = Field(
        default=LicenseTier.PROFESSIONAL,
        description="License tier (starter, professional, enterprise)"
    )
    tenant_id: Optional[str] = Field(
        default=None,
        description="Optional tenant ID for multi-tenant filtering"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for filtering documents"
    )
    options: dict = Field(
        default_factory=dict,
        description="Export options",
        examples=[{
            "include_embeddings": True,
            "include_monitoring": True,
            "include_backups": True,
            "white_label": True,
            "security_level": "advanced",
            "enable_telemetry": False,
            "max_users": 50,
            "license_expiry_days": 365
        }]
    )


class ExportJobResponse(BaseModel):
    """Response with export job details."""
    job_id: str
    job_name: str
    module_name: str
    customer_name: str
    deployment_type: str
    license_tier: str
    status: str
    progress_percentage: float
    current_step: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    package_id: Optional[str]
    package_path: Optional[str]
    package_size_bytes: Optional[int]
    error_message: Optional[str]
    stats: Optional[dict]

    class Config:
        from_attributes = True


class ExportPackageResponse(BaseModel):
    """Response with export package details."""
    package_id: str
    package_name: str
    version: str
    module_name: str
    customer_name: str
    deployment_type: str
    license_tier: str
    package_size_bytes: int
    package_size_mb: float
    checksum_sha256: str
    manifest: dict
    created_at: datetime
    download_count: int
    deployed: bool
    deployment_url: Optional[str]

    class Config:
        from_attributes = True


class ExportTemplateResponse(BaseModel):
    """Response with export template details."""
    template_id: str
    name: str
    display_name: str
    description: Optional[str]
    category: Optional[str]
    deployment_type: str
    license_tier: str
    default_options: dict
    infrastructure_config: dict
    usage_count: int
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get("/health", summary="Health check for Export Wizard")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Status indicating service health
    """
    return {
        "status": "healthy",
        "service": "Export Wizard",
        "components": {
            "configuration_extractor": "ready",
            "document_migrator": "ready",
            "infrastructure_generator": "ready",
            "package_builder": "ready"
        },
        "supported_deployments": [dt.value for dt in DeploymentType]
    }


# ============================================================================
# Export Job Endpoints
# ============================================================================

@router.post(
    "/initiate",
    response_model=ExportJobResponse,
    summary="Initiate POC export",
    description="""
    Start the POC export process.

    This endpoint initiates a complete export including:
    1. Configuration extraction
    2. Document and embedding export
    3. Infrastructure generation
    4. License key generation
    5. Package creation

    The process runs asynchronously. Use the job_id to check status.
    """
)
async def initiate_export(
    request: ExportInitiateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> ExportJobResponse:
    """
    Initiate POC export process.

    Args:
        request: Export configuration
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        ExportJobResponse with job details

    Raises:
        HTTPException: If export initiation fails
    """
    try:
        logger.info(f"🚀 Initiating export for module: {request.module_name}")
        logger.info(f"   Customer: {request.customer_name}")
        logger.info(f"   Deployment: {request.deployment_type.value}")

        # Create initial job record
        from app.models.export_wizard import ExportJob as ExportJobModel
        job = ExportJobModel(
            job_name=f"{request.customer_name}_{request.module_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            tenant_id=request.tenant_id or "default",
            module_name=request.module_name,
            deployment_type=request.deployment_type,
            license_tier=request.license_tier,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            options=request.options,
            status=ExportStatus.PENDING,
            progress_percentage=0.0,
            current_step="Queued for export"
        )

        db.add(job)
        await db.commit()
        await db.refresh(job)

        logger.info(f"✅ Created export job: {job.id}")

        # Create package builder with a NEW database session for background task
        from app.tier_1.infrastructure.database import AsyncSessionLocal

        async def run_export_task():
            """Run export in background with its own DB session."""
            async with AsyncSessionLocal() as task_db:
                try:
                    builder = PackageBuilder(task_db)
                    await builder.build_export_package(
                        module_name=request.module_name,
                        customer_name=request.customer_name,
                        deployment_type=request.deployment_type,
                        license_tier=request.license_tier,
                        tenant_id=request.tenant_id,
                        session_id=request.session_id,
                        options=request.options,
                        created_by=None,  # TODO: Get from auth context
                        job_id=str(job.id)  # Pass existing job ID
                    )
                    logger.info(f"✅ Export task completed for job {job.id}")
                except Exception as e:
                    logger.error(f"❌ Export task failed for job {job.id}: {e}", exc_info=True)
                    # Update job status to failed
                    async with AsyncSessionLocal() as error_db:
                        result = await error_db.execute(
                            select(ExportJobModel).where(ExportJobModel.id == job.id)
                        )
                        failed_job = result.scalar_one_or_none()
                        if failed_job:
                            failed_job.status = ExportStatus.FAILED
                            failed_job.error_message = str(e)
                            await error_db.commit()

        # Start export in background
        background_tasks.add_task(run_export_task)

        return ExportJobResponse(
            job_id=str(job.id),
            job_name=job.job_name,
            module_name=job.module_name,
            customer_name=job.customer_name,
            deployment_type=job.deployment_type.value,
            license_tier=job.license_tier.value,
            status=job.status.value,
            progress_percentage=job.progress_percentage,
            current_step=job.current_step,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            package_id=str(job.export_package_id) if job.export_package_id else None,
            package_path=job.package_path,
            package_size_bytes=job.package_size_bytes,
            error_message=job.error_message,
            stats=job.stats
        )

    except Exception as e:
        logger.error(f"❌ Failed to initiate export: {e}")
        raise HTTPException(status_code=500, detail=f"Export initiation failed: {str(e)}")


@router.get(
    "/jobs/{job_id}",
    response_model=ExportJobResponse,
    summary="Get export job status",
    description="Get the current status and progress of an export job"
)
async def get_export_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
) -> ExportJobResponse:
    """
    Get export job status.

    Args:
        job_id: Export job ID
        db: Database session

    Returns:
        ExportJobResponse with job details

    Raises:
        HTTPException: If job not found
    """
    result = await db.execute(
        select(ExportJob).where(ExportJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail=f"Export job not found: {job_id}")

    return ExportJobResponse(
        job_id=str(job.id),
        job_name=job.job_name,
        module_name=job.module_name,
        customer_name=job.customer_name,
        deployment_type=job.deployment_type.value,
        license_tier=job.license_tier.value,
        status=job.status.value,
        progress_percentage=job.progress_percentage,
        current_step=job.current_step,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        package_id=str(job.export_package_id) if job.export_package_id else None,
        package_path=job.package_path,
        package_size_bytes=job.package_size_bytes,
        error_message=job.error_message,
        stats=job.stats
    )


@router.get(
    "/jobs",
    response_model=List[ExportJobResponse],
    summary="List export jobs",
    description="List all export jobs with optional filtering"
)
async def list_export_jobs(
    module_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[ExportJobResponse]:
    """
    List export jobs with optional filtering.

    Args:
        module_name: Optional module name filter
        status: Optional status filter
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session

    Returns:
        List of ExportJobResponse
    """
    query = select(ExportJob).order_by(desc(ExportJob.created_at))

    if module_name:
        query = query.where(ExportJob.module_name == module_name)

    if status:
        query = query.where(ExportJob.status == status)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return [
        ExportJobResponse(
            job_id=str(job.id),
            job_name=job.job_name,
            module_name=job.module_name,
            customer_name=job.customer_name,
            deployment_type=job.deployment_type.value,
            license_tier=job.license_tier.value,
            status=job.status.value,
            progress_percentage=job.progress_percentage,
            current_step=job.current_step,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            package_id=str(job.export_package_id) if job.export_package_id else None,
            package_path=job.package_path,
            package_size_bytes=job.package_size_bytes,
            error_message=job.error_message,
            stats=job.stats
        )
        for job in jobs
    ]


@router.post(
    "/jobs/{job_id}/cancel",
    summary="Cancel export job",
    description="Cancel a running export job"
)
async def cancel_export_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel running export job.

    Args:
        job_id: Export job ID
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If job not found or cannot be cancelled
    """
    builder = PackageBuilder(db)
    cancelled = await builder.cancel_export_job(job_id)

    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Job not found or cannot be cancelled (already completed/failed)"
        )

    return {"status": "cancelled", "job_id": job_id}


# ============================================================================
# Export Package Endpoints
# ============================================================================

@router.get(
    "/packages",
    response_model=List[ExportPackageResponse],
    summary="List export packages",
    description="List all export packages with optional filtering"
)
async def list_export_packages(
    module_name: Optional[str] = None,
    customer_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> List[ExportPackageResponse]:
    """
    List export packages.

    Args:
        module_name: Optional module name filter
        customer_name: Optional customer name filter
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session

    Returns:
        List of ExportPackageResponse
    """
    query = select(ExportPackage).order_by(desc(ExportPackage.created_at))

    if module_name:
        query = query.where(ExportPackage.module_name == module_name)

    if customer_name:
        query = query.where(ExportPackage.customer_name.ilike(f"%{customer_name}%"))

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    packages = result.scalars().all()

    return [
        ExportPackageResponse(
            package_id=str(pkg.id),
            package_name=pkg.package_name,
            version=pkg.version,
            module_name=pkg.module_name,
            customer_name=pkg.customer_name,
            deployment_type=pkg.deployment_type.value,
            license_tier=pkg.license_tier.value,
            package_size_bytes=pkg.package_size_bytes,
            package_size_mb=round(pkg.package_size_bytes / (1024 * 1024), 2),
            checksum_sha256=pkg.checksum_sha256,
            manifest=pkg.manifest,
            created_at=pkg.created_at,
            download_count=pkg.download_count,
            deployed=pkg.deployed,
            deployment_url=pkg.deployment_url
        )
        for pkg in packages
    ]


@router.get(
    "/packages/{package_id}",
    response_model=ExportPackageResponse,
    summary="Get export package details",
    description="Get detailed information about an export package"
)
async def get_export_package(
    package_id: str,
    db: AsyncSession = Depends(get_db)
) -> ExportPackageResponse:
    """
    Get export package details.

    Args:
        package_id: Export package ID
        db: Database session

    Returns:
        ExportPackageResponse

    Raises:
        HTTPException: If package not found
    """
    result = await db.execute(
        select(ExportPackage).where(ExportPackage.id == package_id)
    )
    pkg = result.scalar_one_or_none()

    if not pkg:
        raise HTTPException(status_code=404, detail=f"Export package not found: {package_id}")

    return ExportPackageResponse(
        package_id=str(pkg.id),
        package_name=pkg.package_name,
        version=pkg.version,
        module_name=pkg.module_name,
        customer_name=pkg.customer_name,
        deployment_type=pkg.deployment_type.value,
        license_tier=pkg.license_tier.value,
        package_size_bytes=pkg.package_size_bytes,
        package_size_mb=round(pkg.package_size_bytes / (1024 * 1024), 2),
        checksum_sha256=pkg.checksum_sha256,
        manifest=pkg.manifest,
        created_at=pkg.created_at,
        download_count=pkg.download_count,
        deployed=pkg.deployed,
        deployment_url=pkg.deployment_url
    )


@router.get(
    "/packages/{package_id}/download",
    summary="Download export package",
    description="Download the export package file (.tar.gz)"
)
async def download_export_package(
    package_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Download export package.

    Args:
        package_id: Export package ID
        db: Database session

    Returns:
        FileResponse with package file

    Raises:
        HTTPException: If package not found or file doesn't exist
    """
    result = await db.execute(
        select(ExportPackage).where(ExportPackage.id == package_id)
    )
    pkg = result.scalar_one_or_none()

    if not pkg:
        raise HTTPException(status_code=404, detail=f"Export package not found: {package_id}")

    # Check if file exists
    import os
    if not os.path.exists(pkg.package_path):
        raise HTTPException(status_code=404, detail="Package file not found on disk")

    # Update download count
    pkg.download_count += 1
    pkg.last_downloaded_at = datetime.utcnow()
    await db.commit()

    # Return file
    return FileResponse(
        path=pkg.package_path,
        media_type="application/gzip",
        filename=f"{pkg.package_name}.tar.gz"
    )


# ============================================================================
# Export Template Endpoints
# ============================================================================

@router.get(
    "/templates",
    response_model=List[ExportTemplateResponse],
    summary="List export templates",
    description="List predefined export templates"
)
async def list_export_templates(
    category: Optional[str] = None,
    deployment_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> List[ExportTemplateResponse]:
    """
    List export templates.

    Args:
        category: Optional category filter
        deployment_type: Optional deployment type filter
        db: Database session

    Returns:
        List of ExportTemplateResponse
    """
    query = select(ExportTemplate).where(ExportTemplate.is_active == True)

    if category:
        query = query.where(ExportTemplate.category == category)

    if deployment_type:
        query = query.where(ExportTemplate.deployment_type == deployment_type)

    result = await db.execute(query)
    templates = result.scalars().all()

    return [
        ExportTemplateResponse(
            template_id=str(tmpl.id),
            name=tmpl.name,
            display_name=tmpl.display_name,
            description=tmpl.description,
            category=tmpl.category,
            deployment_type=tmpl.deployment_type.value,
            license_tier=tmpl.license_tier.value,
            default_options=tmpl.default_options,
            infrastructure_config=tmpl.infrastructure_config,
            usage_count=tmpl.usage_count,
            is_active=tmpl.is_active
        )
        for tmpl in templates
    ]
