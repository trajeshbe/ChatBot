"""
Construction Metrics Extraction API Routes

REST API endpoints for extracting building metrics from construction
project ZIP files.

Endpoints:
- POST /api/v1/construction-metrics/extract - Extract metrics from ZIP file

Author: Construction Metrics Agent
Date: 2025-12-03
"""

import logging
import os
import tempfile
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.agents.construction_metrics import ConstructionMetricsAgent
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/construction-metrics",
    tags=["Construction Metrics"]
)


@router.post("/extract")
async def extract_construction_metrics(
    zip_file: UploadFile = File(..., description="ZIP file containing construction documents"),
    project_name: Optional[str] = Form(None, description="Project name (optional)"),
    session_id: Optional[str] = Form(None, description="Session ID for tracking"),
    model_id: Optional[str] = Form("llama3.2-vision:11b", description="Vision LLM model to use"),
    db: Session = Depends(get_db)
):
    """
    Extract building metrics from construction project ZIP file.

    This endpoint processes a ZIP file containing construction documents
    (architectural drawings, DA approvals, site photos, etc.) and extracts:
    - Levels (Above/Below Ground)
    - Gross Floor Area (GFA)
    - External Area
    - Site Area
    - Building Height

    **Process:**
    1. Upload ZIP file
    2. Extract and classify documents
    3. Analyze using Vision LLM
    4. Aggregate results with confidence weighting
    5. Return structured JSON

    **Returns:**
    ```json
    {
        "project_name": "Sippy Creek Depot",
        "metrics": {
            "levels_above_ground": 4,
            "levels_below_ground": 1,
            "gross_floor_area_m2": 2850.5,
            "external_area_m2": 450.0,
            "site_area_m2": 1200.0,
            "building_height_m": 15.6
        },
        "confidence": 0.95,
        "sources": [
            "A0000 - DRAWING SCHEDULE.pdf",
            "DA Approval.pdf"
        ],
        "details": {
            "metrics_found": 6,
            "total_metrics": 6,
            "documents_processed": 15,
            "aggregation_method": "confidence_weighted_averaging"
        },
        "processing_time_seconds": 45.2
    }
    ```

    **Note:** Metrics that cannot be extracted will return "NA".
    """
    logger.info(f"Received construction metrics extraction request: {zip_file.filename}")

    # Validate file type
    if not zip_file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only ZIP files are supported."
        )

    # Save uploaded ZIP file to temp directory
    try:
        # Create temp file for ZIP
        temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix='.zip', prefix='construction_')
        os.close(temp_zip_fd)

        # Write uploaded file
        with open(temp_zip_path, 'wb') as f:
            content = await zip_file.read()
            f.write(content)

        logger.info(f"Saved ZIP file to: {temp_zip_path}")

        # Extract project name from filename if not provided
        if not project_name:
            project_name = Path(zip_file.filename).stem

        # Initialize agent
        from app.services.hybrid_extraction_service import HybridExtractionService

        llm_service = LLMService()
        vision_service = HybridExtractionService()

        agent = ConstructionMetricsAgent(
            llm_service=llm_service,
            vision_service=vision_service,
            db=db
        )

        # Run extraction
        logger.info(f"Starting extraction for project: {project_name}")
        result = await agent.extract_metrics(
            zip_file_path=temp_zip_path,
            project_name=project_name,
            session_id=session_id or 'default',
            model_id=model_id
        )

        logger.info(f"Extraction complete: {result['metrics']}")

        return result

    except Exception as e:
        logger.error(f"Construction metrics extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )

    finally:
        # Cleanup temp ZIP file
        try:
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
                logger.debug(f"Cleaned up temp file: {temp_zip_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file: {e}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for construction metrics service.

    Returns:
        Service status and available models
    """
    return {
        "status": "healthy",
        "service": "construction_metrics_extraction",
        "version": "1.0.0",
        "supported_models": [
            "llama3.2-vision:11b",
            "llama3.2-vision:90b"
        ],
        "supported_metrics": [
            "levels_above_ground",
            "levels_below_ground",
            "gross_floor_area_m2",
            "external_area_m2",
            "site_area_m2",
            "building_height_m"
        ]
    }


@router.get("/metrics-schema")
async def get_metrics_schema():
    """
    Get the JSON schema for construction metrics output.

    Returns:
        JSON schema definition
    """
    return {
        "schema_version": "1.0",
        "output_schema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "metrics": {
                    "type": "object",
                    "properties": {
                        "levels_above_ground": {
                            "type": ["integer", "string"],
                            "description": "Number of floors above ground (or 'NA')"
                        },
                        "levels_below_ground": {
                            "type": ["integer", "string"],
                            "description": "Number of basement levels (or 'NA')"
                        },
                        "gross_floor_area_m2": {
                            "type": ["number", "string"],
                            "description": "Total floor area in square meters (or 'NA')"
                        },
                        "external_area_m2": {
                            "type": ["number", "string"],
                            "description": "External balcony/terrace area in m² (or 'NA')"
                        },
                        "site_area_m2": {
                            "type": ["number", "string"],
                            "description": "Total site area in m² (or 'NA')"
                        },
                        "building_height_m": {
                            "type": ["number", "string"],
                            "description": "Building height in meters (or 'NA')"
                        }
                    }
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Overall confidence score"
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Source documents used for extraction"
                },
                "details": {
                    "type": "object",
                    "description": "Extraction details and metadata"
                },
                "processing_time_seconds": {
                    "type": "number",
                    "description": "Total processing time"
                }
            },
            "required": ["project_name", "metrics", "confidence"]
        }
    }
