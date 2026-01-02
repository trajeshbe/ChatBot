"""
Grant Thornton API Routes

FastAPI endpoints for Grant Thornton financial analysis:
- POST /api/v1/grant-thornton/extract - Extract financial data from PDF
- GET /api/v1/grant-thornton/download/{md5_hash} - Download Excel report

Author: Claude Code
Date: 2026-01-01
"""

import logging
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
import tempfile
import os
import io

from minio import Minio
from minio.error import S3Error
from app.tier_1.infrastructure.config import settings
from app.services.grant_thornton import get_pipeline
from app.schemas.grant_thornton_schemas import GrantThorntonExtractionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/grant-thornton", tags=["Grant Thornton"])

# MinIO client (initialized lazily)
_minio_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    """Get or create MinIO client"""
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        # Create bucket if it doesn't exist
        if not _minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
            _minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
            logger.info(f"Created MinIO bucket: {settings.MINIO_BUCKET_NAME}")

    return _minio_client


def build_grant_thornton_path(
    company_name: str,
    filename: str,
    organization: str = "merit",
    department: str = "financial-services",
    team: str = "grant-thornton"
) -> str:
    """
    Build organizational MinIO path for Grant Thornton PDFs.

    Pattern: /{organization}/{department}/{team}/{company_name}/{filename}

    Args:
        company_name: Company name (treated as project identifier)
        filename: Original PDF filename
        organization: Organization name (default: merit)
        department: Department name (default: financial-services)
        team: Team name (default: grant-thornton)

    Returns:
        MinIO object path
    """
    # Sanitize company name for path
    safe_company = company_name.lower().replace(" ", "-").replace("/", "-")

    return f"{organization}/{department}/{team}/{safe_company}/{filename}"


@router.post("/extract", response_model=GrantThorntonExtractionResponse)
async def extract_financial_data(
    pdf_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    company_name: Optional[str] = Form(None)
):
    """
    Extract financial datapoints from annual report PDF.

    Process:
    1. Save uploaded PDF to MinIO with organizational hierarchy
    2. Run extraction pipeline
    3. Return complete extraction results with Excel path

    Args:
        pdf_file: Annual report PDF file
        session_id: Optional session ID for tracking
        company_name: Company name (used as project identifier in MinIO path)

    Returns:
        GrantThorntonExtractionResponse with all extracted data
    """
    if not pdf_file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    logger.info(f"📄 Grant Thornton extraction request: {pdf_file.filename}")

    # Use company name from form or extract from filename
    company = company_name or pdf_file.filename.replace(".pdf", "").replace("_", " ")

    # Save uploaded file to temp directory for processing
    temp_dir = tempfile.mkdtemp(prefix="grant_thornton_")
    pdf_path = os.path.join(temp_dir, pdf_file.filename)

    try:
        # Read uploaded file content
        content = await pdf_file.read()

        # Save to MinIO with organizational hierarchy
        minio_client = get_minio_client()
        minio_path = build_grant_thornton_path(
            company_name=company,
            filename=pdf_file.filename
        )

        logger.info(f"📁 Saving PDF to MinIO: {minio_path}")
        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            minio_path,
            io.BytesIO(content),
            length=len(content),
            content_type="application/pdf"
        )
        logger.info(f"✅ PDF saved to MinIO bucket: {settings.MINIO_BUCKET_NAME}")

        # Also save to temp file for pipeline processing
        with open(pdf_path, "wb") as f:
            f.write(content)

        logger.info(f"✅ Saved PDF to temp: {pdf_path}")

        # Get extraction pipeline
        pipeline = await get_pipeline()

        # Run extraction
        logger.info(f"🚀 Starting Grant Thornton extraction pipeline...")
        result = await pipeline.extract(
            pdf_path=pdf_path,
            datapoints_excel_path=None,  # Use defaults from config
            stream_progress=False
        )

        # Store MinIO path in result for future reference
        # Note: The result object is returned directly, but we log the MinIO path
        logger.info(f"📊 PDF stored at MinIO path: {minio_path}")

        logger.info(f"✅ Extraction complete: {result.status}")
        logger.info(
            f"   - Datapoints: {result.datapoints_extracted}/{result.total_datapoints}"
        )
        logger.info(f"   - Company: {company}")
        logger.info(f"   - MinIO Path: {minio_path}")
        logger.info(f"   - Elapsed: {result.processing_time_seconds:.1f}s")

        return result

    except S3Error as e:
        logger.error(f"❌ MinIO upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"MinIO upload failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Grant Thornton extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )

    finally:
        # Cleanup temp directory (but keep Excel file)
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            # Don't remove temp_dir as it may contain the Excel file
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")


@router.get("/download/{md5_hash}")
async def download_excel(md5_hash: str):
    """
    Download Excel report for a completed extraction.

    Args:
        md5_hash: MD5 hash of the processed PDF

    Returns:
        Excel file as download
    """
    # Look for Excel file in /tmp directory
    excel_filename = f"grant_thornton_{md5_hash[:8]}.xlsx"
    excel_path = Path("/tmp") / excel_filename

    if not excel_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Excel file not found for MD5: {md5_hash[:8]}..."
        )

    logger.info(f"📊 Downloading Excel: {excel_path}")

    return FileResponse(
        path=str(excel_path),
        filename=excel_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/status")
async def get_status():
    """
    Get Grant Thornton module status.

    Returns:
        Module status and capabilities
    """
    return {
        "success": True,
        "status": "operational",
        "description": "Grant Thornton Financial Analysis - Extract 50+ financial datapoints from annual reports",
        "capabilities": [
            "PDF parsing with Docling integration",
            "BAAI/bge-large-en-v1.5 embeddings (1024-dim)",
            "Two-stage RAG retrieval",
            "LangGraph agent extraction",
            "Sub-calculations (12+ formulas)",
            "Financial ratios (30+ metrics)",
            "Professional Excel export"
        ],
        "model": "BAAI/bge-large-en-v1.5",
        "version": "1.0.0"
    }
