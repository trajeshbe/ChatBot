"""
API routes for template-based data extraction
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.services.template_extraction_service import (
    template_extraction_service,
    ExtractionField,
    ExtractionTemplate,
    get_screener_in_template
)
from app.models.database import WebScrapeJob
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/extract", tags=["Template Extraction"])


class ExtractFieldRequest(BaseModel):
    """Request model for defining extraction fields"""
    name: str
    selector: Optional[str] = None
    xpath: Optional[str] = None
    regex: Optional[str] = None
    attribute: Optional[str] = None
    data_type: str = "text"
    required: bool = False
    default_value: Optional[Any] = None


class ExtractTemplateRequest(BaseModel):
    """Request model for custom extraction template"""
    name: str
    description: str = ""
    url: str
    fields: List[ExtractFieldRequest]
    wait_for_selector: Optional[str] = None
    pagination_selector: Optional[str] = None
    max_pages: int = Field(default=1, ge=1, le=10)
    session_id: Optional[str] = None


class ExtractPresetRequest(BaseModel):
    """Request model for using a preset template"""
    url: str
    preset: str = "screener_in"
    session_id: Optional[str] = None


class ExtractionResponse(BaseModel):
    """Response model for extraction results"""
    success: bool
    url: str
    template_name: str
    data: List[Dict[str, Any]]
    row_count: int
    extracted_at: str
    session_id: Optional[str] = None
    error: Optional[str] = None


@router.post("/custom", response_model=ExtractionResponse)
async def extract_with_custom_template(
    request: ExtractTemplateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Extract data from a URL using a custom template

    This endpoint allows you to define custom extraction rules to scrape
    structured data from any website.
    """
    try:
        # Convert request fields to ExtractionField objects
        fields = [
            ExtractionField(
                name=f.name,
                selector=f.selector,
                xpath=f.xpath,
                regex=f.regex,
                attribute=f.attribute,
                data_type=f.data_type,
                required=f.required,
                default_value=f.default_value
            )
            for f in request.fields
        ]

        # Create template
        template = ExtractionTemplate(
            name=request.name,
            description=request.description,
            fields=fields,
            wait_for_selector=request.wait_for_selector,
            pagination_selector=request.pagination_selector,
            max_pages=request.max_pages
        )

        # Extract data
        result = await template_extraction_service.extract_data(
            url=request.url,
            template=template,
            session_id=request.session_id
        )

        # Store scrape job in database
        if result['success']:
            job = WebScrapeJob(
                url=request.url,
                scrape_prompt=f"Template extraction: {template.name}",
                status="completed",
                completed_at=datetime.utcnow()
            )
            db.add(job)
            await db.commit()

        return ExtractionResponse(**result)

    except Exception as e:
        logger.error(f"Error in custom template extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preset/{preset_name}", response_model=ExtractionResponse)
async def extract_with_preset_template(
    preset_name: str,
    request: ExtractPresetRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Extract data from a URL using a preset template

    Available presets:
    - screener_in: Extract company financial data from Screener.in
    """
    try:
        # Get preset template
        if preset_name == "screener_in":
            template = get_screener_in_template()
        else:
            raise HTTPException(status_code=404, detail=f"Preset template '{preset_name}' not found")

        # Extract data
        result = await template_extraction_service.extract_data(
            url=request.url,
            template=template,
            session_id=request.session_id
        )

        # Store scrape job in database
        if result['success']:
            job = WebScrapeJob(
                url=request.url,
                scrape_prompt=f"Template extraction: {template.name}",
                status="completed",
                completed_at=datetime.utcnow()
            )
            db.add(job)
            await db.commit()

        return ExtractionResponse(**result)

    except Exception as e:
        logger.error(f"Error in preset template extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/to-excel")
async def export_extraction_to_excel(
    data: List[Dict[str, Any]],
    filename: str = "extracted_data.xlsx"
):
    """
    Export extracted data to Excel format

    Accepts a list of dictionaries and returns an Excel file.
    """
    try:
        # Generate Excel file
        excel_data = await template_extraction_service.export_to_excel(data, filename)

        # Return as streaming response
        return StreamingResponse(
            excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presets")
async def list_preset_templates():
    """
    List all available preset templates
    """
    presets = [
        {
            "name": "screener_in",
            "display_name": "Screener.in Company Data",
            "description": "Extract financial metrics from Screener.in company pages",
            "fields": [
                "Company Name", "Market Cap", "Current Price", "Stock P/E",
                "Book Value", "Dividend Yield", "ROCE", "ROE", "Face Value",
                "Market Position", "Source / Notes"
            ]
        }
    ]

    return {"presets": presets}


@router.get("/test")
async def test_template_extraction():
    """
    Test endpoint to verify template extraction service is working
    """
    return {
        "status": "ok",
        "service": "template_extraction",
        "message": "Template extraction service is ready"
    }
