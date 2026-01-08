"""
Export Wizard API Routes

Purpose: POC-to-Production export package generation with "Full Clone with Filters" strategy

Features:
  - Export complete application with selected module only
  - Automated database sanitization
  - ZIP package generation with installation scripts
  - Module filtering (keep Tier 1 + selected Tier 2/3)

Author: AI Assistant
Date: 2026-01-07
Related: Requirement #10 - Export Wizard Enhancement
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from pathlib import Path
import logging
import asyncio

from app.core.database import get_db
from app.services.export.full_clone_builder import FullCloneExportBuilder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/export-wizard", tags=["Export Wizard"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ExportRequest(BaseModel):
    """Request model for export package generation"""

    module_name: str = Field(..., description="Name of module to export (e.g., 'Relation Extractor')")
    module_tier: int = Field(..., description="Tier of module (2 for Domain Verticals, 3 for Customer Solutions)")
    export_path: Optional[str] = Field("/tmp/exports", description="Base directory for exports")

    class Config:
        json_schema_extra = {
            "example": {
                "module_name": "Relation Extractor",
                "module_tier": 2,
                "export_path": "/tmp/exports"
            }
        }


class ExportResponse(BaseModel):
    """Response model for export package generation"""

    status: str = Field(..., description="Export status: 'started', 'completed', 'failed'")
    message: str = Field(..., description="Human-readable status message")
    export_id: Optional[str] = Field(None, description="Unique export job ID")
    zip_path: Optional[str] = Field(None, description="Path to generated ZIP file (when completed)")
    summary: Optional[dict] = Field(None, description="Export summary statistics")


class ExportStatusResponse(BaseModel):
    """Response model for export status check"""

    export_id: str
    status: str
    progress: int = Field(..., description="Progress percentage (0-100)")
    current_step: str = Field(..., description="Current processing step")
    zip_path: Optional[str] = None
    error: Optional[str] = None


class ModuleListResponse(BaseModel):
    """Response model for available modules list"""

    tier: int
    modules: List[dict]


# ============================================================================
# In-Memory Export Job Tracking
# ============================================================================
# In production, use Redis or database for persistence

export_jobs = {}


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/export", response_model=ExportResponse)
async def create_export_package(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create export package for selected module

    This endpoint:
    1. Validates module selection
    2. Initiates background export job
    3. Returns export job ID for status tracking

    The export process runs asynchronously and includes:
    - Full codebase cloning
    - Module filtering (remove non-selected)
    - SQL script generation (filtered modules + permissions)
    - Data sanitization
    - ZIP packaging
    """

    logger.info(f"📦 Export request: {request.module_name} (Tier {request.module_tier})")

    # Validate module tier
    if request.module_tier not in [2, 3]:
        raise HTTPException(
            status_code=400,
            detail="Invalid module tier. Must be 2 (Domain Verticals) or 3 (Customer Solutions)"
        )

    # Validate module exists in database
    from app.models.database import Module
    module = db.query(Module).filter(
        Module.name == request.module_name,
        Module.meta_info['tier'].astext == str(request.module_tier)
    ).first()

    if not module:
        raise HTTPException(
            status_code=404,
            detail=f"Module '{request.module_name}' not found in Tier {request.module_tier}"
        )

    # Generate export ID
    import uuid
    export_id = str(uuid.uuid4())[:8]

    # Initialize job tracking
    export_jobs[export_id] = {
        "status": "started",
        "progress": 0,
        "current_step": "Initializing export...",
        "module_name": request.module_name,
        "module_tier": request.module_tier,
        "zip_path": None,
        "error": None
    }

    # Start background export job
    background_tasks.add_task(
        run_export_job,
        export_id=export_id,
        module_name=request.module_name,
        module_tier=request.module_tier,
        export_base_path=request.export_path
    )

    return ExportResponse(
        status="started",
        message=f"Export job started for '{request.module_name}' (Tier {request.module_tier})",
        export_id=export_id,
        summary={
            "module": request.module_name,
            "tier": request.module_tier,
            "estimated_time": "2-5 minutes"
        }
    )


@router.get("/status/{export_id}", response_model=ExportStatusResponse)
async def get_export_status(export_id: str):
    """
    Get status of export job

    Returns:
    - Current progress (0-100%)
    - Current processing step
    - ZIP path (when completed)
    - Error message (if failed)
    """

    if export_id not in export_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Export job '{export_id}' not found"
        )

    job = export_jobs[export_id]

    return ExportStatusResponse(
        export_id=export_id,
        status=job["status"],
        progress=job["progress"],
        current_step=job["current_step"],
        zip_path=job.get("zip_path"),
        error=job.get("error")
    )


