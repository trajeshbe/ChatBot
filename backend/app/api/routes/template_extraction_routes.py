"""
API routes for template-based data extraction
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
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
    use_smart_mapping: bool = Field(
        default=False,
        description="Use LLM-based smart mapping instead of selectors (recommended if null values occur)"
    )


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
    db: AsyncSession = Depends(get_db)
):
    """
    Extract data from a URL using a custom template

    This endpoint allows you to define custom extraction rules to scrape
    structured data from any website.

    **New Feature:** Set `use_smart_mapping=true` to use LLM-based intelligent
    mapping instead of selectors. This is recommended if you're experiencing
    null values or want more flexible extraction that adapts to page changes.

    **Selector-based extraction (default):**
    - Fast and precise
    - Requires writing CSS/XPath selectors
    - Breaks when page structure changes

    **Smart mapping (use_smart_mapping=true):**
    - Uses AI to map data to template columns
    - No selectors needed
    - Adapts to page structure changes
    - Never hallucinates missing values
    - Clearly marks fields requiring additional research
    """
    try:
        # Check if smart mapping is requested
        if request.use_smart_mapping:
            logger.info(f"Using smart mapping for template: {request.name}")

            # Import required services
            from app.services.scraper_service import scraper_service
            from app.services.llm_service import llm_service
            from app.services.webscraper.extractors.llm_extractor import LLMExtractor

            # Step 1: Scrape the webpage
            scrape_result = await scraper_service.scrape_url(
                url=request.url,
                strategy='auto',
                scrape_prompt=None
            )

            if not scrape_result or not scrape_result.get('success'):
                error_msg = scrape_result.get('error', 'Failed to scrape URL') if scrape_result else 'Scraper returned None'
                raise HTTPException(status_code=500, detail=f"Failed to scrape URL: {error_msg}")

            scraped_data = scrape_result.get('html') or scrape_result.get('text', '')
            if not scraped_data:
                raise HTTPException(status_code=500, detail="Scraped content is empty")

            # Step 2: Extract template columns from fields
            template_columns = [f.name for f in request.fields]

            # Step 3: Map using LLM
            await llm_service.initialize()
            extractor = LLMExtractor(llm_service=llm_service)

            mapping_result = await extractor.map_to_custom_template(
                scraped_data=scraped_data,
                template_columns=template_columns,
                template_examples=None,  # Could be enhanced to extract from default_value
                llm_provider="openai"
            )

            if not mapping_result:
                raise HTTPException(
                    status_code=500,
                    detail="Smart mapping failed. Check LLM service configuration."
                )

            mapped_data = mapping_result['mapped_data']
            missing_fields = mapping_result['missing_fields']

            logger.info(
                f"Smart mapping complete: {len(mapped_data) - len(missing_fields)}/{len(mapped_data)} fields extracted"
            )

            # Store scrape job
            job = WebScrapeJob(
                url=request.url,
                scrape_prompt=f"Smart template mapping: {request.name}",
                status="completed",
                completed_at=datetime.utcnow()
            )
            db.add(job)
            await db.commit()

            # Return result
            return ExtractionResponse(
                success=True,
                url=request.url,
                template_name=request.name,
                data=[mapped_data],
                row_count=1,
                extracted_at=datetime.utcnow().isoformat(),
                session_id=request.session_id,
                error=None
            )

        else:
            # Original selector-based extraction
            logger.info(f"Using selector-based extraction for template: {request.name}")

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in custom template extraction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preset/{preset_name}", response_model=ExtractionResponse)
async def extract_with_preset_template(
    preset_name: str,
    request: ExtractPresetRequest,
    db: AsyncSession = Depends(get_db)
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


# ============================================================================
# Auto-Generation Endpoints (NEW)
# ============================================================================

class AutoGenerateTemplateRequest(BaseModel):
    """Request model for auto-generating templates"""
    url: str
    user_instructions: Optional[str] = Field(
        None,
        description="Natural language instructions for what data to extract. "
                   "E.g., 'Extract product names, prices, and ratings' or "
                   "'Get company financial metrics like revenue and profit'"
    )
    template_name: Optional[str] = None
    llm_provider: str = Field(default="openai", description="LLM provider: ollama, openai, or anthropic")
    max_fields: int = Field(default=15, ge=1, le=30, description="Maximum number of fields to generate")
    session_id: Optional[str] = None


class AutoGenerateResponse(BaseModel):
    """Response model for auto-generated template"""
    success: bool
    template: Optional[Dict[str, Any]] = None
    fields: Optional[List[Dict[str, Any]]] = None
    template_type: Optional[str] = None
    confidence: Optional[float] = None
    message: Optional[str] = None
    error: Optional[str] = None


class SmartExtractRequest(BaseModel):
    """Request model for smart extraction without predefined template"""
    url: str
    user_instructions: str = Field(
        ...,
        description="Describe what data you want to extract in natural language"
    )
    llm_provider: str = Field(default="openai")
    output_format: str = Field(default="excel", description="Output format: excel, csv, or json")
    session_id: Optional[str] = None


@router.post("/auto-generate", response_model=AutoGenerateResponse)
async def auto_generate_template(
    request: AutoGenerateTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    **AUTO-GENERATE EXTRACTION TEMPLATE (Feature #2)**

    Automatically generate an extraction template by analyzing a webpage with LLM.

    When you don't have a predefined Excel template, this endpoint uses AI to:
    1. Analyze the webpage structure and content
    2. Identify the best fields/columns to extract
    3. Determine optimal extraction strategies for each field
    4. Create a ready-to-use template

    **User Instructions (Feature #3):**
    Provide natural language guidance for what you want to extract:
    - "Extract product information including name, price, and reviews"
    - "Get company financial data like revenue, profit margin, and growth rate"
    - "Pull article metadata: title, author, date, and category"

    The LLM will analyze the page and create appropriate field mappings based on your instructions.

    **Example Usage:**
    ```json
    {
        "url": "https://example.com/products/laptop",
        "user_instructions": "Extract laptop specs: model name, processor, RAM, price, and customer rating",
        "llm_provider": "ollama",
        "max_fields": 10
    }
    ```

    **Response:**
    Returns the generated template with field definitions, extraction strategies,
    and validation rules. You can then use this template for extraction or refine it further.
    """
    try:
        # Import auto-generator service
        from app.services.webscraper.templates.template_auto_generator import TemplateAutoGenerator
        from app.services.llm_service import llm_service
        from app.services.scraper_service import scraper_service

        # Initialize auto-generator
        auto_gen = TemplateAutoGenerator(
            llm_service=llm_service,
            scraper_service=scraper_service
        )

        # Generate template
        logger.info(f"Auto-generating template for URL: {request.url}")
        if request.user_instructions:
            logger.info(f"User instructions: {request.user_instructions}")

        template = await auto_gen.analyze_webpage_and_generate_template(
            url=request.url,
            user_instructions=request.user_instructions,
            template_name=request.template_name,
            llm_provider=request.llm_provider,
            max_fields=request.max_fields
        )

        if not template:
            return AutoGenerateResponse(
                success=False,
                error="Failed to auto-generate template. This may be due to: "
                      "1) Website blocking automated access, "
                      "2) Invalid or unreachable URL, "
                      "3) Empty webpage content. "
                      "Please check the URL and try again."
            )

        # Format response
        fields_data = [
            {
                "name": f.name,
                "display_name": f.display_name,
                "description": f.description,
                "type": f.type,
                "required": f.required,
                "extraction_strategy": f.source_hint.type if f.source_hint else "unknown",
                "extraction_hint": (
                    f.source_hint.selector or
                    f.source_hint.xpath or
                    f.source_hint.pattern or
                    f.source_hint.prompt or
                    "N/A"
                ) if f.source_hint else "N/A"
            }
            for f in template.fields
        ]

        template_data = {
            "name": template.name,
            "description": template.description,
            "template_type": template.schema_definition.type,
            "fields_count": len(template.fields),
            "metadata": template.schema_definition.metadata
        }

        # Check if this was generated using fallback
        is_fallback = template.schema_definition.metadata.get('fallback', False)
        success_message = f"Successfully generated template with {len(template.fields)} fields"

        if is_fallback:
            success_message += " (using rule-based analysis). For AI-powered analysis, configure OpenAI API key."

        return AutoGenerateResponse(
            success=True,
            template=template_data,
            fields=fields_data,
            template_type=template.schema_definition.type,
            confidence=template.schema_definition.metadata.get('confidence', 0.8),
            message=success_message
        )

    except Exception as e:
        logger.error(f"Error in auto-generate template: {e}", exc_info=True)
        return AutoGenerateResponse(
            success=False,
            error=f"Auto-generation failed: {str(e)}"
        )


