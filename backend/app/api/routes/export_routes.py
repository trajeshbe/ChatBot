"""
Export API Routes - Generate and download files from templates
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID
import logging
import io
from datetime import datetime

from app.tier_1.infrastructure.database import get_db
from app.models.prompt_library import OutputTemplate
from app.models.database_enhanced import User
from app.schemas.prompt_schemas import ExportRequest, ExportResponse
from app.api.routes.auth import get_current_user, get_current_user_optional
from app.tier_1.export.export_service import export_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["export"])


@router.post("/export", response_class=StreamingResponse)
async def export_content(
    request: ExportRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Export content using a template or inline configuration.

    Args:
        request: Export request with template_id OR (template_type + template_config), content, variables, filename

    Returns:
        File stream for download
    """
    try:
        template = None
        template_config = None
        template_type = None

        # Support both template_id and inline template config
        if hasattr(request, 'template_id') and request.template_id:
            # Get template from database
            query = select(OutputTemplate).where(OutputTemplate.id == request.template_id)
            result = await db.execute(query)
            template = result.scalar_one_or_none()

            if not template:
                raise HTTPException(status_code=404, detail="Template not found")

            # Check access - must be public or owned by user
            if not template.is_public and (not current_user or template.created_by != current_user.id):
                raise HTTPException(status_code=403, detail="Access denied to this template")

            template_config = template.template_config
            template_type = template.template_type

            # Update template usage stats
            template.usage_count += 1
            template.last_used_at = datetime.now()
            await db.commit()

        elif hasattr(request, 'template_type') and request.template_type:
            # Use inline template config (for quick export without saving template)
            template_type = request.template_type
            template_config = request.template_config if hasattr(request, 'template_config') else {}

        else:
            raise HTTPException(status_code=400, detail="Either template_id or template_type must be provided")

        # Generate file
        file_bytes, mime_type = await export_service.export_data(
            template_config=template_config,
            template_type=template_type,
            content=request.content,
            variables=request.variables if hasattr(request, 'variables') else None
        )

        # Determine filename
        if hasattr(request, 'filename') and request.filename:
            filename = request.filename
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            extension = {
                'excel': 'xlsx',
                'word': 'docx',
                'markdown': 'md',
                'json': 'json',
                'pdf': 'pdf'
            }.get(template_type, 'txt')
            filename = f"export_{timestamp}.{extension}"

        # Add extension if not present
        extension = {
            'excel': 'xlsx',
            'word': 'docx',
            'markdown': 'md',
            'json': 'json',
            'pdf': 'pdf'
        }.get(template_type, 'txt')

        if not filename.endswith(f".{extension}"):
            filename = f"{filename}.{extension}"

        logger.info(f"Exporting content ({template_type}) for user {current_user.username if current_user else 'anonymous'}")

        # Return file stream
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=mime_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(len(file_bytes))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/preview")
async def preview_export(
    request: ExportRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Preview export result without downloading.
    Returns metadata and sample content.
    """
    try:
        # Get template
        query = select(OutputTemplate).where(OutputTemplate.id == request.template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Check access
        if not template.is_public and (not current_user or template.created_by != current_user.id):
            raise HTTPException(status_code=403, detail="Access denied to this template")

        # Generate file
        file_bytes, mime_type = await export_service.export_data(
            template_config=template.template_config,
            template_type=template.template_type,
            content=request.content,
            variables=request.variables
        )

        # For text-based formats, return preview
        preview_content = None
        if template.template_type in ['markdown', 'json']:
            preview_content = file_bytes.decode('utf-8')[:1000]  # First 1000 chars

        return {
            'success': True,
            'template_name': template.name,
            'template_type': template.template_type,
            'file_size': len(file_bytes),
            'mime_type': mime_type,
            'preview': preview_content
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing export: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/formats")
async def get_supported_formats():
    """Get list of supported export formats"""
    return {
        'formats': [
            {
                'type': 'excel',
                'name': 'Microsoft Excel',
                'extension': 'xlsx',
                'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'description': 'Spreadsheet format for tabular data'
            },
            {
                'type': 'word',
                'name': 'Microsoft Word',
                'extension': 'docx',
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'description': 'Document format for reports and text'
            },
            {
                'type': 'markdown',
                'name': 'Markdown',
                'extension': 'md',
                'mime_type': 'text/markdown',
                'description': 'Plain text format with markdown syntax'
            },
            {
                'type': 'json',
                'name': 'JSON',
                'extension': 'json',
                'mime_type': 'application/json',
                'description': 'Structured data format'
            },
            {
                'type': 'pdf',
                'name': 'PDF',
                'extension': 'pdf',
                'mime_type': 'application/pdf',
                'description': 'Portable Document Format (coming soon)',
                'available': False
            }
        ]
    }