@router.get("/modules/tier/{tier}", response_model=ModuleListResponse)
async def list_exportable_modules(tier: int, db: Session = Depends(get_db)):
    """
    List all exportable modules for a given tier

    Args:
        tier: Module tier (2 or 3)

    Returns:
        List of modules with name, description, category
    """

    if tier not in [2, 3]:
        raise HTTPException(
            status_code=400,
            detail="Invalid tier. Must be 2 (Domain Verticals) or 3 (Customer Solutions)"
        )

    from app.models.database import Module

    modules = db.query(Module).filter(
        Module.meta_info['tier'].astext == str(tier),
        Module.is_active == True
    ).order_by(Module.display_order).all()

    module_list = [
        {
            "name": m.name,
            "code": m.code,
            "description": m.description,
            "category": m.meta_info.get("category"),
            "tags": m.meta_info.get("tags", [])
        }
        for m in modules
    ]

    return ModuleListResponse(
        tier=tier,
        modules=module_list
    )


@router.get("/download/{export_id}")
async def download_export_package(export_id: str):
    """
    Download generated export package

    Returns:
        ZIP file download
    """

    if export_id not in export_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Export job '{export_id}' not found"
        )

    job = export_jobs[export_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Export job not completed. Current status: {job['status']}"
        )

    zip_path = job.get("zip_path")
    if not zip_path or not Path(zip_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Export package file not found"
        )

    from fastapi.responses import FileResponse

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=Path(zip_path).name
    )


@router.delete("/jobs/{export_id}")
async def delete_export_job(export_id: str):
    """
    Delete export job and cleanup files

    This will:
    - Remove job from tracking
    - Delete generated ZIP file
    - Delete export directory
    """

    if export_id not in export_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Export job '{export_id}' not found"
        )

    job = export_jobs[export_id]

    # Cleanup files
    zip_path = job.get("zip_path")
    if zip_path and Path(zip_path).exists():
        Path(zip_path).unlink()
        logger.info(f"Deleted export package: {zip_path}")

    # Remove job
    del export_jobs[export_id]

    return {"status": "deleted", "message": f"Export job '{export_id}' deleted"}


# ============================================================================
# Background Job Execution
# ============================================================================

async def run_export_job(
    export_id: str,
    module_name: str,
    module_tier: int,
    export_base_path: str
):
    """
    Background task to run export job

    Updates job status and progress as it runs
    """

    try:
        logger.info(f"🚀 Starting export job {export_id}")

        # Update status
        export_jobs[export_id]["progress"] = 10
        export_jobs[export_id]["current_step"] = "Copying codebase..."

        # Initialize builder
        builder = FullCloneExportBuilder(
            selected_module=module_name,
            module_tier=module_tier,
            export_base_path=export_base_path
        )

        # Update progress - codebase copying
        export_jobs[export_id]["progress"] = 20
        export_jobs[export_id]["current_step"] = "Filtering modules..."

        # Build export package
        zip_path = await builder.build_export_package()

        # Update progress - completed
        export_jobs[export_id]["status"] = "completed"
        export_jobs[export_id]["progress"] = 100
        export_jobs[export_id]["current_step"] = "Export completed"
        export_jobs[export_id]["zip_path"] = zip_path

        # Get summary
        summary = builder.get_export_summary()
        export_jobs[export_id]["summary"] = summary

        logger.info(f"✅ Export job {export_id} completed: {zip_path}")

    except Exception as e:
        logger.error(f"❌ Export job {export_id} failed: {e}", exc_info=True)

        export_jobs[export_id]["status"] = "failed"
        export_jobs[export_id]["progress"] = 0
        export_jobs[export_id]["current_step"] = "Export failed"
        export_jobs[export_id]["error"] = str(e)


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def export_wizard_health():
    """Health check for export wizard service"""

    return {
        "status": "healthy",
        "active_jobs": len([j for j in export_jobs.values() if j["status"] == "started"]),
        "completed_jobs": len([j for j in export_jobs.values() if j["status"] == "completed"]),
        "failed_jobs": len([j for j in export_jobs.values() if j["status"] == "failed"])
    }