@router.post("/smart-extract", response_model=ExtractionResponse)
async def smart_extract_without_template(
    request: SmartExtractRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    **SMART EXTRACTION WITHOUT PREDEFINED TEMPLATE (ENHANCED)**

    Extract data from a webpage using only natural language instructions - no template needed!

    This endpoint now uses **LLM-based mapping** for more reliable extraction:
    1. Auto-generates column names based on your instructions (or auto-detects if not specified)
    2. Scrapes the webpage content
    3. Uses AI to intelligently map scraped data to columns
    4. Returns the extracted data in your chosen format (Excel/CSV/JSON)

    **Two Modes of Operation:**

    **Mode 1: User Specifies Column Names**
    - Example: "Extract financial data and map to columns like Revenue (Annual), EBITDA, EBITDA Margin, Net Profit"
    - The system will extract those exact column names and map data to them

    **Mode 2: Auto-Generate Column Names**
    - Example: "Extract product information from this page"
    - The system will analyze the page and create appropriate column names automatically

    **How it works:**
    1. You provide a URL and describe what you want to extract
    2. If you specify column names, they're used; otherwise, AI auto-generates them
    3. Webpage is scraped
    4. AI maps scraped data to the columns (never hallucinates missing values)
    5. Results are returned in your preferred format

    **Example Usage - With Column Names:**
    ```json
    {
        "url": "https://www.screener.in/company/RELIANCE/",
        "user_instructions": "Extract financial data and map to columns like Market Cap, Stock P/E, ROE, ROCE",
        "llm_provider": "openai",
        "output_format": "excel"
    }
    ```

    **Example Usage - Auto Column Names:**
    ```json
    {
        "url": "https://example.com/products",
        "user_instructions": "Extract all product information from this page",
        "llm_provider": "openai",
        "output_format": "excel"
    }
    ```

    **Benefits:**
    - No need to create templates or write selectors
    - Natural language interface - just describe what you need
    - Intelligent field mapping using LLM (no selector failures)
    - Respects user-specified column names when provided
    - Auto-generates appropriate column names when not specified
    - Never hallucinates - marks missing fields clearly

    **Perfect for:**
    - One-time data extraction tasks
    - Exploring new websites
    - Quick data gathering without setup
    - Dynamic content that changes frequently
    """
    try:
        # Import required services
        from app.services.webscraper.templates.template_auto_generator import TemplateAutoGenerator
        from app.services.llm_service import llm_service
        from app.services.scraper_service import scraper_service
        from app.services.webscraper.extractors.llm_extractor import LLMExtractor

        logger.info(f"Smart extraction from: {request.url}")
        logger.info(f"Instructions: {request.user_instructions}")

        # Step 1: Auto-generate template to determine column names
        auto_gen = TemplateAutoGenerator(
            llm_service=llm_service,
            scraper_service=scraper_service
        )

        template = await auto_gen.generate_template_from_user_instructions(
            url=request.url,
            user_instructions=request.user_instructions,
            llm_provider=request.llm_provider,
            include_smart_mapping=True
        )

        if not template:
            error_msg = (
                "Failed to auto-generate template from instructions. "
                "This may be due to: "
                "1) LLM service not properly configured (check OpenAI API key in .env), "
                "2) Website blocking automated access, "
                "3) Ollama/vLLM services not running. "
                "Please check backend logs for details."
            )
            logger.error(error_msg)
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )

        # Extract column names from generated template
        template_columns = [f.display_name or f.name for f in template.fields]
        logger.info(f"Generated {len(template_columns)} columns: {template_columns}")

        # Step 2: Scrape the webpage
        logger.info("Scraping webpage content...")
        scrape_result = await scraper_service.scrape_url(
            url=request.url,
            strategy='auto',
            scrape_prompt=None
        )

        if not scrape_result or not scrape_result.get('success'):
            error_msg = scrape_result.get('error', 'Failed to scrape URL') if scrape_result else 'Scraper returned None'
            logger.error(f"Scraping failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to scrape URL: {error_msg}"
            )

        # Get scraped content
        scraped_data = scrape_result.get('html') or scrape_result.get('text', '')

        if not scraped_data:
            raise HTTPException(
                status_code=500,
                detail="Scraped content is empty"
            )

        logger.info(f"Successfully scraped {len(scraped_data)} characters")

        # Step 3: Use LLM to intelligently map scraped data to columns
        logger.info(f"Mapping scraped data to {len(template_columns)} columns using LLM...")

        await llm_service.initialize()
        extractor = LLMExtractor(llm_service=llm_service)

        mapping_result = await extractor.map_to_custom_template(
            scraped_data=scraped_data,
            template_columns=template_columns,
            template_examples=None,
            llm_provider=request.llm_provider
        )

        if not mapping_result:
            raise HTTPException(
                status_code=500,
                detail="LLM-based mapping failed. Check LLM service configuration and logs."
            )

        mapped_data = mapping_result['mapped_data']
        missing_fields = mapping_result['missing_fields']

        logger.info(
            f"Mapping complete: {len(mapped_data) - len(missing_fields)}/{len(mapped_data)} fields extracted. "
            f"Missing: {missing_fields}"
        )

        # Step 4: Store scrape job
        job = WebScrapeJob(
            url=request.url,
            scrape_prompt=f"Smart extraction: {request.user_instructions}",
            status="completed",
            completed_at=datetime.utcnow()
        )
        db.add(job)
        await db.commit()

        # Step 5: Return response
        return ExtractionResponse(
            success=True,
            url=request.url,
            template_name="Smart Extraction (Auto-generated + LLM Mapping)",
            data=[mapped_data],
            row_count=1,
            extracted_at=datetime.utcnow().isoformat(),
            session_id=request.session_id,
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in smart extract: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class SmartTemplateMapRequest(BaseModel):
    """Request model for smart template mapping"""
    url: str
    template_columns: List[str] = Field(
        ...,
        description="List of column headers from your custom Excel template"
    )
    template_examples: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional example values for each column to guide extraction"
    )
    llm_provider: str = Field(default="openai", description="LLM provider: openai, anthropic, or ollama")
    output_format: str = Field(default="excel", description="Output format: excel, csv, or json")
    session_id: Optional[str] = None


@router.post("/smart-map-to-template", response_model=ExtractionResponse)
async def smart_map_to_custom_template(
    request: SmartTemplateMapRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    **SMART TEMPLATE MAPPING (NEW!)**

    Map scraped web data to your custom template columns using AI - no selectors needed!

    This is the NEW approach that solves the null value problem. It uses an improved
    LLM prompt that:
    - Never hallucinates values
    - Only extracts data that exists in the scraped content
    - Clearly marks missing fields as "— (requires additional research)"
    - Provides transparency about data completeness

    **How it works:**
    1. You provide a URL and your template columns
    2. We scrape the webpage
    3. AI intelligently maps scraped data to your template columns
    4. Missing fields are clearly marked
    5. Results exported in your preferred format

    **Example Usage:**
    ```json
    {
        "url": "https://www.screener.in/company/RELIANCE/",
        "template_columns": [
            "Company Name",
            "Market Cap",
            "Current Price",
            "Stock P/E",
            "Revenue Growth"
        ],
        "template_examples": {
            "Market Cap": "1234 Cr",
            "Stock P/E": "25.3"
        },
        "llm_provider": "openai",
        "output_format": "excel"
    }
    ```

    **Response:**
    Returns extracted data with clear indication of:
    - Successfully mapped fields
    - Fields marked as "— (requires additional research)"
    - List of missing fields

    **Benefits:**
    - No more null values in your data
    - Clear visibility of data completeness
    - No need to write CSS selectors or XPath
    - Works with any custom template structure
    - Handles variations in webpage structure
    """
    try:
        # Import required services
        from app.services.scraper_service import scraper_service
        from app.services.llm_service import llm_service
        from app.services.webscraper.extractors.llm_extractor import LLMExtractor

        logger.info(f"Smart template mapping from: {request.url}")
        logger.info(f"Template columns: {request.template_columns}")

        # Step 1: Scrape the webpage
        logger.info("Scraping webpage...")
        scrape_result = await scraper_service.scrape_url(
            url=request.url,
            strategy='auto',
            scrape_prompt=None
        )

        if not scrape_result or not scrape_result.get('success'):
            error_msg = scrape_result.get('error', 'Failed to scrape URL') if scrape_result else 'Scraper returned None'
            logger.error(f"Scraping failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to scrape URL: {error_msg}"
            )

        # Get scraped content (prefer HTML, fallback to text)
        scraped_data = scrape_result.get('html') or scrape_result.get('text', '')

        if not scraped_data:
            raise HTTPException(
                status_code=500,
                detail="Scraped content is empty"
            )

        logger.info(f"Successfully scraped {len(scraped_data)} characters")

        # Step 2: Initialize LLM extractor and map to template
        logger.info(f"Mapping to {len(request.template_columns)} template columns using {request.llm_provider}...")

        await llm_service.initialize()
        extractor = LLMExtractor(llm_service=llm_service)

        mapping_result = await extractor.map_to_custom_template(
            scraped_data=scraped_data,
            template_columns=request.template_columns,
            template_examples=request.template_examples,
            llm_provider=request.llm_provider
        )

        if not mapping_result:
            raise HTTPException(
                status_code=500,
                detail="Template mapping failed. Check LLM service configuration and logs."
            )

        mapped_data = mapping_result['mapped_data']
        missing_fields = mapping_result['missing_fields']
        extraction_complete = mapping_result['extraction_complete']

        logger.info(
            f"Mapping complete: {len(mapped_data) - len(missing_fields)}/{len(mapped_data)} fields extracted. "
            f"Missing: {missing_fields}"
        )

        # Step 3: Create response with single row of data
        data_row = mapped_data

        # Store scrape job
        job = WebScrapeJob(
            url=request.url,
            scrape_prompt=f"Smart template mapping: {', '.join(request.template_columns)}",
            status="completed",
            completed_at=datetime.utcnow()
        )
        db.add(job)
        await db.commit()

        # Return response
        return ExtractionResponse(
            success=True,
            url=request.url,
            template_name="Smart Template Mapping",
            data=[data_row],  # Single row
            row_count=1,
            extracted_at=datetime.utcnow().isoformat(),
            session_id=request.session_id,
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in smart template mapping: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class RefineTemplateRequest(BaseModel):
    """Request model for refining templates"""
    template_id: Optional[str] = None
    template_json: Optional[Dict[str, Any]] = None
    user_feedback: str = Field(
        ...,
        description="Feedback for refining the template. "
                   "E.g., 'Add a field for product ratings' or "
                   "'Change the price extraction to use the sale price instead'"
    )
    sample_url: str
    llm_provider: str = Field(default="openai")


@router.post("/refine-template")
async def refine_template_with_feedback(
    request: RefineTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    **REFINE TEMPLATE WITH USER FEEDBACK**

    Improve an existing template based on natural language feedback.

    This allows iterative refinement of templates:
    - Add new fields
    - Remove unwanted fields
    - Modify extraction strategies
    - Adjust data types

    **Example Usage:**
    ```json
    {
        "template_json": { ... existing template ... },
        "user_feedback": "The price field should extract the discounted price, not the original price. Also add a field for product availability.",
        "sample_url": "https://example.com/product/123",
        "llm_provider": "ollama"
    }
    ```
    """
    try:
        # Implementation would refine the template based on feedback
        # This is a placeholder for the refinement logic
        return {
            "success": True,
            "message": "Template refinement is in development"
        }

    except Exception as e:
        logger.error(f"Error refining template: {e}")
        raise HTTPException(status_code=500, detail=str(e))
